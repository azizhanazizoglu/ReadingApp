#!/usr/bin/env python3

"""Test script to verify calib.json mapping works for insurance-quote page."""

import sys
import json
from pathlib import Path

# Add backend to path
root = Path(__file__).parent
backend_path = root / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Import the static mapping component
from backend.Components.mappingStaticFillForms import static_analyze_page
from backend.Components.calibRuntimeLookup import resolve_site_mapping
import config

def test_calib_mapping():
    """Test if calib.json mapping is correctly applied for insurance-quote page."""
    
    # Load config
    cfg = config.load_config()
    
    # Test parameters
    host = "preview--screen-to-data.lovable.app"
    task = "Yeni Trafik"
    url = "https://preview--screen-to-data.lovable.app/insurance-quote"
    
    # Sample HTML (minimal)
    html = """
    <html>
    <body>
    <button data-lov-id="src/pages/InsuranceQuote.tsx:231:10">Poliçeyi Aktifleştir</button>
    </body>
    </html>
    """
    
    print("=== Testing Calib Mapping ===")
    print(f"Host: {host}")
    print(f"Task: {task}")
    print(f"URL: {url}")
    print()
    
    # 1. Test calib lookup directly
    print("1. Testing calib lookup...")
    site_mapping = resolve_site_mapping(host, task, cfg)
    print(f"Site mapping keys: {list(site_mapping.keys())}")
    print(f"Pages found: {len(site_mapping.get('pages', []))}")
    
    if site_mapping.get('pages'):
        for i, page in enumerate(site_mapping['pages']):
            print(f"  Page {i+1}: {page.get('name')} - {page.get('urlSample')}")
            if page.get('actionsDetail'):
                for j, action in enumerate(page['actionsDetail']):
                    print(f"    Action {j+1}: {action.get('label')} -> {action.get('selector')}")
    print()
    
    # 2. Test static analyze
    print("2. Testing static analyze...")
    result = static_analyze_page(html, url, task, cfg)
    print(f"Analysis OK: {result.get('ok')}")
    print(f"Actions found: {result.get('actions', [])}")
    print(f"Field mapping: {result.get('field_mapping', {})}")
    print(f"Mapping sources: {result.get('mapping_source', {})}")
    print()
    
    # 3. Check for CSS actions
    print("3. Checking for CSS selector actions...")
    actions = result.get('actions', [])
    css_actions = [a for a in actions if a.startswith('css#')]
    text_actions = [a for a in actions if not a.startswith('css#')]
    
    print(f"CSS selector actions: {css_actions}")
    print(f"Text-based actions: {text_actions}")
    
    if css_actions:
        for css_action in css_actions:
            selector = css_action[4:]  # Remove 'css#' prefix
            print(f"  CSS selector: {selector}")
            # Check if selector exists in HTML
            if selector in html:
                print(f"    ✓ Selector found in HTML")
            else:
                print(f"    ✗ Selector NOT found in HTML")
    
    return result

if __name__ == "__main__":
    test_calib_mapping()