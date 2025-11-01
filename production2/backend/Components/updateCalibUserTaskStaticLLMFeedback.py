"""
Update calib.json with LLM feedback while preserving other domains.

This component safely updates the calibration file with successful LLM mappings,
ensuring exact format preservation and domain isolation.
"""

from typing import Any, Dict, Optional
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse


def update_calib_with_llm_feedback(
    llm_calib_data: Dict[str, Any],
    host: str,
    task: str,
    calib_path: str = "calib.json"
) -> Dict[str, Any]:
    """
    Update calib.json with LLM feedback for specific host+task.
    Preserve all other domains and tasks.
    
    Args:
        llm_calib_data: Calibration format data from LLM capture (calib_structure key)
        host: "preview--screen-to-data.lovable.app"
        task: "Yeni Trafik"
        calib_path: Path to calib.json file
        
    Returns:
        {
            "ok": True, 
            "updated": True, 
            "backup_created": True,
            "backup_path": "calib_backup_20250921_153045.json",
            "fields_updated": ["plaka_no", "motor_no", ...],
            "actions_updated": ["Devam", "Poliçeyi Aktifleştir"],
            "pages_updated": 3
        }
    """
    try:
        # Validate input data
        if not llm_calib_data.get("ok") or not llm_calib_data.get("calib_structure"):
            return {"ok": False, "error": "Invalid LLM calibration data"}
        
        calib_structure = llm_calib_data["calib_structure"]
        
        # Create backup before updating
        backup_result = backup_calib_before_update(calib_path)
        if not backup_result["ok"]:
            return backup_result
        
        # Load existing calibration
        existing_calib = load_existing_calibration(calib_path)
        if not existing_calib["ok"]:
            return existing_calib
        
        # Merge LLM data with existing calibration
        merge_result = merge_llm_with_existing_calib(
            existing_calib["data"],
            calib_structure,
            host,
            task
        )
        
        if not merge_result["ok"]:
            return merge_result
        
        # Validate merged structure
        validation_result = validate_calib_structure(merge_result["merged_calib"])
        if not validation_result["ok"]:
            return validation_result
        
        # Save updated calibration
        save_result = save_calibration_file(merge_result["merged_calib"], calib_path)
        if not save_result["ok"]:
            return save_result
        
        return {
            "ok": True,
            "updated": True,
            "backup_created": True,
            "backup_path": backup_result["backup_path"],
            "fields_updated": calib_structure.get("fieldKeys", []),
            "actions_updated": calib_structure.get("actions", []),
            "pages_updated": len(calib_structure.get("pages", [])),
            "host": host,
            "task": task,
            "updated_at": calib_structure.get("updatedAt")
        }
        
    except Exception as e:
        return {"ok": False, "error": f"Failed to update calibration: {str(e)}"}


def backup_calib_before_update(calib_path: str) -> Dict[str, Any]:
    """
    Create timestamped backup of calib.json before updating.
    
    Returns:
        {"ok": True, "backup_path": "calib_backup_20250921_153045.json"}
    """
    try:
        calib_file = Path(calib_path)
        if not calib_file.exists():
            return {"ok": False, "error": f"Calibration file not found: {calib_path}"}
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"calib_backup_{timestamp}.json"
        backup_path = calib_file.parent / backup_name
        
        # Create backup
        shutil.copy2(calib_file, backup_path)
        
        return {
            "ok": True,
            "backup_path": str(backup_path),
            "original_size": calib_file.stat().st_size,
            "backup_size": backup_path.stat().st_size
        }
        
    except Exception as e:
        return {"ok": False, "error": f"Failed to create backup: {str(e)}"}


def load_existing_calibration(calib_path: str) -> Dict[str, Any]:
    """
    Load and parse existing calib.json file.
    
    Returns:
        {"ok": True, "data": {...}, "hosts": [...], "tasks": {...}}
    """
    try:
        calib_file = Path(calib_path)
        if not calib_file.exists():
            # Create empty calibration structure if file doesn't exist
            return {"ok": True, "data": {}, "hosts": [], "tasks": {}}
        
        with open(calib_file, 'r', encoding='utf-8') as f:
            calib_data = json.load(f)
        
        # Analyze existing structure
        hosts = list(calib_data.keys())
        tasks = {}
        for host, host_data in calib_data.items():
            if isinstance(host_data, dict):
                tasks[host] = list(host_data.keys())
        
        return {
            "ok": True,
            "data": calib_data,
            "hosts": hosts,
            "tasks": tasks,
            "total_entries": sum(len(host_tasks) for host_tasks in tasks.values())
        }
        
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"Invalid JSON in calibration file: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"Failed to load calibration: {str(e)}"}


def merge_llm_with_existing_calib(
    existing_calib: Dict[str, Any],
    llm_calib_data: Dict[str, Any],
    host: str,
    task: str
) -> Dict[str, Any]:
    """
    Merge LLM calibration data with existing calib.json.
    Replace only the specific host+task section.
    
    Preserve:
    - All other hosts
    - All other tasks under same host  
    - Structure and metadata
    - CreatedAt timestamp for existing entries
    """
    try:
        # Create deep copy of existing calibration
        merged_calib = json.loads(json.dumps(existing_calib))
        
        # Ensure host structure exists
        if host not in merged_calib:
            merged_calib[host] = {}
        
        # Preserve createdAt if task already exists
        existing_created_at = None
        if task in merged_calib[host]:
            existing_created_at = merged_calib[host][task].get("createdAt")
        
        # Update createdAt in LLM data if preserving
        if existing_created_at:
            llm_calib_data["createdAt"] = existing_created_at
        
        # Replace the specific task with LLM data
        merged_calib[host][task] = llm_calib_data
        
        return {
            "ok": True,
            "merged_calib": merged_calib,
            "preserved_created_at": existing_created_at is not None,
            "total_hosts": len(merged_calib),
            "total_tasks": sum(len(host_data) for host_data in merged_calib.values() if isinstance(host_data, dict))
        }
        
    except Exception as e:
        return {"ok": False, "error": f"Failed to merge calibration data: {str(e)}"}


def validate_calib_structure(calib_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate calibration data structure before saving.
    
    Checks:
    - Required fields presence
    - Data types
    - Structure consistency
    """
    try:
        validation_errors = []
        validation_warnings = []
        
        if not isinstance(calib_data, dict):
            return {"ok": False, "error": "Calibration data must be a dictionary"}
        
        # Validate each host
        for host, host_data in calib_data.items():
            if not isinstance(host_data, dict):
                validation_errors.append(f"Host '{host}' data must be a dictionary")
                continue
            
            # Validate each task under host
            for task, task_data in host_data.items():
                if not isinstance(task_data, dict):
                    validation_errors.append(f"Task '{task}' under host '{host}' must be a dictionary")
                    continue
                
                # Check required fields for complete task entries
                required_fields = ["host", "task", "updatedAt"]
                optional_fields = ["fieldSelectors", "fieldKeys", "actions", "pages", "createdAt"]
                
                for field in required_fields:
                    if field not in task_data:
                        validation_errors.append(f"Missing required field '{field}' in {host}/{task}")
                
                # Validate pages structure if present
                if "pages" in task_data:
                    pages = task_data["pages"]
                    if not isinstance(pages, list):
                        validation_errors.append(f"Pages must be a list in {host}/{task}")
                    else:
                        for i, page in enumerate(pages):
                            if not isinstance(page, dict):
                                validation_errors.append(f"Page {i} must be a dictionary in {host}/{task}")
                            elif "id" not in page:
                                validation_warnings.append(f"Page {i} missing 'id' field in {host}/{task}")
                
                # Validate actions structure if present
                if "actionsDetail" in task_data:
                    actions = task_data["actionsDetail"]
                    if not isinstance(actions, list):
                        validation_errors.append(f"actionsDetail must be a list in {host}/{task}")
                    else:
                        for i, action in enumerate(actions):
                            if not isinstance(action, dict):
                                validation_errors.append(f"Action {i} must be a dictionary in {host}/{task}")
                            elif "id" not in action or "label" not in action:
                                validation_warnings.append(f"Action {i} missing required fields in {host}/{task}")
        
        return {
            "ok": len(validation_errors) == 0,
            "errors": validation_errors,
            "warnings": validation_warnings,
            "total_hosts": len(calib_data),
            "validation_passed": len(validation_errors) == 0 and len(validation_warnings) == 0
        }
        
    except Exception as e:
        return {"ok": False, "error": f"Validation failed: {str(e)}"}


def save_calibration_file(calib_data: Dict[str, Any], calib_path: str) -> Dict[str, Any]:
    """
    Save calibration data to file with proper formatting.
    """
    try:
        calib_file = Path(calib_path)
        
        # Ensure directory exists
        calib_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save with proper JSON formatting (2-space indent to match original)
        with open(calib_file, 'w', encoding='utf-8') as f:
            json.dump(calib_data, f, indent=2, ensure_ascii=False)
        
        # Verify file was written correctly
        file_size = calib_file.stat().st_size
        
        return {
            "ok": True,
            "path": str(calib_file),
            "size": file_size,
            "entries": sum(len(host_data) for host_data in calib_data.values() if isinstance(host_data, dict))
        }
        
    except Exception as e:
        return {"ok": False, "error": f"Failed to save calibration file: {str(e)}"}


def preview_calib_update(
    llm_calib_data: Dict[str, Any],
    host: str,
    task: str,
    calib_path: str = "calib.json"
) -> Dict[str, Any]:
    """
    Preview what changes would be made without actually updating the file.
    Useful for validation and user confirmation.
    
    Returns:
        {
            "ok": True,
            "changes": {
                "fields_added": ["motor_no", "sasi_no"],
                "fields_updated": ["plaka_no"],
                "actions_added": ["Poliçeyi Aktifleştir"],
                "pages_added": 1,
                "pages_updated": 2
            },
            "preview_structure": {...}
        }
    """
    try:
        if not llm_calib_data.get("ok") or not llm_calib_data.get("calib_structure"):
            return {"ok": False, "error": "Invalid LLM calibration data"}
        
        # Load existing calibration
        existing_result = load_existing_calibration(calib_path)
        if not existing_result["ok"]:
            return existing_result
        
        existing_calib = existing_result["data"]
        llm_structure = llm_calib_data["calib_structure"]
        
        # Analyze changes
        changes = {"fields_added": [], "fields_updated": [], "actions_added": [], "pages_added": 0, "pages_updated": 0}
        
        # Check if host/task exists
        existing_task_data = existing_calib.get(host, {}).get(task, {})
        
        if existing_task_data:
            # Compare fields
            existing_fields = set(existing_task_data.get("fieldKeys", []))
            new_fields = set(llm_structure.get("fieldKeys", []))
            
            changes["fields_added"] = list(new_fields - existing_fields)
            changes["fields_updated"] = list(new_fields & existing_fields)
            
            # Compare actions
            existing_actions = set(existing_task_data.get("actions", []))
            new_actions = set(llm_structure.get("actions", []))
            
            changes["actions_added"] = list(new_actions - existing_actions)
            
            # Compare pages
            existing_pages = len(existing_task_data.get("pages", []))
            new_pages = len(llm_structure.get("pages", []))
            
            if new_pages > existing_pages:
                changes["pages_added"] = new_pages - existing_pages
            else:
                changes["pages_updated"] = existing_pages
        else:
            # New host/task - everything is added
            changes["fields_added"] = llm_structure.get("fieldKeys", [])
            changes["actions_added"] = llm_structure.get("actions", [])
            changes["pages_added"] = len(llm_structure.get("pages", []))
        
        # Create preview structure
        preview_calib = json.loads(json.dumps(existing_calib))
        if host not in preview_calib:
            preview_calib[host] = {}
        preview_calib[host][task] = llm_structure
        
        return {
            "ok": True,
            "changes": changes,
            "preview_structure": preview_calib,
            "is_new_entry": not bool(existing_task_data),
            "total_entries_after": sum(len(host_data) for host_data in preview_calib.values() if isinstance(host_data, dict))
        }
        
    except Exception as e:
        return {"ok": False, "error": f"Preview failed: {str(e)}"}