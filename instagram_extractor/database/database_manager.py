"""
Database Manager for Instagram Content Extraction System
Handles all database operations for storing extracted reels and resources.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class Reel:
    """Data class representing an extracted reel"""
    id: Optional[int] = None
    instagram_id: str = ""
    url: str = ""
    caption: str = ""
    author_username: str = ""
    author_full_name: str = ""
    content_text: str = ""
    content_hindi: str = ""
    summary: str = ""
    extracted_at: Optional[datetime] = None
    saved_at: Optional[datetime] = None
    media_type: str = "reel"
    duration: int = 0
    view_count: int = 0
    like_count: int = 0
    share_count: int = 0
    processed: bool = False
    processing_status: str = "pending"
    error_message: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if isinstance(self.tags, str):
            self.tags = json.loads(self.tags)


@dataclass
class Resource:
    """Data class representing a resource/document mentioned in a reel"""
    id: Optional[int] = None
    reel_id: int = 0
    resource_type: str = ""
    title: str = ""
    description: str = ""
    url: str = ""
    file_path: str = ""
    source_mention: str = ""
    timestamp_in_reel: int = 0
    extracted_at: Optional[datetime] = None
    verified: bool = False
    action_required: str = ""


class DatabaseManager:
    """Main database manager class for the Instagram extraction system"""
    
    def __init__(self, db_path: str = "data/instagram_content.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.commit()
            conn.close()
    
    def _init_database(self):
        """Initialize database with schema"""
        schema_path = Path(__file__).parent / "schema.sql"
        with self._get_connection() as conn:
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
    
    def _row_to_reel(self, row: sqlite3.Row) -> Reel:
        """Convert database row to Reel object"""
        return Reel(
            id=row['id'],
            instagram_id=row['instagram_id'],
            url=row['url'],
            caption=row['caption'],
            author_username=row['author_username'],
            author_full_name=row['author_full_name'],
            content_text=row['content_text'],
            content_hindi=row['content_hindi'],
            summary=row['summary'],
            extracted_at=row['extracted_at'],
            saved_at=row['saved_at'],
            media_type=row['media_type'],
            duration=row['duration'],
            view_count=row['view_count'],
            like_count=row['like_count'],
            share_count=row['share_count'],
            processed=bool(row['processed']),
            processing_status=row['processing_status'],
            error_message=row['error_message'] or "",
            tags=json.loads(row['tags']) if row['tags'] else []
        )
    
    def _row_to_resource(self, row: sqlite3.Row) -> Resource:
        """Convert database row to Resource object"""
        return Resource(
            id=row['id'],
            reel_id=row['reel_id'],
            resource_type=row['resource_type'],
            title=row['title'],
            description=row['description'],
            url=row['url'],
            file_path=row['file_path'],
            source_mention=row['source_mention'],
            timestamp_in_reel=row['timestamp_in_reel'],
            extracted_at=row['extracted_at'],
            verified=bool(row['verified']),
            action_required=row.get('action_required', '') if 'action_required' in row.keys() else ''
        )
    
    def save_reel(self, reel: Reel) -> int:
        """Save or update a reel and return its ID"""
        with self._get_connection() as conn:
            # Check if exists
            existing = conn.execute(
                "SELECT id FROM reels WHERE instagram_id = ?",
                (reel.instagram_id,)
            ).fetchone()
            
            if existing:
                # Update
                conn.execute("""
                    UPDATE reels SET
                        caption = ?,
                        content_text = ?,
                        content_hindi = ?,
                        summary = ?,
                        author_username = ?,
                        author_full_name = ?,
                        view_count = ?,
                        like_count = ?,
                        share_count = ?,
                        tags = ?
                    WHERE id = ?
                """, (
                    reel.caption, reel.content_text, reel.content_hindi,
                    reel.summary, reel.author_username, reel.author_full_name,
                    reel.view_count, reel.like_count, reel.share_count,
                    json.dumps(reel.tags), existing['id']
                ))
                return existing['id']
            else:
                # Insert
                cur = conn.execute("""
                    INSERT INTO reels (instagram_id, url, caption, author_username,
                                       author_full_name, content_text, content_hindi,
                                       summary, saved_at, media_type, duration,
                                       view_count, like_count, share_count, tags,
                                       processing_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    reel.instagram_id, reel.url, reel.caption, reel.author_username,
                    reel.author_full_name, reel.content_text, reel.content_hindi,
                    reel.summary, reel.saved_at, reel.media_type, reel.duration,
                    reel.view_count, reel.like_count, reel.share_count,
                    json.dumps(reel.tags), reel.processing_status
                ))
                return cur.lastrowid
    
    def get_reel_by_id(self, reel_id: int) -> Optional[Reel]:
        """Get a reel by its database ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM reels WHERE id = ?", (reel_id,)
            ).fetchone()
            return self._row_to_reel(row) if row else None
    
    def get_reel_by_instagram_id(self, instagram_id: str) -> Optional[Reel]:
        """Get a reel by its Instagram ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM reels WHERE instagram_id = ?", (instagram_id,)
            ).fetchone()
            return self._row_to_reel(row) if row else None
    
    def get_unprocessed_reels(self, limit: int = 100) -> List[Reel]:
        """Get reels that haven't been processed yet"""
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM reels 
                   WHERE processed = FALSE OR processing_status = 'pending'
                   ORDER BY saved_at DESC
                   LIMIT ?""",
                (limit,)
            ).fetchall()            return [self._row_to_reel(row) for row in rows]
    
    def update_reel_status(self, reel_id: int, status: str, error_message: str = None):
        """Update processing status of a reel"""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE reels 
                SET processing_status = ?, 
                    processed = ?,
                    error_message = COALESCE(?, error_message)
                WHERE id = ?
            """, (status, status == 'completed', error_message, reel_id))
    
    # ============ RESOURCE OPERATIONS ============
    
    def save_resource(self, resource: Resource) -> int:
        """Save a resource mentioned in a reel"""
        with self._get_connection() as conn:
            cur = conn.execute("""
                INSERT INTO resources (reel_id, resource_type, title, description,
                                     url, file_path, source_mention, timestamp_in_reel,
                                     action_required)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (resource.reel_id, resource.resource_type, resource.title,
                  resource.description, resource.url, resource.file_path,
                  resource.source_mention, resource.timestamp_in_reel,
                  resource.action_required))
            return cur.lastrowid
    
    def get_resources_by_reel(self, reel_id: int) -> List[Resource]:
        """Get all resources mentioned in a specific reel"""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM resources WHERE reel_id = ?", (reel_id,)
            ).fetchall()
            return [self._row_to_resource(row) for row in rows]
    
    def get_resources_by_type(self, resource_type: str) -> List[Resource]:
        """Get all resources of a specific type"""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM resources WHERE resource_type = ?",
                (resource_type,)
            ).fetchall()
            return [self._row_to_resource(row) for row in rows]
    
    def search_resources(self, query: str) -> List[Dict]:
        """Search resources by title or description"""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT r.*, reels.url as reel_url, reels.author_username
                FROM resources r
                JOIN reels ON r.reel_id = reels.id
                WHERE r.title LIKE ? OR r.description LIKE ? OR r.resource_type LIKE ?
                ORDER BY r.extracted_at DESC
            """, (f'%{query}%', f'%{query}%', f'%{query}%'))
            return [dict(row) for row in rows]
    
    def get_all_resources(self) -> List[Dict]:
        """Get all resources with reel info"""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT r.*, reels.url as reel_url, reels.author_username, reels.caption
                FROM resources r
                JOIN reels ON r.reel_id = reels.id
                ORDER BY r.extracted_at DESC
            """).fetchall()
            return [dict(row) for row in rows]
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with self._get_connection() as conn:
            stats = {}
            
            # Reel counts
            row = conn.execute(
                "SELECT COUNT(*) as total FROM reels"
            ).fetchone()
            stats['total_reels'] = row['total']
            
            # Processed count
            row = conn.execute(
                "SELECT COUNT(*) as processed FROM reels WHERE processed = TRUE"
            ).fetchone()
            stats['processed_reels'] = row['processed']
            stats['pending_reels'] = stats['total_reels'] - stats['processed_reels']
            
            # Resource counts
            row = conn.execute(
                "SELECT COUNT(*) as total FROM resources"
            ).fetchone()
            stats['total_resources'] = row['total']
            
            # Resource types breakdown
            rows = conn.execute("""
                SELECT resource_type, COUNT(*) as count 
                FROM resources 
                GROUP BY resource_type
                ORDER BY count DESC
            """).fetchall()
            stats['resource_types'] = {row['resource_type']: row['count'] for row in rows}
            
            return stats
    
    def get_recent_resources(self, limit: int = 20) -> List[Dict]:
        """Get recently extracted resources"""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT r.*, reels.url as reel_url, reels.author_username
                FROM resources r
                JOIN reels ON r.reel_id = reels.id
                ORDER BY r.extracted_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [dict(row) for row in rows]
