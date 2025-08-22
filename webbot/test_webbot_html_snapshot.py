

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from webbot.test_webbot_html_mapping import readWebPage

def save_html_snapshot(html: str, filename: str):
    """Save HTML content to a file for manual inspection."""
    snapshot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tdsp', 'test_reports', 'html_snapshots'))
    os.makedirs(snapshot_dir, exist_ok=True)
    file_path = os.path.join(snapshot_dir, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[HTML SNAPSHOT] Saved to: {file_path}")


def test_webbot_html_snapshot():
    """
    Unit test: Download HTML from the site and save a snapshot for manual inspection. Print first 500 chars.
    """
    html = readWebPage()
    filename = 'webbot_html_snapshot.html'
    save_html_snapshot(html, filename)
    print("\n[HTML PREVIEW] First 500 chars:\n", html[:500] + ("..." if len(html) > 500 else ""))
    assert os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'tdsp', 'test_reports', 'html_snapshots', filename))

if __name__ == "__main__":
    test_webbot_html_snapshot()
