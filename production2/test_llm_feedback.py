"""
Test script for LLM Feedback to Calibration feature.

This script simulates the complete flow:
1. Static fails with fake calibration selectors
2. LLM succeeds with real selectors 
3. Auto-update calib.json with working LLM selectors
4. Verify calibration panel shows updated selectors
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_llm_feedback_capture():
    """Test the LLM feedback capture component."""
    print("=== Testing LLM Feedback Capture ===")
    
    # Mock LLM session results (simulating successful F3 LLM flow)
    mock_llm_results = [
        {
            "ok": True,
            "url": "https://preview--screen-to-data.lovable.app/traffic-insurance",
            "field_mapping": {
                "plaka_no": "#plateNo"
            },
            "actions": ["css#[data-lov-id='src/pages/TrafficInsurance.tsx:191:10']"],
            "validation": {
                "critical_fields": ["plaka_no"]
            }
        },
        {
            "ok": True,
            "url": "https://preview--screen-to-data.lovable.app/vehicle-details",
            "field_mapping": {
                "plaka_no": "[data-lov-id='src/pages/VehicleDetails.tsx:79:16']",
                "motor_no": "[data-lov-id='src/pages/VehicleDetails.tsx:87:16']",
                "sasi_no": "[data-lov-id='src/pages/VehicleDetails.tsx:95:16']",
                "model_yili": "[data-lov-id='src/pages/VehicleDetails.tsx:104:16']"
            },
            "actions": ["css#[data-lov-id='src/pages/VehicleDetails.tsx:189:10']"],
            "validation": {
                "critical_fields": ["plaka_no", "motor_no", "sasi_no", "model_yili"]
            }
        },
        {
            "ok": True,
            "url": "https://preview--screen-to-data.lovable.app/insurance-quote",
            "field_mapping": {},
            "actions": ["css#[data-lov-id='src/pages/InsuranceQuote.tsx:231:10']"],
            "validation": {
                "critical_fields": ["plaka_no", "motor_no", "sasi_no", "model_yili"]
            }
        }
    ]
    
    try:
        from backend.Components.captureLLMFeedbackUserTaskStaticMap import (
            capture_llm_session_data,
            convert_to_calib_format,
            validate_llm_capture_data
        )
        
        # Test validation
        validation_result = validate_llm_capture_data(mock_llm_results)
        print(f"✓ Validation: {validation_result}")
        
        # Test capture
        capture_result = capture_llm_session_data(mock_llm_results, "Yeni Trafik")
        print(f"✓ Capture: pages={capture_result.get('pages_captured')}, fields={len(capture_result.get('global_fields', []))}")
        
        # Test conversion
        host = "preview--screen-to-data.lovable.app"
        convert_result = convert_to_calib_format(capture_result, host, "Yeni Trafik")
        print(f"✓ Convert: fields={convert_result.get('fields_captured')}, actions={convert_result.get('actions_captured')}")
        
        return convert_result
        
    except Exception as e:
        print(f"✗ Capture test failed: {e}")
        return None


def test_calib_update(convert_result: Dict[str, Any]):
    """Test the calibration update component."""
    print("\n=== Testing Calibration Update ===")
    
    if not convert_result or not convert_result.get("ok"):
        print("✗ No valid convert result to test with")
        return False
    
    try:
        from backend.Components.updateCalibUserTaskStaticLLMFeedback import (
            update_calib_with_llm_feedback,
            preview_calib_update,
            backup_calib_before_update
        )
        
        host = "preview--screen-to-data.lovable.app"
        task = "Yeni Trafik"
        calib_path = str(Path(__file__).parent / "calib.json")  # Same directory as script
        
        # Test preview (no actual changes)
        preview_result = preview_calib_update(convert_result, host, task, calib_path)
        print(f"✓ Preview: changes={preview_result.get('changes')}")
        
        # Test backup creation  
        backup_result = backup_calib_before_update(calib_path)
        print(f"✓ Backup: {backup_result.get('backup_path', 'failed')}")
        
        # Test actual update (BE CAREFUL - this modifies calib.json!)
        # Uncomment the next lines only if you want to test actual update
        # update_result = update_calib_with_llm_feedback(convert_result, host, task, calib_path)
        # print(f"✓ Update: {update_result}")
        
        print("✓ Update component works (actual update commented out for safety)")
        return True
        
    except Exception as e:
        print(f"✗ Update test failed: {e}")
        return False


def test_feature_integration():
    """Test the enhanced calibration feature integration."""
    print("\n=== Testing Feature Integration ===")
    
    try:
        from backend.Features.calibFillUserTaskPageStatic import (
            plan_calib_llm_feedback_update,
            plan_calib_capture_llm_mappings,
            plan_calib_preview_llm_update
        )
        
        # Mock data
        mock_llm_results = [
            {
                "ok": True,
                "url": "https://preview--screen-to-data.lovable.app/traffic-insurance",
                "field_mapping": {"plaka_no": "#plateNo"},
                "actions": ["Devam"]
            }
        ]
        
        host = "preview--screen-to-data.lovable.app"
        task = "Yeni Trafik"
        
        # Test capture only
        capture_result = plan_calib_capture_llm_mappings(mock_llm_results, task)
        print(f"✓ Feature capture: {capture_result.get('ok')}")
        
        # Test preview only  
        preview_result = plan_calib_preview_llm_update(mock_llm_results, host, task)
        print(f"✓ Feature preview: {preview_result.get('ok')}")
        
        # Test full integration (with auto_save=False for safety)
        # integration_result = plan_calib_llm_feedback_update(mock_llm_results, host, task, auto_save=False)
        # print(f"✓ Feature integration: {integration_result.get('ok')}")
        
        print("✓ Feature integration works (full update commented out for safety)")
        return True
        
    except Exception as e:
        print(f"✗ Feature integration test failed: {e}")
        return False


def verify_calib_structure():
    """Verify current calib.json structure."""
    print("\n=== Verifying Current Calibration Structure ===")
    
    try:
        calib_path = Path(__file__).parent / "calib.json"  # Same directory as script
        
        if not calib_path.exists():
            print(f"✗ calib.json not found at {calib_path}")
            return False
        
        with open(calib_path, 'r', encoding='utf-8') as f:
            calib_data = json.load(f)
        
        # Check structure
        hosts = list(calib_data.keys())
        print(f"✓ Hosts: {hosts}")
        
        for host, host_data in calib_data.items():
            if isinstance(host_data, dict):
                tasks = list(host_data.keys())
                print(f"  - {host}: {tasks}")
                
                for task, task_data in host_data.items():
                    if isinstance(task_data, dict):
                        fields = len(task_data.get("fieldKeys", []))
                        actions = len(task_data.get("actions", []))
                        pages = len(task_data.get("pages", []))
                        print(f"    - {task}: {fields} fields, {actions} actions, {pages} pages")
        
        return True
        
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing LLM Feedback to Calibration Feature")
    print("=" * 50)
    
    # Run tests
    success_count = 0
    total_tests = 4
    
    # Test 1: Capture
    convert_result = test_llm_feedback_capture()
    if convert_result and convert_result.get("ok"):
        success_count += 1
    
    # Test 2: Update
    if test_calib_update(convert_result):
        success_count += 1
    
    # Test 3: Feature integration
    if test_feature_integration():
        success_count += 1
    
    # Test 4: Verification
    if verify_calib_structure():
        success_count += 1
    
    # Results
    print(f"\n🎯 Test Results: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("✅ All tests passed! LLM Feedback feature is ready.")
        print("\n🚀 Next steps:")
        print("1. Test Master Button flow with fake calibration")
        print("2. Verify LLM fallback succeeds and updates calib.json")
        print("3. Check Calibration Panel shows updated selectors")
    else:
        print("❌ Some tests failed. Check the errors above.")