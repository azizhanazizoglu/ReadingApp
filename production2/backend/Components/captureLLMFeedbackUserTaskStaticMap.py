"""
Capture successful LLM field mappings and action selectors.
Transform LLM data into calibration-compatible format.

This component extracts working selectors from F3 LLM session results and
converts them to the exact calib.json format for seamless integration.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse
import uuid
import re


def capture_llm_session_data(
    llm_results: List[Dict[str, Any]],  
    task: str = "Yeni Trafik"
) -> Dict[str, Any]:
    """
    Extract successful LLM mappings from F3 session results.
    
    Args:
        llm_results: List of F3 LLM page analysis results from successful session
        task: Domain task name
        
    Returns:
        {
            "ok": True,
            "host": "preview--screen-to-data.lovable.app",
            "task": "Yeni Trafik", 
            "pages_captured": 3,
            "page_mappings": [...],
            "global_fields": ["plaka_no", "motor_no", ...],
            "global_actions": ["Devam", "Poliçeyi Aktifleştir", ...]
        }
    """
    if not llm_results or not isinstance(llm_results, list):
        return {"ok": False, "error": "No LLM results provided"}
    
    try:
        page_mappings = []
        all_fields = set()
        all_actions = set()
        host = None
        
        for result in llm_results:
            if not result.get("ok") or not result.get("url"):
                continue
                
            # Extract host from first valid URL
            if host is None:
                parsed_url = urlparse(result["url"])
                host = parsed_url.netloc
            
            # Extract page mapping data
            page_mapping = extract_page_mappings(result)
            if page_mapping["ok"]:
                page_mappings.append(page_mapping)
                all_fields.update(page_mapping.get("field_keys", []))
                all_actions.update([action["label"] for action in page_mapping.get("actions", [])])
        
        return {
            "ok": True,
            "host": host,
            "task": task,
            "pages_captured": len(page_mappings),
            "page_mappings": page_mappings,
            "global_fields": sorted(list(all_fields)),
            "global_actions": sorted(list(all_actions))
        }
        
    except Exception as e:
        return {"ok": False, "error": f"Failed to capture LLM session data: {str(e)}"}


def extract_page_mappings(llm_page_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract field_mapping, actions, and URL from single F3 LLM page result.
    
    Args:
        llm_page_result: Single F3 LLM analyzePage result
        
    Returns:
        {
            "ok": True,
            "url": "https://preview--screen-to-data.lovable.app/traffic-insurance",
            "field_mapping": {"plaka_no": "#plateNo", "motor_no": "[data-lov-id='...']"},
            "actions": [{"label": "Devam", "selector": "[data-lov-id='...']"}],
            "field_keys": ["plaka_no", "motor_no"],
            "critical_fields": ["plaka_no"]
        }
    """
    try:
        url = llm_page_result.get("url", "")
        field_mapping = llm_page_result.get("field_mapping", {})
        actions_raw = llm_page_result.get("actions", [])
        
        # Convert actions to detailed format
        actions_detailed = []
        action_selectors = llm_page_result.get("action_selectors", {})  # Direct action->selector mapping
        
        for i, action in enumerate(actions_raw):
            if isinstance(action, str):
                # Handle different action formats from LLM
                if action.startswith("css#"):
                    # CSS selector action: "css#[data-lov-id='...']"
                    selector = action[4:]  # Remove "css#" prefix
                    # Find label from action_selectors mapping
                    label = None
                    for action_label, action_selector in action_selectors.items():
                        if action_selector == selector:
                            label = action_label
                            break
                    if not label:
                        label = f"Action {i+1}"  # Fallback
                elif action.startswith("click#"):
                    # Click action: "click#Devam"
                    label = action[6:]  # Remove "click#" prefix
                    selector = action_selectors.get(label, "")  # Look up selector from mapping
                else:
                    # Plain text action: "Devam"
                    label = action
                    selector = action_selectors.get(label, "")  # Look up selector from mapping
                
                actions_detailed.append({
                    "label": label,
                    "selector": selector
                })
        
        # Extract field keys and critical fields
        field_keys = list(field_mapping.keys())
        critical_fields = llm_page_result.get("validation", {}).get("critical_fields", field_keys)
        
        return {
            "ok": True,
            "url": url,
            "field_mapping": field_mapping,
            "actions": actions_detailed,
            "field_keys": field_keys,
            "critical_fields": critical_fields if critical_fields else field_keys
        }
        
    except Exception as e:
        return {"ok": False, "error": f"Failed to extract page mappings: {str(e)}"}


def convert_to_calib_format(
    captured_data: Dict[str, Any],
    host: str,
    task: str,
    preserve_created_at: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert LLM capture data to exact calib.json format with pages structure.
    
    Args:
        captured_data: Output from capture_llm_session_data
        host: "preview--screen-to-data.lovable.app"
        task: "Yeni Trafik"
        preserve_created_at: Existing createdAt timestamp to preserve
        
    Returns:
        Complete calibration structure matching calib.json format exactly
    """
    try:
        if not captured_data.get("ok"):
            return {"ok": False, "error": "Invalid captured data"}
        
        page_mappings = captured_data.get("page_mappings", [])
        global_fields = captured_data.get("global_fields", [])
        global_actions = captured_data.get("global_actions", [])
        
        # Build global field selectors from all pages
        global_field_selectors = {}
        for page in page_mappings:
            for field, selector in page.get("field_mapping", {}).items():
                if field not in global_field_selectors and selector:
                    global_field_selectors[field] = selector
        
        # Build global actions detail
        actions_detail = []
        actions_execution_order = []
        action_id_counter = 1
        
        for action_label in global_actions:
            # Find selector for this action from any page
            action_selector = ""
            for page in page_mappings:
                for action in page.get("actions", []):
                    if action["label"] == action_label and action.get("selector"):
                        action_selector = action["selector"]
                        break
                if action_selector:
                    break
            
            actions_detail.append({
                "id": f"a{action_id_counter}",
                "label": action_label,
                "selector": action_selector
            })
            actions_execution_order.append(action_label)
            action_id_counter += 1
        
        # Build pages structure
        pages = []
        for i, page_mapping in enumerate(page_mappings):
            page_id = f"p_{_generate_page_id()}"
            page_name = f"Page {i+1}"
            
            # Convert actions to page-specific format
            page_actions_detail = []
            for action in page_mapping.get("actions", []):
                page_actions_detail.append({
                    "id": f"a{i+1}",
                    "label": action["label"],
                    "selector": action.get("selector", "")
                })
            
            page_data = {
                "id": page_id,
                "name": page_name,
                "urlPattern": "",
                "urlSample": page_mapping["url"],
                "fieldSelectors": page_mapping.get("field_mapping", {}),
                "fieldKeys": page_mapping.get("field_keys", []),
                "executionOrder": [],
                "actionsDetail": page_actions_detail,
                "criticalFields": page_mapping.get("critical_fields", [])
            }
            
            # Mark last page if it's the final one
            if i == len(page_mappings) - 1:
                page_data["isLast"] = False  # Will be determined by context
            
            pages.append(page_data)
        
        # Build complete calibration structure
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        created_at = preserve_created_at or now
        
        calib_structure = {
            "fieldSelectors": global_field_selectors,
            "fieldKeys": global_fields,
            "actions": global_actions,
            "actionsDetail": actions_detail,
            "actionsExecutionOrder": actions_execution_order,
            "executionOrder": [],
            "criticalFields": _extract_global_critical_fields(page_mappings),
            "pages": pages,
            "currentPageId": pages[0]["id"] if pages else "",
            "host": host,
            "task": task,
            "updatedAt": now,
            "createdAt": created_at
        }
        
        return {
            "ok": True,
            "calib_structure": calib_structure,
            "pages_processed": len(pages),
            "fields_captured": len(global_fields),
            "actions_captured": len(global_actions)
        }
        
    except Exception as e:
        return {"ok": False, "error": f"Failed to convert to calib format: {str(e)}"}


def _generate_page_id() -> str:
    """Generate random page ID similar to existing format."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "mfr" + "".join([chars[ord(c) % len(chars)] for c in str(uuid.uuid4())[:6]])


def _extract_global_critical_fields(page_mappings: List[Dict[str, Any]]) -> List[str]:
    """Extract critical fields that appear across multiple pages."""
    field_counts = {}
    
    for page in page_mappings:
        critical_fields = page.get("critical_fields", [])
        for field in critical_fields:
            field_counts[field] = field_counts.get(field, 0) + 1
    
    # Return fields that appear in multiple pages or are consistently critical
    total_pages = len(page_mappings)
    return [field for field, count in field_counts.items() if count >= max(1, total_pages // 2)]


def validate_llm_capture_data(llm_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate LLM session results before processing.
    
    Returns:
        {"ok": True, "valid_pages": 3, "total_pages": 3, "warnings": [...]}
    """
    try:
        if not llm_results or not isinstance(llm_results, list):
            return {"ok": False, "error": "Invalid LLM results format"}
        
        valid_pages = 0
        warnings = []
        
        for i, result in enumerate(llm_results):
            page_num = i + 1
            
            if not result.get("ok"):
                warnings.append(f"Page {page_num}: LLM analysis failed")
                continue
                
            if not result.get("url"):
                warnings.append(f"Page {page_num}: Missing URL")
                continue
                
            field_mapping = result.get("field_mapping", {})
            if not field_mapping:
                warnings.append(f"Page {page_num}: No field mappings found")
                
            actions = result.get("actions", [])
            if not actions:
                warnings.append(f"Page {page_num}: No actions found")
                
            valid_pages += 1
        
        return {
            "ok": valid_pages > 0,
            "valid_pages": valid_pages,
            "total_pages": len(llm_results),
            "warnings": warnings,
            "validation_passed": valid_pages == len(llm_results) and len(warnings) == 0
        }
        
    except Exception as e:
        return {"ok": False, "error": f"Validation failed: {str(e)}"}