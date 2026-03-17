#!/usr/bin/env python3
"""
Quick Start for Instagram Content Extractor
Initializes the system and runs a demo.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.database_manager import DatabaseManager
from instagram_extractor import InstagramExtractor


def main():
    print("=" * 60)
    print("INSTAGRAM CONTENT EXTRACTOR - QUICK START")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    db = DatabaseManager()
    print("   ✓ Database ready")
    
    # Initialize extractor
    print("\n2. Initializing extractor...")
    extractor = InstagramExtractor()
    print("   ✓ Extractor ready")
    
    # Show stats
    stats = db.get_statistics()
    print("\n3. Current database status:")
    print(f"   • Reels: {stats.get('total_reels', 0)}")
    print(f"   • Processed: {stats.get('processed_reels', 0)}")
    print(f"   • Resources: {stats.get('total_resources', 0)}")
    
    print("\n" + "=" * 60)
    print("USAGE:")
    print("=" * 60)
    print("""
Add a reel:
  python instagram_extractor.py add-url "https://instagram.com/reel/ABC123" \
    --caption "Description" --author "username"

Process all pending:
  python instagram_extractor.py process-all

Search resources:
  python instagram_extractor.py search "pdf template"

Export to file:
  python instagram_extractor.py export resources.json

Show report:
  python instagram_extractor.py report

Manual entry (interactive):
  python scripts/instagram_browser_helper.py -i

List files:
  ls -la data/
  ls -la downloads/
""")
    print("=" * 60)


if __name__ == '__main__':
    main()
