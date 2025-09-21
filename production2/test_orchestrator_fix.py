import requests
import json

# Test the TsX endpoint with sample HTML containing the action selector
test_html = '''
<html>
<body>
  <form>
    <label>Plaka No</label>
    <input id="plateNo" name="plaka_no" />
    <button data-lov-id="src/pages/TrafficInsurance.tsx:191:10">Action 1</button>
  </form>
</body>
</html>
'''

url = 'http://127.0.0.1:5100/api/tsx/dev-run'
data = {
    "html": test_html,
    "current_url": "https://preview--screen-to-data.lovable.app/traffic-insurance"
}

print("Testing TsX endpoint with corrected orchestrator...")
print(f"URL: {url}")
print(f"HTML length: {len(test_html)} chars")
print(f"Current URL: {data['current_url']}")
print()

try:
    response = requests.post(url, json=data, timeout=30)
    result = response.json()
    
    print("=== Response ===")
    print(f"Status Code: {response.status_code}")
    print(f"OK: {result.get('ok', False)}")
    
    if result.get('ok'):
        print(f"Step: {result.get('step', 'unknown')}")
        print(f"PDF Generated: {result.get('pdf_found', False)}")
        
        # Print full result for debugging
        print("\n=== Full Response ===")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
        
        # Look for action-related logs
        logs = result.get('logs', [])
        print(f"\nTotal logs: {len(logs)}")
        
        action_logs = [log for log in logs if 'action' in log.lower()]
        
        print("\n=== Action-related logs ===")
        for log in action_logs[-10:]:  # Last 10 action logs
            print(f"  {log}")
            
        # Check if action_selectors were used
        selector_logs = [log for log in logs if 'CSS selector (mapped)' in log]
        if selector_logs:
            print("\n=== SUCCESS: CSS selectors were mapped! ===")
            for log in selector_logs:
                print(f"  ✓ {log}")
        else:
            print("\n=== WARNING: No CSS selector mapping detected ===")
            fallback_logs = [log for log in logs if 'Text search (fallback)' in log]
            for log in fallback_logs:
                print(f"  ⚠ {log}")
    else:
        print(f"Error: {result.get('error', 'unknown')}")
        print(f"Error Code: {result.get('error_code', 'none')}")
        
except Exception as e:
    print(f"Request failed: {e}")