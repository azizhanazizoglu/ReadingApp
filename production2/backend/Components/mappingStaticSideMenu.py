"""
mappingStaticSideMenu.py

Static mapping component for finding hamburger/menu toggle buttons.
Looks for elements with lucide-menu icons or similar menu indicators.
"""

from __future__ import annotations

import re
import json
import hashlib
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pathlib import Path as _Path
from dataclasses import asdict

# Make production2 importable to reach memory and config
_this = _Path(__file__).resolve()
_root = _this.parents[2]  # production2 root
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from config import get_static_max_candidates_go_user_task, get_map_user_task  # type: ignore
from memory import MappingJson, MappingMeta, MappingAction, MappingCandidate  # type: ignore

def map_side_menu_static(html: Optional[str] = None, name: Optional[str] = None) -> MappingJson:
    """
    Scan filtered HTML for side menu / hamburger toggle buttons and save a mapping JSON.
    
    Specifically looks for:
    - SVG elements with class 'lucide-menu' or similar
    - Buttons with menu icons
    - Elements with menu-related aria attributes

    Args:
        html: filtered HTML; if None, uses memory.html.get_last_html()
        name: optional base name for the mapping file
        
    Returns: 
        MappingJson (meta, mapping, candidates)
    """
    # Menu icon indicators - common class patterns for menu toggles
    menu_icon_classes = [
        "lucide-menu",
        "menu-icon",
        "hamburger",
        "navbar-toggler",
        "fa-bars"
    ]
    
    # Menu-related aria attributes
    menu_aria_keywords = [
        "menu",
        "hamburger",
        "toggle",
        "navigation"
    ]
    
    # Source HTML (filtered) - require explicit input
    filtered_html = html
    if not filtered_html:
        return {"ok": False, "error": "no_filtered_html"}

    # Try BeautifulSoup; fallback to regex if unavailable
    soup = None
    try:
        from bs4 import BeautifulSoup  # type: ignore
        soup = BeautifulSoup(filtered_html, "html.parser")
    except Exception:
        soup = None

    candidates: List[Dict[str, Any]] = []

    def has_menu_icon_class(tag) -> bool:
        """Check if tag has any menu-related classes."""
        if not tag:
            return False
            
        class_attr = tag.get("class", [])
        if isinstance(class_attr, str):
            class_attr = class_attr.split()
            
        return any(menu_cls in " ".join(class_attr).lower() for menu_cls in menu_icon_classes)
    
    def contains_menu_icon(tag) -> bool:
        """Check if tag contains a menu icon (SVG or i element with menu classes)."""
        if not tag:
            return False
            
        # Check for direct SVG with menu class
        svgs = tag.find_all("svg") if hasattr(tag, "find_all") else []
        for svg in svgs:
            if has_menu_icon_class(svg):
                return True
                
        # Check for i elements (font icons)
        i_elems = tag.find_all("i") if hasattr(tag, "find_all") else []
        for i in i_elems:
            if has_menu_icon_class(i):
                return True
                
        return False
    
    def is_menu_related(tag) -> bool:
        """Check if tag has menu-related attributes."""
        if not tag:
            return False
            
        # Check aria attributes
        for attr in ["aria-label", "title", "alt"]:
            value = tag.get(attr, "").lower()
            if any(keyword in value for keyword in menu_aria_keywords):
                return True
                
        return False
    
    def score_menu_button(tag) -> int:
        """Score a tag based on how likely it is to be a menu toggle button."""
        if not tag:
            return 0
            
        score = 0
        tag_name = getattr(tag, "name", "")
        
        # Button or anchor gets base score
        if tag_name == "button":
            score += 5
        elif tag_name == "a":
            score += 3
        elif tag_name == "div" and tag.get("role") == "button":
            score += 4
            
        # Has menu icon class directly
        if has_menu_icon_class(tag):
            score += 7
            
        # Contains a menu icon
        if contains_menu_icon(tag):
            score += 6
            
        # Menu-related attributes
        if is_menu_related(tag):
            score += 4
            
        # Small menu buttons tend to be toggles
        try:
            width = tag.get("width")
            height = tag.get("height")
            if width and height and int(width) <= 40 and int(height) <= 40:
                score += 2
        except (ValueError, TypeError):
            pass
            
        return score

    def selectors_for(tag) -> Dict[str, List[str]]:
        """Generate CSS and heuristic selectors for the tag."""
        sels: Dict[str, List[str]] = {"css": [], "heuristic": []}
        if tag is None:
            return sels
            
        t = getattr(tag, "name", "") or "*"
        tid = (tag.get("id") or "").strip()
        tclass = tag.get("class", [])
        if isinstance(tclass, str):
            tclass = tclass.split()
        class_str = " ".join(tclass).strip()
        
        aria_label = (tag.get("aria-label") or "").strip()
        title = (tag.get("title") or "").strip()
        role = (tag.get("role") or "").strip()
        
        # ID selector (most specific)
        if tid:
            sels["css"].append(f"#{tid}")
            
        # Class combinations
        if class_str:
            classes = class_str.split()
            # Add specific selector for each menu-related class
            for cls in classes:
                if any(menu_cls in cls.lower() for menu_cls in menu_icon_classes):
                    sels["css"].append(f"{t}.{cls}")
            
            # Add full class selector (most specific)
            if len(classes) > 0:
                class_sel = ".".join(classes)
                sels["css"].append(f"{t}.{class_sel}")
                
        # Role-based selector
        if role == "button":
            sels["css"].append(f"{t}[role='button']")
            
        # Aria attributes
        if aria_label:
            sels["css"].append(f"{t}[aria-label='{aria_label}']")
            # Partial match for menu keywords in aria-label
            for keyword in menu_aria_keywords:
                if keyword in aria_label.lower():
                    sels["css"].append(f"{t}[aria-label*='{keyword}']")
                    
        if title:
            sels["css"].append(f"{t}[title='{title}']")
            # Partial match for menu keywords in title
            for keyword in menu_aria_keywords:
                if keyword in title.lower():
                    sels["css"].append(f"{t}[title*='{keyword}']")
        
        # SVG with lucide-menu inside button
        if contains_menu_icon(tag):
            if t in ["button", "a", "div"]:
                # For button/link containing menu icon
                sels["heuristic"].append(f"{t}:has(svg.lucide-menu)")
                sels["heuristic"].append(f"{t}:has(.lucide-menu)")
                sels["heuristic"].append(f"{t}:has(svg[class*='menu'])")
                
                # XPath alternatives
                xpath_sel = f"//{t}[.//svg[contains(@class, 'lucide-menu')]]"
                sels["heuristic"].append(f"xpath:{xpath_sel}")
                
                xpath_sel_alt = f"//{t}[.//svg[contains(@class, 'menu')]]"
                sels["heuristic"].append(f"xpath:{xpath_sel_alt}")
        
        # Special heuristic for data-lov attributes (from example)
        if tag.get("data-lov-name") == "Button" and contains_menu_icon(tag):
            sels["heuristic"].append(f"{t}[data-lov-name='Button']:has(svg.lucide-menu)")
            
        # Special heuristic for data-component attributes
        if tag.get("data-component-name") == "Button" and contains_menu_icon(tag):
            sels["heuristic"].append(f"{t}[data-component-name='Button']:has(svg.lucide-menu)")
        
        return sels

    if soup is not None:
        # Find all potential menu toggle elements
        
        # Strategy 1: Look for SVG with lucide-menu class
        svg_elements = soup.find_all("svg", attrs={"class": re.compile(r"lucide-menu", re.I)})
        for svg in svg_elements:
            # Find the closest button or clickable ancestor
            parent = svg.parent
            max_depth = 3  # Limit search depth
            depth = 0
            
            while parent and depth < max_depth:
                if parent.name in ["button", "a"] or parent.get("role") == "button":
                    score = score_menu_button(parent)
                    if score >= 7:  # Threshold for inclusion
                        attributes = {}
                        for attr in ["id", "class", "aria-label", "title", "data-lov-name", "data-component-name"]:
                            if parent.get(attr):
                                attributes[attr] = parent.get(attr)
                                
                        selectors = selectors_for(parent)
                        candidates.append({
                            "type": parent.name,
                            "text": "Menu Toggle",
                            "attributes": attributes,
                            "selectors": selectors,
                            "score": score,
                            "action": "click",
                            "icon_type": "lucide-menu"
                        })
                    break
                parent = parent.parent
                depth += 1
        
        # Strategy 2: Look for buttons with menu related aria attributes
        button_elements = soup.find_all(["button", "a", "div"])
        for button in button_elements:
            if is_menu_related(button) or contains_menu_icon(button):
                score = score_menu_button(button)
                if score >= 6:  # Threshold for inclusion
                    attributes = {}
                    for attr in ["id", "class", "aria-label", "title", "data-lov-name", "data-component-name"]:
                        if button.get(attr):
                            attributes[attr] = button.get(attr)
                            
                    selectors = selectors_for(button)
                    candidates.append({
                        "type": button.name,
                        "text": button.get_text(strip=True) or "Menu Toggle",
                        "attributes": attributes,
                        "selectors": selectors,
                        "score": score,
                        "action": "click",
                        "icon_type": "menu-button"
                    })
    else:
        # Regex fallback for when BeautifulSoup is not available
        html_src = filtered_html
        
        # Look for buttons containing svg with lucide-menu class
        button_pattern = re.compile(r'<button[^>]*>.*?class="[^"]*lucide-menu[^"]*".*?</button>', re.IGNORECASE | re.DOTALL)
        for match in button_pattern.finditer(html_src):
            candidates.append({
                "type": "button",
                "text": "Menu Toggle",
                "attributes": {"detected_by": "regex"},
                "selectors": {
                    "css": ["button:has(.lucide-menu)"],
                    "heuristic": ["xpath://button[.//svg[contains(@class, 'lucide-menu')]]"]
                },
                "score": 8,
                "action": "click",
                "icon_type": "lucide-menu"
            })
            
        # Look for any element with aria-label containing menu keywords
        aria_pattern = re.compile(r'<([a-z]+)[^>]*aria-label="[^"]*(?:menu|hamburger|toggle)[^"]*"[^>]*>', re.IGNORECASE)
        for match in aria_pattern.finditer(html_src):
            tag_name = match.group(1)
            candidates.append({
                "type": tag_name,
                "text": "Menu Toggle",
                "attributes": {"detected_by": "regex_aria"},
                "selectors": {
                    "css": [f"{tag_name}[aria-label*='menu' i]"],
                    "heuristic": [f"xpath://{tag_name}[contains(translate(@aria-label, 'MENU', 'menu'), 'menu')]"]
                },
                "score": 7,
                "action": "click",
                "icon_type": "aria-menu"
            })

    # prioritize candidates by score desc
    candidates.sort(key=lambda c: c.get("score", 0), reverse=True)
    
    # Limit candidates
    max_candidates = get_static_max_candidates_go_user_task()
    candidates = candidates[:max_candidates]

    # Prepare output dir and filename
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%fZ")
    base = name or "menu_toggle"
    out_dir = _root / "tmp" / "jsonMappings"
    out_dir.mkdir(parents=True, exist_ok=True)

    # compute a local fingerprint (stateless)
    try:
        html_fp = hashlib.sha256(filtered_html.encode("utf-8")).hexdigest()
    except Exception:
        html_fp = None

    max_alt = int(get_map_user_task("max_alternatives", 12) or 12)

    # Build dataclass objects from results
    primary_selector = (
        candidates[0]["selectors"]["css"][0]
        if candidates and candidates[0]["selectors"]["css"]
        else (
            candidates[0]["selectors"]["heuristic"][0]
            if candidates and candidates[0]["selectors"]["heuristic"]
            else None
        )
    )
    alternatives: List[str] = [
        *(candidates[0]["selectors"].get("css", []) if candidates else []),
        *(candidates[0]["selectors"].get("heuristic", []) if candidates else []),
    ][:max_alt]

    meta_dc = MappingMeta(
        timestamp=ts,
        source="map_side_menu_static",
        variants=menu_icon_classes,
        html_fingerprint=html_fp,
    )
    action_dc = MappingAction(
        primary_selector=primary_selector,
        action="click",
        alternatives=alternatives,
    )
    candidates_dc: List[MappingCandidate] = [
        MappingCandidate(
            type=c.get("type", "*"),
            text=c.get("text", ""),
            attributes=c.get("attributes", {}),
            selectors=c.get("selectors", {}),
            score=int(c.get("score", 0)),
            action=c.get("action", "click"),
        )
        for c in candidates
    ]

    mapping_json = MappingJson(meta=meta_dc, mapping=action_dc, candidates=candidates_dc)

    out_path = out_dir / f"{base}_{ts}.json"
    out_path.write_text(json.dumps(asdict(mapping_json), indent=2, ensure_ascii=False), encoding="utf-8")

    return mapping_json


# For direct testing/execution
if __name__ == "__main__":
    # Example test HTML with a hamburger button similar to the provided example
    test_html = """
    <div>
        <button data-lov-id="src/pages/Dashboard.tsx:40:10" data-lov-name="Button" data-component-path="src/pages/Dashboard.tsx" 
            data-component-line="40" data-component-file="Dashboard.tsx" data-component-name="Button" 
            data-component-content="%7B%7D" class="inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" 
                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" 
                class="lucide lucide-menu h-5 w-5" data-lov-id="src/pages/Dashboard.tsx:45:12" data-lov-name="Menu">
                <line x1="4" x2="20" y1="12" y2="12"></line>
                <line x1="4" x2="20" y1="6" y2="6"></line>
                <line x1="4" x2="20" y1="18" y2="18"></line>
            </svg>
        </button>
        <a href="#" aria-label="Toggle menu" class="navbar-toggler">
            <i class="fa fa-bars"></i>
        </a>
    </div>
    """
    
    result = map_side_menu_static(test_html, "test_menu_toggle")
    print(f"Found {len(result.candidates)} menu toggle candidates")
    if result.candidates:
        print(f"Top candidate: {result.candidates[0].type} with score {result.candidates[0].score}")
        print(f"Primary selector: {result.mapping.primary_selector}")
