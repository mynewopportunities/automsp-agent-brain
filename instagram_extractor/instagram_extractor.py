#!/usr/bin/env python3
"""
Instagram Content Extractor
Main entry point for extracting and organizing Instagram saved content.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from database.database_manager import DatabaseManager, Reel, Resource
from processors.content_analyzer import ResourceExtractor


class InstagramExtractor:
    """Main orchestrator for the Instagram extraction pipeline"""
    
    def __init__(self, db_path: str = "data/instagram_content.db"):
        self.db = DatabaseManager(db_path)
        self.analyzer = ResourceExtractor(language="mixed")
    
    def add_reel_from_url(self, url: str, caption: str = "", 
                          author: str = "", saved_date: str = None) -> int:
        """Manually add a reel from URL for processing"""
        import re
        match = re.search(r'/reel[s]?/([A-Za-z0-9_-]+)', url)
        shortcode = match.group(1) if match else url.split('/')[-1].split('?')[0]
        
        reel = Reel(
            instagram_id=shortcode,
            url=url,
            caption=caption,
            author_username=author,
            saved_at=saved_date or datetime.now().isoformat(),
            processed=False,
            processing_status='pending'
        )
        
        reel_id = self.db.save_reel(reel)
        print(f"✓ Added reel: {shortcode} (ID: {reel_id})")
        return reel_id
    
    def process_reel(self, reel_id: int) -> dict:
        """Process a single reel to extract resources"""
        reel = self.db.get_reel_by_id(reel_id)
        if not reel:
            return {'status': 'error', 'message': 'Reel not found'}
        
        if reel.processed:
            return {'status': 'skipped', 'message': 'Already processed'}
        
        self.db.update_reel_status(reel_id, 'processing')
        
        try:
            # Extract resources from caption
            resources = self.analyzer.extract_resources(
                reel.caption or '',
                reel.content_text or ''
            )
            
            saved_resources = []
            for res in resources:
                if res.confidence > 0.5:
                    resource = Resource(
                        reel_id=reel_id,
                        resource_type=res.resource_type,
                        title=res.title,
                        description=res.description,
                        url=res.urls[0] if res.urls else '',
                        source_mention=res.context,
                        action_required=res.action_required
                    )
                    resource_id = self.db.save_resource(resource)
                    saved_resources.append({
                        'id': resource_id,
                        'type': res.resource_type,
                        'title': res.title[:50],
                        'action': res.action_required
                    })
            
            self.db.update_reel_status(reel_id, 'completed')
            
            return {
                'status': 'success',
                'reel_id': reel_id,
                'resources_found': len(saved_resources),
                'resources': saved_resources
            }
            
        except Exception as e:
            self.db.update_reel_status(reel_id, 'failed', str(e))
            return {'status': 'error', 'message': str(e)}
    
    def process_all_pending(self) -> dict:
        """Process all unprocessed reels"""
        unprocessed = self.db.get_unprocessed_reels(limit=100)
        results = {'processed': 0, 'failed': 0}
        
        for reel in unprocessed:
            if reel.id:
                result = self.process_reel(reel.id)
                if result['status'] == 'success':
                    results['processed'] += 1
                    print(f"  ✓ Processed reel {reel.id}: {result['resources_found']} resources")
                else:
                    results['failed'] += 1
                    print(f"  ✗ Failed reel {reel.id}: {result['message']}")
        
        return results
    
    def search_resources(self, query: str) -> list:
        """Search for resources by query"""
        return self.db.search_resources(query)
    
    def export_resources(self, output_path: str, format: str = 'json'):
        """Export all resources to a file"""
        resources = self.db.get_all_resources()
        
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(resources, f, indent=2, default=str)
        
        print(f"✓ Exported {len(resources)} resources to {output_path}")
    
    def print_report(self):
        """Generate and print summary report"""
        stats = self.db.get_statistics()
        
        print("\n" + "=" * 50)
        print("INSTAGRAM CONTENT EXTRACTION SUMMARY")
        print("=" * 50)
        print(f"Total Reels:     {stats.get('total_reels', 0)}")
        print(f"Processed:       {stats.get('processed_reels', 0)}")
        print(f"Pending:         {stats.get('pending_reels', 0)}")
        print(f"\nResources Found: {stats.get('total_resources', 0)}")
        print("\nBy Type:")
        for res_type, count in stats.get('resource_types', {}).items():
            print(f"  • {res_type}: {count}")
        print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Instagram Saved Content Extractor"
    )
    
    subparsers = parser.add_subparsers(dest='command')
    
    # Add URL
    add = subparsers.add_parser('add-url', help='Add reel from URL')
    add.add_argument('url', help='Instagram reel URL')
    add.add_argument('--caption', '-c', default='', help='Caption text')
    add.add_argument('--author', '-a', default='', help='Author username')
    
    # Process
    subparsers.add_parser('process-all', help='Process all pending reels')
    
    # Search
    search = subparsers.add_parser('search', help='Search resources')
    search.add_argument('query', help='Search query')
    
    # Export
    export = subparsers.add_parser('export', help='Export resources')
    export.add_argument('output', help='Output file path')
    export.add_argument('--format', default='json', choices=['json', 'csv'])
    
    # Report
    subparsers.add_parser('report', help='Show summary report')
    
    args = parser.parse_args()
    
    extractor = InstagramExtractor()
    
    if args.command == 'add-url':
        extractor.add_reel_from_url(args.url, args.caption, args.author)
        print("✓ Reel added. Run 'process-all' to analyze.")
    
    elif args.command == 'process-all':
        print("Processing pending reels...")
        results = extractor.process_all_pending()
        print(f"\nComplete: {results['processed']} processed, {results['failed']} failed")
    
    elif args.command == 'search':
        resources = extractor.search_resources(args.query)
        print(f"\nFound {len(resources)} resources:\n")
        for r in resources[:10]:
            print(f"  [{r['resource_type']}] {r['title'][:60]}")
            if r.get('url'):
                print(f"    → {r['url']}")
            print()
    
    elif args.command == 'export':
        extractor.export_resources(args.output, args.format)
    
    elif args.command == 'report':
        extractor.print_report()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
