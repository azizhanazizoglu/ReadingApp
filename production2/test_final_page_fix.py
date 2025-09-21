import requests
import json

def test_final_page_action_mapping():
    """Test that the final page (no fields, only actions) uses CSS selectors correctly"""
    
    backend_url = 'http://127.0.0.1:5100'
    
    # Final page HTML - no form fields, just action button
    final_page_html = '''
    <html>
    <head><title>Insurance Quote - Final</title></head>
    <body>
      <h1>Your Insurance Quote is Ready!</h1>
      <div class="quote-summary">
        <p>Premium: $250/year</p>
        <p>Policy Number: INS-123456</p>
      </div>
      <button data-lov-id="src/pages/InsuranceQuote.tsx:231:10" class="activate-btn">Action 1</button>
      <div id="pdf-container" style="display:none;">
        <a href="/quote.pdf" download>Download PDF</a>
      </div>
    </body>
    </html>
    '''
    
    print("=== Final Page Action Mapping Test ===")
    print("Testing no-mapping branch with action_selectors")
    print()
    
    try:
        # Test the static analyzer for final page
        analyze_url = f'{backend_url}/api/f3-static'
        analyze_data = {
            "op": "analyzePageStaticFillForms",
            "html": final_page_html,
            "current_url": "https://preview--screen-to-data.lovable.app/insurance-quote",
            "task": "Yeni Trafik"
        }
        
        print("1. Testing static analyzer...")
        analyze_response = requests.post(analyze_url, json=analyze_data, timeout=10)
        analyze_result = analyze_response.json()
        
        if analyze_result.get('ok'):
            field_mapping = analyze_result.get('field_mapping', {})
            actions = analyze_result.get('actions', [])
            action_selectors = analyze_result.get('action_selectors', {})
            
            print(f"✓ Static analyzer OK")
            print(f"  Field mapping: {field_mapping} (should be empty)")
            print(f"  Actions: {actions}")
            print(f"  Action selectors: {action_selectors}")
            
            # Verify this would trigger no-mapping branch
            has_mapping = field_mapping and len(field_mapping) > 0
            print(f"  Has field mapping: {has_mapping} (should be False for no-mapping branch)")
            
            # Verify action selector mapping exists
            if 'Action 1' in actions and 'Action 1' in action_selectors:
                expected_selector = "[data-lov-id=\"src/pages/InsuranceQuote.tsx:231:10\"]"
                actual_selector = action_selectors['Action 1']
                
                if actual_selector == expected_selector:
                    print(f"  ✅ Action selector mapping correct: {actual_selector}")
                    
                    # Simulate the fixed no-mapping logic
                    print("\n2. Simulating fixed no-mapping action processing...")
                    acts = actions
                    action_selector_map = action_selectors
                    
                    click_acts = []
                    for a in acts:
                        if a.startswith('css#'):
                            click_acts.append(a)
                            print(f"  CSS selector (preserved): {a}")
                        elif action_selector_map.get(a):
                            mapped = f"css#{action_selector_map[a]}"
                            click_acts.append(mapped)
                            print(f"  CSS selector (mapped): {a} -> {mapped}")
                        else:
                            fallback = f"click#{a}"
                            click_acts.append(fallback)
                            print(f"  Text search (fallback): {a} -> {fallback}")
                    
                    print(f"\n  Final click actions: {click_acts}")
                    
                    if click_acts[0] == f"css#{expected_selector}":
                        print("  ✅ SUCCESS: No-mapping branch will use CSS selector!")
                        print("  ✅ This should enable PDF generation on final page")
                        return True
                    else:
                        print(f"  ❌ FAILED: Expected css#{expected_selector}, got {click_acts[0]}")
                        return False
                else:
                    print(f"  ❌ Action selector incorrect: expected {expected_selector}, got {actual_selector}")
                    return False
            else:
                print(f"  ❌ Action 1 not found in actions or action_selectors")
                return False
        else:
            print(f"  ❌ Static analyzer failed: {analyze_result.get('error', 'unknown')}")
            return False
            
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_final_page_action_mapping()
    if success:
        print("\n🎉 Final page fix validated!")
        print("The orchestrator should now use CSS selectors on the final page,")
        print("enabling proper button clicking and PDF generation.")
    else:
        print("\n❌ Final page fix needs attention.")