#!/usr/bin/env python3
"""
Instagram Browser Helper
Assists with extracting content from Instagram using the browser.
This works with OpenClaw's browser automation.
"""

import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from database.database_manager import DatabaseManager, Reel


def process_clipboard_url(url: str, db: DatabaseManager):
    """Process a URL from clipboard"""
    print(f"Processing URL: {url}")
    
    # Extract shortcode
    import re
    match = re.search(r'/reel[s]?/([A-Za-z0-9_-]+)', url)
    if not match:
        print("Invalid Instagram URL")
        return
    
    shortcode = match.group(1)
    
    # Check if already exists
    existing = db.get_reel_by_instagram_id(shortcode)
    if existing:
        print(f"Reel already in database (ID: {existing.id})")
        return existing.id
    
    # Create reel entry
    reel = Reel(
        instagram_id=shortcode,
        url=url,
        processed=False,
        processing_status='pending'
    )
    
    reel_id = db.save_reel(reel)
    print(f"✓ Added reel {shortcode} with ID {reel_id}")
    return reel_id


def manual_entry(db: DatabaseManager):
    """Interactive manual entry"""
    print("\n=== Manual Reel Entry ===")
    print("Enter reel details (or 'done' to finish):\n")
    
    entries = []
    
    while True:
        url = input("URL: ").strip()
        if url.lower() == 'done':
            break
        if not url:
            continue
        
        # Basic validation
        if 'instagram.com' not in url:
            print("Warning: URL doesn't contain instagram.com")
            continue
        
        caption = input("Caption (enter/paste, blank for none): ").strip()
        author = input("Author username: ").strip()
        
        entry = {
            'url': url,
            'caption': caption,
            'author': author
        }
        entries.append(entry)
        print("✓ Entry added\n")
    
    # Process all entries
    print(f"\nProcessing {len(entries)} entries...")
    for entry in entries:
        process_clipboard_url(entry['url'], db)
        # Would also save caption and author here
    
    print(f"\n✓ Total added: {len(entries)} reels")


def batch_import_from_file(filepath: str, db: DatabaseManager):
    """Import reels from a JSON/text file"""
    path = Path(filepath)
    
    if not path.exists():
        print(f"File not found: {filepath}")
        return
    
    if filepath.endswith('.json'):
        with open(filepath) as f:
            data = json.load(f)
        entries = data if isinstance(data, list) else [data]
    else:
        # Assume one URL per line
        with open(filepath) as f:
            entries = [{'url': line.strip()} for line in f if line.strip()]
    
    print(f"Found {len(entries)} entries in {filepath}")
    
    added = 0
    for entry in entries:
        url = entry.get('url', '')
        if url:
            reel_id = process_clipboard_url(url, db)
            if reel_id:
                added += 1
    
    print(f"\n✓ Added {added}/{len(entries)} reels to database")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Instagram Browser Helper - Manual data entry"
    )
    parser.add_argument('--db', default='data/instagram_content.db',
                       help='Database path')
    parser.add_argument('--import-file', help='Import from file (JSON/txt)')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode')
    
    args = parser.parse_args()
    
    db = DatabaseManager(args.db)
    
    if args.import_file:
        batch_import_from_file(args.import_file, db)
    elif args.interactive or len(sys.argv) == 1:
        manual_entry(db)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
