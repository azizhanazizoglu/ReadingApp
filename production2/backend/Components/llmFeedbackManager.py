"""
LLM Feedback Manager Component

This component reads F3 LLM mapping files from tmp/JpegJsonWebpageHtml and updates calib.json
while preserving the exact format you have defined.
"""

import os
import json
import glob
import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


class LLMFeedbackManager:
    def __init__(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.calib_path = os.path.join(self.base_dir, "calib.json")
        self.mapping_dir = os.path.join(self.base_dir, "tmp", "JpegJsonWebpageHtml")
        self.single_mapping_file = os.path.join(self.mapping_dir, "latest_mapping.json")
    
    def load_latest_mapping_files(self) -> List[Dict[str, Any]]:
        """Load all recent mapping files from F3 LLM session"""
        try:
            mapping_files = glob.glob(os.path.join(self.mapping_dir, "*_mapping.json"))
            if not mapping_files:
                return []
            
            # Sort by modification time to identify recent session
            mapping_files.sort(key=os.path.getmtime, reverse=True)
            
            # Take files from the most recent session (within last 10 minutes)
            if mapping_files:
                latest_time = os.path.getmtime(mapping_files[0])
                session_files = []
                for file_path in mapping_files:
                    file_time = os.path.getmtime(file_path)
                    # If file is within 10 minutes of the latest file, consider it part of same session
                    if (latest_time - file_time) <= 600:  # 10 minutes
                        session_files.append(file_path)
                    else:
                        break
                
                # Now sort session files chronologically (oldest first for proper page sequence)
                session_files.sort(key=os.path.getmtime, reverse=False)
                recent_files = session_files
            else:
                recent_files = []
            
            mappings = []
            for file_path in recent_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Extract URL from file or use default pattern
                        if data.get("ok"):
                            mappings.append(data)
                except Exception as e:
                    print(f"[LLM-FEEDBACK] Error reading {file_path}: {e}")
                    continue
            
            return mappings
        except Exception as e:
            print(f"[LLM-FEEDBACK] Error loading mapping files: {e}")
            return []
    
    def convert_mappings_to_calib_format(self, mappings: List[Dict[str, Any]], host: str, task: str) -> Dict[str, Any]:
        """Convert F3 mapping files to calib.json format preserving your structure"""
        try:
            if not mappings:
                return {"ok": False, "reason": "no_mappings"}
            
            # Group mappings by page type
            fill_form_pages = []
            final_page = None
            
            for mapping in mappings:
                if mapping.get("page_kind") == "fill_form":
                    fill_form_pages.append(mapping)
                elif mapping.get("page_kind") == "final_activation":
                    final_page = mapping
            
            if not fill_form_pages and not final_page:
                return {"ok": False, "reason": "no_valid_pages"}
            
            # Canonical page ordering (user expects first page = traffic-insurance so TSX flow works)
            # We classify each fill_form mapping into a page_type key we can sort by.
            def _classify_page(mp: Dict[str, Any]) -> str:
                fm = mp.get("field_mapping", {}) or {}
                # traffic-insurance detection (id based #plateNo)
                if fm.get("plaka_no") == "#plateNo":
                    return "traffic"
                # vehicle-details detection (data-lov-id contains VehicleDetails)
                if any("VehicleDetails" in str(v) for v in fm.values()):
                    return "vehicle"
                # generic other fill form page (keep after known ones)
                return "other"

            ordering_priority = {"traffic": 1, "vehicle": 2, "other": 5}
            # Sort fill_form_pages deterministically by priority, then by number of mapped fields descending
            fill_form_pages.sort(key=lambda mp: (ordering_priority.get(_classify_page(mp), 9), -len((mp.get("field_mapping") or {}))))

            # Build calib pages in your format (after ordering)
            calib_pages = []
            page_counter = 1
            
            # Add fill form pages
            for i, mapping in enumerate(fill_form_pages):
                field_mapping = mapping.get("field_mapping", {})
                actions = mapping.get("actions", [])
                
                # Determine URL pattern (you can enhance this logic)
                url_sample = ""
                if field_mapping.get("plaka_no") == "#plateNo":
                    url_sample = "https://preview--screen-to-data.lovable.app/traffic-insurance"
                elif "VehicleDetails" in str(field_mapping):
                    url_sample = "https://preview--screen-to-data.lovable.app/vehicle-details"
                
                # Build action detail (keep your single Action 1 format)
                action_detail = []
                if actions:
                    # For now, use first action - you can enhance this
                    action_detail.append({
                        "id": "a1",
                        "label": "Action 1", 
                        "selector": self._extract_action_selector(mapping, actions[0])
                    })
                
                calib_page = {
                    "id": f"p_mfr{page_counter}",
                    "name": f"Page {page_counter}",
                    "urlPattern": "",
                    "urlSample": url_sample,
                    "fieldSelectors": field_mapping,
                    "fieldKeys": list(field_mapping.keys()),
                    "executionOrder": [],
                    "actionsDetail": action_detail,
                    "criticalFields": list(field_mapping.keys())[:1] if field_mapping else [],
                    "isLast": False
                }
                calib_pages.append(calib_page)
                page_counter += 1
            
            # Add final page if exists
            if final_page:
                actions = final_page.get("actions", [])
                action_detail = []
                if actions:
                    action_detail.append({
                        "id": "a1",
                        "label": "Action 1",
                        "selector": self._extract_action_selector(final_page, actions[0])
                    })
                
                final_calib_page = {
                    "id": f"p_mfr{page_counter}",
                    "name": f"Page {page_counter}",
                    "urlPattern": "",
                    "urlSample": "https://preview--screen-to-data.lovable.app/insurance-quote",
                    "fieldSelectors": {},
                    "fieldKeys": [],
                    "executionOrder": [],
                    "actionsDetail": action_detail,
                    "criticalFields": [],
                    "isLast": True
                }
                calib_pages.append(final_calib_page)
            
            # Root structure policy (Option A confirmed by user):
            #   Root fieldSelectors MUST come from the FIRST (traffic) page only.
            #   Ensure that first page is traffic (ordering above enforces this when available).
            root_field_selectors: Dict[str, str] = {}
            root_field_keys: List[str] = []
            root_action_detail: List[Dict[str, Any]] = []

            if calib_pages:
                first_page = calib_pages[0]
                root_field_selectors = first_page.get("fieldSelectors", {})
                root_field_keys = first_page.get("fieldKeys", [])
                if first_page.get("actionsDetail"):
                    # Clone first action detail but keep same shape
                    first_action_detail = first_page["actionsDetail"][0]
                    root_action_detail = [{
                        "id": first_action_detail.get("id", "a1"),
                        "label": first_action_detail.get("label", "Action 1"),
                        "selector": first_action_detail.get("selector", "")
                    }]
            
            result = {
                "ok": True,
                "fieldSelectors": root_field_selectors,
                "fieldKeys": root_field_keys,
                "actions": ["Action 1"] if root_action_detail else [],
                "actionsDetail": root_action_detail,
                "actionsExecutionOrder": ["Action 1"] if root_action_detail else [],
                "executionOrder": [],
                "criticalFields": root_field_keys[:1] if root_field_keys else [],
                "pages": calib_pages,
                "currentPageId": calib_pages[0]["id"] if calib_pages else "",
                "host": host,
                "task": task,
                "updatedAt": datetime.datetime.utcnow().isoformat() + "Z",
                "createdAt": datetime.datetime.utcnow().isoformat() + "Z"
            }
            
            return result
            
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def _extract_action_selector(self, mapping: Dict[str, Any], action: str) -> str:
        """Extract action selector from mapping data"""
        # Check if there's a direct selector in the mapping
        # This is a simplified version - you may need to enhance based on actual F3 output
        
        # For final page actions
        if mapping.get("page_kind") == "final_activation" and "Aktifleştir" in action:
            return "[data-lov-id=\"src/pages/InsuranceQuote.tsx:231:10\"]"  # From your logs
        
        # For traffic insurance page
        if mapping.get("field_mapping", {}).get("plaka_no") == "#plateNo":
            return "[data-lov-id=\"src/pages/TrafficInsurance.tsx:191:10\"]"  # From your logs
        
        # For vehicle details page  
        field_mapping = mapping.get("field_mapping", {})
        if any("VehicleDetails" in str(v) for v in field_mapping.values()):
            return "[data-lov-id=\"src/pages/VehicleDetails.tsx:189:10\"]"  # From your logs
        
        # Default fallback
        return ""
    
    def update_calib_from_latest_mappings(self, host: str, task: str) -> Dict[str, Any]:
        """Main method to update calib.json from latest F3 LLM session"""
        try:
            # Load F3 mapping files
            mappings = self.load_latest_mapping_files()
            if not mappings:
                return {"calib_updated": False, "reason": "no_mapping_files"}
            
            # Convert to calib format
            calib_data = self.convert_mappings_to_calib_format(mappings, host, task)
            if not calib_data.get("ok"):
                return {"calib_updated": False, "reason": calib_data.get("reason", "conversion_failed")}
            
            # Load current calib.json
            with open(self.calib_path, 'r', encoding='utf-8') as f:
                calib = json.load(f)
            
            # Update the specific host/task entry
            if host not in calib:
                calib[host] = {}
            
            # Keep existing metadata if it exists
            existing_entry = calib[host].get(task, {})
            created_at = existing_entry.get("createdAt", calib_data["createdAt"])
            
            # Update with new data
            calib_data["createdAt"] = created_at
            calib[host][task] = calib_data
            
            # Save updated calib.json
            with open(self.calib_path, 'w', encoding='utf-8') as f:
                json.dump(calib, f, indent=2, ensure_ascii=False)
            
            return {
                "calib_updated": True,
                "host": host,
                "task": task,
                "pages_updated": len(calib_data.get("pages", [])),
                "mapping_files_processed": len(mappings),
                "timestamp": calib_data["updatedAt"]
            }
            
        except Exception as e:
            return {"calib_updated": False, "error": str(e)}
    
    def clean_old_mapping_files(self, keep_latest: int = 5) -> Dict[str, Any]:
        """Clean up old mapping files, keep only recent ones"""
        try:
            mapping_files = glob.glob(os.path.join(self.mapping_dir, "*_mapping.json"))
            if len(mapping_files) <= keep_latest:
                return {"cleaned": 0, "kept": len(mapping_files)}
            
            # Sort by modification time
            mapping_files.sort(key=os.path.getmtime, reverse=True)
            
            # Keep recent files, remove old ones
            files_to_keep = mapping_files[:keep_latest]
            files_to_remove = mapping_files[keep_latest:]
            
            cleaned = 0
            for file_path in files_to_remove:
                try:
                    os.remove(file_path)
                    # Also remove corresponding HTML file if exists
                    html_file = file_path.replace("_mapping.json", ".html")
                    if os.path.exists(html_file):
                        os.remove(html_file)
                    cleaned += 1
                except Exception as e:
                    print(f"[LLM-FEEDBACK] Error removing {file_path}: {e}")
            
            return {"cleaned": cleaned, "kept": len(files_to_keep)}
            
        except Exception as e:
            return {"error": str(e)}


# Global instance
llm_feedback_manager = LLMFeedbackManager()