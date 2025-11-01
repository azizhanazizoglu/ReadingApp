"""
Mapping File Processor Component

This component handles reading and processing F3 LLM mapping files to extract
working selectors and convert them to calib.json compatible format.
"""

import os
import json
import glob
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path


class MappingFileProcessor:
    def __init__(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.mapping_dir = os.path.join(self.base_dir, "tmp", "JpegJsonWebpageHtml")
    
    def get_latest_session_files(self, max_age_minutes: int = 30) -> List[str]:
        """Get mapping files from the latest F3 LLM session"""
        try:
            mapping_files = glob.glob(os.path.join(self.mapping_dir, "*_mapping.json"))
            if not mapping_files:
                return []
            
            # Sort by modification time
            mapping_files.sort(key=os.path.getmtime, reverse=True)
            
            # Get files from recent session (assuming they're created within max_age_minutes)
            import time
            current_time = time.time()
            session_files = []
            
            for file_path in mapping_files:
                file_time = os.path.getmtime(file_path)
                age_minutes = (current_time - file_time) / 60
                
                if age_minutes <= max_age_minutes:
                    session_files.append(file_path)
                else:
                    break  # Files are sorted by time, so we can break here
            
            return session_files
            
        except Exception as e:
            print(f"[MAPPING-PROCESSOR] Error getting session files: {e}")
            return []
    
    def parse_mapping_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse a single mapping file and extract useful data"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data.get("ok"):
                return None
            
            # Extract URL from filename or content
            filename = os.path.basename(file_path)
            hash_part = filename.replace("_mapping.json", "")
            
            # Try to determine URL from mapping content patterns
            field_mapping = data.get("field_mapping", {})
            page_kind = data.get("page_kind", "unknown")
            actions = data.get("actions", [])
            
            # Determine page URL based on field patterns
            url = self._determine_page_url(field_mapping, page_kind, actions)
            
            result = {
                "file_path": file_path,
                "hash": hash_part,
                "url": url,
                "page_kind": page_kind,
                "field_mapping": field_mapping,
                "actions": actions,
                "is_final": page_kind == "final_activation",
                "has_fields": bool(field_mapping),
                "action_count": len(actions)
            }
            
            return result
            
        except Exception as e:
            print(f"[MAPPING-PROCESSOR] Error parsing {file_path}: {e}")
            return None
    
    def _determine_page_url(self, field_mapping: Dict[str, str], page_kind: str, actions: List[str]) -> str:
        """Determine page URL based on field patterns and actions"""
        
        # Final page detection
        if page_kind == "final_activation" or any("Aktifleştir" in action for action in actions):
            return "https://preview--screen-to-data.lovable.app/insurance-quote"
        
        # Traffic insurance page (has plateNo field)
        if field_mapping.get("plaka_no") == "#plateNo":
            return "https://preview--screen-to-data.lovable.app/traffic-insurance"
        
        # Vehicle details page (has data-lov-id patterns)
        if any("VehicleDetails" in str(selector) for selector in field_mapping.values()):
            return "https://preview--screen-to-data.lovable.app/vehicle-details"
        
        # Default fallback
        return ""
    
    def extract_action_selectors(self, mapping_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract action selectors from mapping data"""
        action_selectors = {}
        
        page_kind = mapping_data.get("page_kind", "")
        field_mapping = mapping_data.get("field_mapping", {})
        actions = mapping_data.get("actions", [])
        url = mapping_data.get("url", "")
        
        # Based on your logs, map actions to known working selectors
        for action in actions:
            if "Aktifleştir" in action and "insurance-quote" in url:
                action_selectors[action] = "[data-lov-id=\"src/pages/InsuranceQuote.tsx:231:10\"]"
            elif action == "Devam":
                if "traffic-insurance" in url:
                    action_selectors[action] = "[data-lov-id=\"src/pages/TrafficInsurance.tsx:191:10\"]"
                elif "vehicle-details" in url:
                    action_selectors[action] = "[data-lov-id=\"src/pages/VehicleDetails.tsx:189:10\"]"
            else:
                # Generic action handling
                if "traffic-insurance" in url:
                    action_selectors[action] = "[data-lov-id=\"src/pages/TrafficInsurance.tsx:191:10\"]"
                elif "vehicle-details" in url:
                    action_selectors[action] = "[data-lov-id=\"src/pages/VehicleDetails.tsx:189:10\"]"
                elif "insurance-quote" in url:
                    action_selectors[action] = "[data-lov-id=\"src/pages/InsuranceQuote.tsx:231:10\"]"
        
        return action_selectors
    
    def process_session_mappings(self) -> Dict[str, Any]:
        """Process all mappings from the latest session"""
        try:
            session_files = self.get_latest_session_files()
            if not session_files:
                return {"ok": False, "reason": "no_session_files"}
            
            processed_mappings = []
            
            for file_path in session_files:
                mapping = self.parse_mapping_file(file_path)
                if mapping:
                    # Add action selectors
                    mapping["action_selectors"] = self.extract_action_selectors(mapping)
                    processed_mappings.append(mapping)
            
            if not processed_mappings:
                return {"ok": False, "reason": "no_valid_mappings"}
            
            # Sort by page flow (traffic-insurance -> vehicle-details -> insurance-quote)
            page_order = {
                "https://preview--screen-to-data.lovable.app/traffic-insurance": 1,
                "https://preview--screen-to-data.lovable.app/vehicle-details": 2,
                "https://preview--screen-to-data.lovable.app/insurance-quote": 3
            }
            
            processed_mappings.sort(key=lambda x: page_order.get(x["url"], 999))
            
            return {
                "ok": True,
                "mappings": processed_mappings,
                "total_files": len(session_files),
                "valid_mappings": len(processed_mappings)
            }
            
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def build_calib_structure(self, processed_mappings: List[Dict[str, Any]], host: str, task: str) -> Dict[str, Any]:
        """Build calib.json structure from processed mappings"""
        try:
            if not processed_mappings:
                return {"ok": False, "reason": "no_mappings"}
            
            pages = []
            page_counter = 1
            
            for mapping in processed_mappings:
                field_mapping = mapping.get("field_mapping", {})
                actions = mapping.get("actions", [])
                action_selectors = mapping.get("action_selectors", {})
                url = mapping.get("url", "")
                is_final = mapping.get("is_final", False)
                
                # Build action detail (keep your Action 1 format)
                action_detail = []
                if actions and action_selectors:
                    # Use first action's selector
                    first_action = actions[0]
                    selector = action_selectors.get(first_action, "")
                    if selector:
                        action_detail.append({
                            "id": "a1",
                            "label": "Action 1",
                            "selector": selector
                        })
                
                page = {
                    "id": f"p_mfr{page_counter}auto",
                    "name": f"Page {page_counter}",
                    "urlPattern": "",
                    "urlSample": url,
                    "fieldSelectors": field_mapping,
                    "fieldKeys": list(field_mapping.keys()),
                    "executionOrder": [],
                    "actionsDetail": action_detail,
                    "criticalFields": list(field_mapping.keys()),
                    "isLast": is_final
                }
                
                pages.append(page)
                page_counter += 1
            
            # Build root structure from first page
            first_page = pages[0] if pages else {}
            root_field_selectors = first_page.get("fieldSelectors", {})
            root_field_keys = first_page.get("fieldKeys", [])
            root_action_detail = first_page.get("actionsDetail", [])
            
            result = {
                "ok": True,
                "fieldSelectors": root_field_selectors,
                "fieldKeys": root_field_keys,
                "actions": ["Action 1"] if root_action_detail else [],
                "actionsDetail": root_action_detail,
                "actionsExecutionOrder": ["Action 1"] if root_action_detail else [],
                "executionOrder": [],
                "criticalFields": root_field_keys[:1] if root_field_keys else [],
                "pages": pages,
                "currentPageId": first_page.get("id", ""),
                "host": host,
                "task": task
            }
            
            return result
            
        except Exception as e:
            return {"ok": False, "error": str(e)}


# Global instance
mapping_processor = MappingFileProcessor()