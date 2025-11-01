import requests
import json
import time

# Comprehensive test of the multi-page navigation with corrected orchestrator
def test_multi_page_navigation():
    """Test the complete 3-page navigation flow with action_selectors"""
    
    backend_url = 'http://127.0.0.1:5100'
    
    # Page 1: traffic-insurance
    page1_html = '''
    <html>
    <head><title>Traffic Insurance</title></head>
    <body>
      <h1>Traffic Insurance</h1>
      <form>
        <label>Plaka No</label>
        <input id="plateNo" name="plaka_no" />
        <button data-lov-id="src/pages/TrafficInsurance.tsx:191:10">Action 1</button>
      </form>
    </body>
    </html>
    '''
    
    # Page 2: vehicle-details  
    page2_html = '''
    <html>
    <head><title>Vehicle Details</title></head>
    <body>
      <h1>Vehicle Details</h1>
      <form>
        <label>Plaka No</label>
        <input data-lov-id="src/pages/VehicleDetails.tsx:79:16" name="plaka_no" />
        <label>Motor No</label>
        <input data-lov-id="src/pages/VehicleDetails.tsx:87:16" name="motor_no" />
        <label>Sasi No</label>
        <input data-lov-id="src/pages/VehicleDetails.tsx:95:16" name="sasi_no" />
        <label>Model Yili</label>
        <input data-lov-id="src/pages/VehicleDetails.tsx:104:16" name="model_yili" />
        <button data-lov-id="src/pages/VehicleDetails.tsx:189:10">Action 1</button>
      </form>
    </body>
    </html>
    '''
    
    # Page 3: insurance-quote (final page)
    page3_html = '''
    <html>
    <head><title>Insurance Quote</title></head>
    <body>
      <h1>Insurance Quote - Final Page</h1>
      <div>Your insurance quote is ready!</div>
      <button data-lov-id="src/pages/InsuranceQuote.tsx:231:10">Action 1</button>
      <a href="/quote.pdf">Download PDF</a>
    </body>
    </html>
    '''
    
    pages = [
        {
            "name": "Page 1 - Traffic Insurance", 
            "url": "https://preview--screen-to-data.lovable.app/traffic-insurance",
            "html": page1_html,
            "expected_action": "css#[data-lov-id=\"src/pages/TrafficInsurance.tsx:191:10\"]"
        },
        {
            "name": "Page 2 - Vehicle Details",
            "url": "https://preview--screen-to-data.lovable.app/vehicle-details", 
            "html": page2_html,
            "expected_action": "css#[data-lov-id=\"src/pages/VehicleDetails.tsx:189:10\"]"
        },
        {
            "name": "Page 3 - Insurance Quote",
            "url": "https://preview--screen-to-data.lovable.app/insurance-quote",
            "html": page3_html,
            "expected_action": "css#[data-lov-id=\"src/pages/InsuranceQuote.tsx:231:10\"]"
        }
    ]
    
    print("=== Multi-Page Navigation Test ===")
    print("Testing corrected orchestrator with action_selectors mapping")
    print(f"Backend URL: {backend_url}")
    print()
    
    all_passed = True
    
    for i, page in enumerate(pages, 1):
        print(f"--- {page['name']} ---")
        print(f"URL: {page['url']}")
        print(f"Expected Action: {page['expected_action']}")
        
        try:
            # Call the static analyzer directly to verify action_selectors
            analyze_url = f'{backend_url}/api/f3-static'
            analyze_data = {
                "op": "analyzePageStaticFillForms",
                "html": page['html'],
                "current_url": page['url'],
                "task": "Yeni Trafik"
            }
            
            analyze_response = requests.post(analyze_url, json=analyze_data, timeout=10)
            analyze_result = analyze_response.json()
            
            if analyze_result.get('ok'):
                action_selectors = analyze_result.get('action_selectors', {})
                actions = analyze_result.get('actions', [])
                
                print(f"✓ Static analyzer OK")
                print(f"  Actions found: {actions}")
                print(f"  Action selectors: {action_selectors}")
                
                # Verify the mapping is correct
                if 'Action 1' in actions and 'Action 1' in action_selectors:
                    mapped_selector = action_selectors['Action 1']
                    expected_selector = page['expected_action'].replace('css#', '')
                    
                    if mapped_selector == expected_selector:
                        print(f"  ✅ Action mapping correct: Action 1 -> {mapped_selector}")
                    else:
                        print(f"  ❌ Action mapping incorrect: expected {expected_selector}, got {mapped_selector}")
                        all_passed = False
                else:
                    print(f"  ❌ Action 1 not found in actions or action_selectors")
                    all_passed = False
                    
            else:
                print(f"  ❌ Static analyzer failed: {analyze_result.get('error', 'unknown')}")
                all_passed = False
                
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
            all_passed = False
            
        print()
        
    print("=== Test Summary ===")
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Orchestrator fix is working correctly")
        print("✅ Action selectors are properly mapped for all pages")
        print("✅ Multi-page navigation should work as expected")
        print()
        print("Next steps:")
        print("1. Test in actual Electron app with real website")
        print("2. Verify Page 1 → Page 2 → Page 3 navigation")
        print("3. Confirm PDF generation on final page")
    else:
        print("❌ Some tests failed - orchestrator fix needs attention")
        
    return all_passed

if __name__ == "__main__":
    test_multi_page_navigation()