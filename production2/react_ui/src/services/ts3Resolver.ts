type DevLog = (c: string, m: string) => void;

const normalize = (s: string) => {
  const t = String(s || '').toLowerCase()
    .replace(/ç/g, 'c').replace(/ğ/g, 'g').replace(/ı/g, 'i').replace(/ö/g, 'o').replace(/ş/g, 's').replace(/ü/g, 'u')
    .replace(/Ç/g, 'c').replace(/Ğ/g, 'g').replace(/İ/g, 'i').replace(/Ö/g, 'o').replace(/Ş/g, 's').replace(/Ü/g, 'u')
    .replace(/[^\p{L}\p{N}]+/gu, '');
  try { return t.normalize('NFD').replace(/[\u0300-\u036f]/g, ''); } catch { return t; }
};

const flatten = (obj: any): Record<string, { value: any; path: string }> => {
  const out: Record<string, { value: any; path: string }> = {};
  const walk = (o: any, path: string[] = []) => {
    if (!o || typeof o !== 'object') return;
    for (const [k, v] of Object.entries(o)) {
      const p = [...path, k];
      if (v && typeof v === 'object' && !Array.isArray(v)) {
        walk(v, p);
      } else {
        out[normalize(k)] = { value: v, path: p.join('.') };
      }
    }
  };
  try { walk(obj || {}); } catch {}
  return out;
};

const unwrapCodeFence = (txt: string) => {
  const m = typeof txt === 'string' ? txt.match(/```(?:json)?\s*([\s\S]*?)\s*```/i) : null;
  return m ? m[1].trim() : (txt || '');
};

const parseRawResponseJson = (ruhsat_json: any, devLog?: DevLog): Record<string, any> => {
  const out: Record<string, any> = {};
  try {
    if (ruhsat_json && typeof ruhsat_json.raw_response === 'string') {
      const inner = unwrapCodeFence(ruhsat_json.raw_response);
      const j = JSON.parse(inner);
      ['tckimlik','dogum_tarihi','ad_soyad','plaka_no'].forEach(k => {
        if (j && j[k] != null && String(j[k]).trim() !== '') {
          out[k] = j[k];
          devLog?.('IDX-TS3-RAWJSON', `${k} <- from raw_response JSON`);
        }
      });
    }
  } catch {}
  return out;
};

const extractFromRaw = (text: string, devLog?: DevLog) => {
  const out: Record<string, string> = {};
  if (!text || typeof text !== 'string') return out;
  const s = text.replace(/\r/g, '');
  // plate ex: 34 ABC 123
  const plateRe = /\b([0-8][0-9])\s*[- ]?\s*([A-ZÇĞİÖŞÜ]{1,3})\s*[- ]?\s*([0-9]{2,4})\b/iu;
  const pm = s.match(plateRe);
  if (pm) out['plaka_no'] = `${pm[1]} ${pm[2].toUpperCase()} ${pm[3]}`;
  // TCKN
  const tcRe = /\b\d{11}\b/g;
  const tcm = s.match(tcRe);
  if (tcm && tcm.length > 0) out['tckimlik'] = tcm[0];
  // date dd.mm.yyyy
  const dRe = /\b([0-3]?\d)[./-]([0-1]?\d)[./-](\d{4})\b/;
  const dm = s.match(dRe);
  if (dm) out['dogum_tarihi'] = `${dm[3]}-${dm[2].padStart(2,'0')}-${dm[1].padStart(2,'0')}`;
  // name heuristic
  const nameLabelRe = /(ad\s*soyad[ıi]?|ad[ıi]?:\s*[^\n]+\n\s*soyad[ıi]?:\s*[^\n]+)/i;
  const nl = s.match(nameLabelRe);
  if (nl) {
    const block = nl[0];
    const both = block.match(/ad\s*soyad[ıi]?\s*[:：]?\s*([^\n]+)/i);
    if (both && both[1]) out['ad_soyad'] = both[1].trim();
    else {
      const ad = (block.match(/ad[ıi]?\s*[:：]\s*([^\n]+)/i) || [,''])[1].trim();
      const soyad = (block.match(/soyad[ıi]?\s*[:：]\s*([^\n]+)/i) || [,''])[1].trim();
      const full = (ad + ' ' + soyad).trim();
      if (full) out['ad_soyad'] = full;
    }
  }
  if (Object.keys(out).length > 0) devLog?.('IDX-TS3-EXTRACT', JSON.stringify(out));
  return out;
};

export function resolveValues(mapping: any, ruhsat_json: any, raw: string, devLog?: DevLog): Record<string, any> {
  const fieldMapping = mapping?.field_mapping || {};
  const synonyms: Record<string, string[]> = {
    'plaka_no': ['plaka', 'plakano', 'plate', 'plateno', 'aracplaka', 'vehicleplate', 'plaka_no'],
    'ad_soyad': ['adsoyad', 'isim', 'ad', 'soyad', 'name', 'fullname', 'full_name'],
    'tckimlik': ['tc', 'tckimlik', 'kimlik', 'kimlikno', 'tcno', 'identity', 'nationalid'],
    'dogum_tarihi': ['dogumtarihi', 'd_tarihi', 'dtarihi', 'birthdate', 'birth_date', 'dob']
  };
  const flat = flatten(ruhsat_json);
  const rawJson = parseRawResponseJson(ruhsat_json, devLog);
  const rawExtract = extractFromRaw(raw, devLog);
  const dataResolved: Record<string, any> = {};

  for (const key of Object.keys(fieldMapping)) {
    const nKey = normalize(key);
    const cands = new Set<string>([nKey, ...(synonyms[key] || []).map(normalize)]);
    let foundVal: any = undefined;
    let foundFrom = '';
    // 1) explicit from raw_response JSON
    if (rawJson[key] != null && String(rawJson[key]).trim() !== '') {
      foundVal = rawJson[key];
      foundFrom = 'raw_response_json';
    }
    // 2) exact key match
    if (foundVal == null) {
      for (const cand of cands) {
        if (flat[cand] && flat[cand].value != null && String(flat[cand].value).trim() !== '') {
          foundVal = flat[cand].value; foundFrom = flat[cand].path; break;
        }
      }
    }
    // 3) substring fallback
    if (foundVal == null) {
      for (const [fk, info] of Object.entries(flat)) {
        if ([...cands].some(c => fk.includes(c))) {
          if (info.value != null && String(info.value).trim() !== '') { foundVal = info.value; foundFrom = info.path; break; }
        }
      }
    }
    // 4) raw text extraction
    if (foundVal == null && rawExtract[key] != null) { foundVal = rawExtract[key]; foundFrom = 'rawresponse'; }

    dataResolved[key] = foundVal ?? '';
    const vStr = foundVal == null ? '' : String(foundVal);
    devLog?.('IDX-TS3-RESOLVE', `${key} <- ${foundFrom || 'N/A'} = ${vStr.length > 60 ? vStr.slice(0,60)+'…' : vStr}`);
  }

  // normalize some common fields
  if (typeof dataResolved['plaka_no'] === 'string') {
    dataResolved['plaka_no'] = String(dataResolved['plaka_no']).replace(/\s+/g, ' ').trim().toUpperCase();
  }
  if (typeof dataResolved['tckimlik'] === 'string') {
    dataResolved['tckimlik'] = String(dataResolved['tckimlik']).replace(/\D+/g, '');
  }

  return dataResolved;
}
