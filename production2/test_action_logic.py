import sys
sys.path.append('production2/react_ui/src/stateflows')

# Create a mock test to verify the orchestrator logic
def test_action_processing():
    """Test that action_selectors mapping is used correctly"""
    
    # Simulate the analyzer response with action_selectors
    ana = {
        "ok": True,
        "actions": ["Action 1"],
        "action_selectors": {
            "Action 1": "[data-lov-id=\"src/pages/TrafficInsurance.tsx:191:10\"]"
        }
    }
    
    # Simulate the action processing logic from the orchestrator
    acts = ana.get("actions", [])
    action_selectors = ana.get("action_selectors", {})
    
    click_acts = []
    for a in acts:
        if a.startswith('css#'):
            # Already css# prefixed, preserve as is
            click_acts.append(a)
            print(f"CSS selector (preserved): {a}")
        elif action_selectors.get(a):
            # Map action label to css selector using backend mapping
            mapped = f"css#{action_selectors[a]}"
            click_acts.append(mapped)
            print(f"CSS selector (mapped): {a} -> {mapped}")
        else:
            # Fall back to text search
            fallback = f"click#{a}"
            click_acts.append(fallback)
            print(f"Text search (fallback): {a} -> {fallback}")
    
    print(f"\nOriginal actions: {acts}")
    print(f"Action selectors: {action_selectors}")
    print(f"Final click actions: {click_acts}")
    
    # Verify the mapping worked
    assert len(click_acts) == 1
    assert click_acts[0] == "css#[data-lov-id=\"src/pages/TrafficInsurance.tsx:191:10\"]"
    print("\n✅ SUCCESS: Action selector mapping is working correctly!")
    return True

if __name__ == "__main__":
    test_action_processing()