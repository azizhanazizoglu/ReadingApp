import json
from webbot.webbot_filler import (
    flatten_data,
    extract_from_raw,
    resolve_values,
    build_fill_plan,
    analyze_selectors,
    generate_injection_script,
)


def test_flatten_and_extract():
    data = {
        "Ad": {"Soyad": "VELI"},
        "Plaka No": "34 abc 123",
        "rawresponse": "Plaka: 34 ABC 123\nTC: 10000000000\nDogum Tarihi: 01.02.1990\nAd Soyad: Ali Veli",
    }
    flat = flatten_data(data)
    assert "ad" in flat and flat["ad"]["path"] == "Ad"
    assert "plakano" in flat

    raw_ex = extract_from_raw(data["rawresponse"])
    assert raw_ex["plaka_no"].upper() == "34 ABC 123"
    assert raw_ex["tckimlik"] == "10000000000"
    assert raw_ex["dogum_tarihi"] == "1990-02-01"
    assert raw_ex["ad_soyad"].lower() == "ali veli"


def test_resolve_values_pipeline():
    mapping_keys = ["plaka_no", "tckimlik", "dogum_tarihi", "ad_soyad"]
    ruhsat_json = {"Some": {"Nested": {"irrelevant": 1}}}
    raw = "PLAKA 06 bcd 789, TC 12345678901, Doğum 5/6/1985, Ad Soyad: Ayşe Yılmaz"
    samples = {"ad_soyad": "Sample Name"}
    resolved, logs = resolve_values(mapping_keys, ruhsat_json, raw, sample_values=samples, use_dummy_when_empty=True)
    assert resolved["plaka_no"].upper() == "06 BCD 789"
    assert resolved["tckimlik"] == "12345678901"
    assert resolved["dogum_tarihi"] == "1985-06-05"
    # ad_soyad comes from raw; if not, sample would apply
    assert resolved["ad_soyad"].lower() == "ayşe yılmaz" or resolved["ad_soyad"].lower() == "ayse yilmaz"
    assert any("raw-extract" in l for l in logs)


def test_build_plan_and_analyze_selectors():
    html = """
    <form>
      <label for="plk">Plaka</label>
      <input id="plk" />
      <label for="tc">TC Kimlik</label>
      <input id="tc" />
      <label for="dt">Doğum Tarihi</label>
      <input id="dt" type="date" />
      <label for="ad">Ad Soyad</label>
      <input id="ad" />
    </form>
    """
    mapping = {
        "field_mapping": {
            "plaka_no": "#plk",
            "tckimlik": "#tc",
            "dogum_tarihi": "#dt",
            "ad_soyad": "#ad",
        },
        "sample_values": {
            "plaka_no": "34 ABC 123",
            "tckimlik": "10000000000",
            "dogum_tarihi": "1990-01-01",
            "ad_soyad": "Ali Veli",
        },
    }
    plan, resolved, logs = build_fill_plan(mapping, ruhsat_json={}, raw_text=None, options={"use_dummy_when_empty": True})
    assert len(plan) == 4
    assert resolved["plaka_no"]
    analysis = analyze_selectors(html, mapping)
    assert all(analysis[k]["count"] == 1 for k in mapping["field_mapping"])  # every selector matches once


def test_generate_injection_script_smoke():
    plan = [
        type("FillItem", (), {"field": "plaka_no", "selector": "#plk", "value": "34 ABC 123"})(),
        type("FillItem", (), {"field": "tckimlik", "selector": "#tc", "value": "10000000000"})(),
    ]
    script = generate_injection_script(plan, highlight=True, simulate_typing=True, step_delay_ms=10)
    assert "selector-check plaka_no" in script or "selector-check" in script
    assert "document.querySelectorAll" in script
