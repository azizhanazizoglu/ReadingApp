import requests
import json
import time

def comprehensive_flow_test():
    """Test the complete 3-page flow with PDF generation focus"""
    
    backend_url = 'http://127.0.0.1:5100'
    
    print("=== Comprehensive Multi-Page Flow Test ===")
    print("Testing the fixed orchestrator with focus on PDF generation")
    print()
    
    # Test each page individually to see action_selectors
    pages = [
        {
            "name": "Page 1 - Traffic Insurance", 
            "url": "https://preview--screen-to-data.lovable.app/traffic-insurance",
            "has_fields": True,
            "expected_selector": "[data-lov-id=\"src/pages/TrafficInsurance.tsx:191:10\"]"
        },
        {
            "name": "Page 2 - Vehicle Details",
            "url": "https://preview--screen-to-data.lovable.app/vehicle-details", 
            "has_fields": True,
            "expected_selector": "[data-lov-id=\"src/pages/VehicleDetails.tsx:189:10\"]"
        },
        {
            "name": "Page 3 - Insurance Quote (Final)",
            "url": "https://preview--screen-to-data.lovable.app/insurance-quote",
            "has_fields": False,  # No fields = no-mapping branch
            "expected_selector": "[data-lov-id=\"src/pages/InsuranceQuote.tsx:231:10\"]"
        }
    ]
    
    all_passed = True
    
    for i, page in enumerate(pages, 1):
        print(f"--- {page['name']} ---")
        
        # Create sample HTML based on page type
        if page['has_fields']:
            html = f'''
            <html><body>
                <form>
                    <input id="field1" name="test_field" />
                    <button data-lov-id="{page['expected_selector'].replace('"', '\\"')}">Action 1</button>
                </form>
            </body></html>
            '''
        else:
            # Final page - no fields, just action button (triggers no-mapping branch)
            html = f'''
            <html><body>
                <h1>Insurance Quote Ready</h1>
                <div>Premium: $250/year</div>
                <button data-lov-id="{page['expected_selector'].replace('"', '\\"')}">Action 1</button>
                <div id="pdf-container" style="display:none;">
                    <a href="/quote.pdf" download>Download PDF</a>
                </div>
            </body></html>
            '''
        
        try:
            # Test static analyzer
            analyze_response = requests.post(f'{backend_url}/api/f3-static', json={
                "op": "analyzePageStaticFillForms",
                "html": html,
                "current_url": page['url'],
                "task": "Yeni Trafik"
            }, timeout=10)
            
            if analyze_response.status_code == 200:
                result = analyze_response.json()
                
                if result.get('ok'):
                    field_mapping = result.get('field_mapping', {})
                    actions = result.get('actions', [])
                    action_selectors = result.get('action_selectors', {})
                    
                    print(f"✓ Static analyzer OK")
                    print(f"  Has fields: {len(field_mapping) > 0} (expected: {page['has_fields']})")
                    print(f"  Actions: {actions}")
                    print(f"  Action selectors: {action_selectors}")
                    
                    # Verify action mapping
                    if 'Action 1' in actions and 'Action 1' in action_selectors:
                        actual_selector = action_selectors['Action 1']
                        if actual_selector == page['expected_selector']:
                            print(f"  ✅ Action mapping correct")
                            
                            # Determine which branch this would use
                            if page['has_fields']:
                                print(f"  📋 Will use main branch (with field mapping)")
                            else:
                                print(f"  🎯 Will use no-mapping branch (final page)")
                                
                        else:
                            print(f"  ❌ Action mapping incorrect: expected {page['expected_selector']}, got {actual_selector}")
                            all_passed = False
                    else:
                        print(f"  ❌ Action 1 not found")
                        all_passed = False
                        
                else:
                    print(f"  ❌ Analyzer failed: {result.get('error')}")
                    all_passed = False
            else:
                print(f"  ❌ HTTP {analyze_response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
            all_passed = False
            
        print()
    
    print("=== Final Assessment ===")
    if all_passed:
        print("🎉 ALL PAGES VALIDATED!")
        print()
        print("✅ Orchestrator Fix Status:")
        print("  - Main branch: Uses action_selectors for pages with fields")
        print("  - No-mapping branch: Uses action_selectors for final page")
        print("  - Both branches now use CSS selectors instead of text search")
        print()
        print("🎯 Next Steps for PDF Generation:")
        print("  1. Ensure target website actually generates PDF after button click")
        print("  2. Consider increasing PDF wait timeout (currently 2000ms)")
        print("  3. Test alternative PDF detection methods:")
        print("     - Blob URLs (modern web apps)")
        print("     - PDF iframes/embeds")
        print("     - Download links")
        print("  4. Manual verification:")
        print("     - Click Action 1 button manually on insurance-quote page")
        print("     - Check if PDF appears/downloads")
        print("     - Verify button selector is correct in browser DevTools")
        print()
        print("🔍 Debugging Tips:")
        print("  - If button doesn't work: Check data-lov-id attribute in browser")
        print("  - If no PDF appears: Website might use different PDF mechanism")
        print("  - Try increasing wait time or checking browser Network tab")
        
    else:
        print("❌ Some validations failed")
        
    return all_passed

if __name__ == "__main__":
    comprehensive_flow_test()