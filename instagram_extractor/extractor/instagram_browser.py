"""
Instagram Browser Extractor
Uses browser automation to access Instagram saved content and extract data.
"""

import json
import time
import re
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, parse_qs

@dataclass
class ExtractedReel:
    """Raw extracted data from Instagram"""
    instagram_id: str
    url: str
    shortcode: str
    caption: str
    author_username: str
    author_full_name: str
    likes: int
    comments: int
    shares: int
    views: int
    is_video: bool
    video_duration: int
    display_url: str
    thumbnail_url: str
    saved_date: Optional[str] = None
    mentioned_resources: List[Dict] = None
    
    def __post_init__(self):
        if self.mentioned_resources is None:
            self.mentioned_resources = []


class InstagramBrowserExtractor:
    """Extracts content from Instagram using browser automation"""
    
    # Instagram URLs
    BASE_URL = "https://www.instagram.com"
    SAVED_URL = "https://www.instagram.com/your_activity/interactions/save"
    
    def __init__(self):
        self.current_user = None
        self.is_authenticated = False
        
    def _extract_shortcode_from_url(self, url: str) -> Optional[str]:
        """Extract post shortcode from Instagram URL"""
        patterns = [
            r'/reel/([A-Za-z0-9_-]+)',
            r'/p/([A-Za-z0-9_-]+)',
            r'/reels/([A-Za-z0-9_-]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def extract_resources_from_text(self, text: str) -> List[Dict]:
        """
        Extract mentioned resources from caption/text.
        Handles both English and Hindi content.
        """
        resources = []
        
        # URL patterns (links to docs, drives, etc.)
        url_pattern = r'(https?://[^\s]+)'
        urls = re.findall(url_pattern, text)
        for url in urls:
            resource = self._classify_url(url)
            if resource:
                resources.append(resource)
        
        # Document/resource mentions (English and Hindi patterns)
        resource_patterns = [
            # Generic patterns
            (r'link\s+(?:in|is)\s+(?:bio|description)[\s:]*([^\n]+)', 'bio_link'),
            (r'download\s+(?:from|at)\s*:?\s*([^\n]+)', 'download'),
            (r'pdf\s*:?\s*([^\n]{2,50})', 'pdf'),
            (r'free\s+template\s*:?\s*([^\n]+)', 'template'),
            (r'free\s+guide\s*:?\s*([^\n]+)', 'guide'),
            (r'free\s+checklist\s*:?\s*([^\n]+)', 'checklist'),
            
            # Hindi patterns (romanized and devanagari)
            (r'(?:link|लिंक)\s+(?:bio|बायो)\s+(?:में|mein)', 'bio_link'),
            (r'(?:pdf|पीडीएफ)\s+(?:download|डाउनलोड)', 'pdf'),
            (r'(?:template|टेम्पलेट|template)', 'template'),
            (r'(?:guide|गाइड)', 'guide'),
            (r'(?:checklist|चेकलिस्ट)', 'checklist'),
            
            # Specific platform mentions
            (r'drive\.google\.com/[^\s]+', 'google_drive'),
            (r'notion\.so/[^\s]+', 'notion'),
            (r'canva\.com/[^\s]+', 'canva'),
            (r'figma\.com/[^\s]+', 'figma'),
            (r'telegram\.me/[^\s]+', 'telegram'),
            (r'whats\s*app[^\s]*\s*(?:group|channel)?\s*:?\s*([^\n]+)', 'whatsapp'),
            
            # Email captures for resources
            (r'(?:DM|message|email)\s+(?:me|for)\s+(?:the|this)?\s*([^\n]{2,30})', 'dm_access'),
            (r'comment\s+(?:"[^"]*"|\'[^\']*\')\s+(?:to|for)\s+([^\n]+)', 'comment_access'),
        ]
        
        for pattern, resource_type in resource_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                resources.append({
                    'type': resource_type,
                    'raw_text': match if isinstance(match, str) else ' '.join(match),
                    'context': self._extract_context(text, match)
                })
        
        return resources
    
    def _classify_url(self, url: str) -> Optional[Dict]:
        """Classify a URL by type and purpose"""
        url_lower = url.lower()
        
        if 'drive.google.com' in url_lower:
            return {'type': 'google_drive', 'url': url, 'name': 'Google Drive'}
        elif 'dropbox.com' in url_lower:
            return {'type': 'dropbox', 'url': url, 'name': 'Dropbox'}
        elif 'notion.so' in url_lower:
            return {'type': 'notion', 'url': url, 'name': 'Notion'}
        elif 'canva.com' in url_lower:
            return {'type': 'canva', 'url': url, 'name': 'Canva'}
        elif 'figma.com' in url_lower:
            return {'type': 'figma', 'url': url, 'name': 'Figma'}
        elif 'telegram.me' in url_lower or 't.me' in url_lower:
            return {'type': 'telegram', 'url': url, 'name': 'Telegram'}
        elif 'discord.gg' in url_lower or 'discord.com' in url_lower:
            return {'type': 'discord', 'url': url, 'name': 'Discord'}
        elif any(doc in url_lower for doc in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']):
            return {'type': 'document_link', 'url': url, 'name': 'Document'}
        else:
            return {'type': 'external_link', 'url': url, 'name': 'External Link'}
    
    def _extract_context(self, text: str, match) -> str:
        """Extract surrounding context for a match"""
        match_str = match if isinstance(match, str) else ' '.join(match)
        index = text.find(match_str)
        if index == -1:
            return ""
        start = max(0, index - 100)
        end = min(len(text), index + len(match_str) + 100)
        return text[start:end].strip()
    
    def parse_instagram_page_structure(self, html_content: str) -> Dict:
        """
        Parse Instagram page structure to extract reel data.
        This is used when we get the page source.
        """
        reels = []
        
        # Look for embedded JSON data (Instagram stores data in script tags)
        json_patterns = [
            r'<script[^>]*>window\._sharedData\s*=\s*({.+?});</script>',
            r'<script[^>]*>window\.__initialDataLoaded\s*=\s*({.+?});</script>',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    # Parse based on Instagram's data structure
                    if 'entry_data' in data:
                        reels.extend(self._parse_entry_data(data['entry_data']))
                    elif 'graphql' in str(data):
                        reels.extend(self._parse_graphql_data(data))
                except json.JSONDecodeError:
                    continue
        
        return {'reels': reels, 'count': len(reels)}
    
    def _parse_entry_data(self, entry_data: Dict) -> List[Dict]:
        """Parse Instagram entry data structure"""
        reels = []
        # Implementation depends on exact Instagram structure
        # This is a placeholder for the parsing logic
        return reels
    
    def _parse_graphql_data(self, data: Dict) -> List[Dict]:
        """Parse Instagram GraphQL response structure"""
        reels = []
        # Implementation depends on exact GraphQL structure
        return reels
    
    def extract_reel_from_html(self, url: str, html_content: str) -> Optional[ExtractedReel]:
        """Extract reel data from Instagram HTML page"""
        shortcode = self._extract_shortcode