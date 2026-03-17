"""
Content Analyzer for Instagram Reels
Processes extracted content to identify resources, summarize, and categorize.
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ResourceMention:
    """Represents a resource mentioned in content"""
    resource_type: str
    title: str
    description: str
    confidence: float
    context: str
    urls: List[str]
    action_required: str  # "click_link", "dm_author", "comment", "bio_check"
    priority: int = 1  # 1-5, higher = more important


class ResourceExtractor:
    """Extracts document/resource mentions from reel content"""
    
    RESOURCE_TYPES = {
        'document': ['pdf', 'doc', 'document', 'file', 'spreadsheet'],
        'template': ['template', 'format', 'blueprint'],
        'guide': ['guide', 'tutorial', 'how-to', 'roadmap'],
        'checklist': ['checklist', 'list', 'steps'],
        'tool': ['tool', 'software', 'app', 'platform'],
        'course': ['course', 'class', 'lesson', 'training'],
        'ebook': ['ebook', 'book', 'e-book', 'pdf book'],
        'link': ['link', 'url', 'website', 'bio'],
    }
    
    ACTION_KEYWORDS = {
        'click_link': ['link in bio', 'link below', 'click the link', 'swipe up'],
        'dm_author': ['dm me', 'message me', 'inbox me', 'send dm'],
        'comment': ['comment below', 'drop a comment', 'type in comments'],
        'follow': ['follow for', 'follow me', 'follow page'],
        'save_post': ['save this', 'bookmark this', 'save for later'],
    }
    
    def __init__(self, language: str = "mixed"):
        self.language = language  # "en", "hi", "mixed"
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for resource extraction"""
        self.patterns = {
            # URL extraction
            'url': re.compile(r'https?://[^\s<>"\'|]+'),
            
            # Resource mentions with context
            'resource_mention': re.compile(
                r'(?i)(?:free\s+)?(\w+)\s*(?:download|get|grab|access|template|guide|checklist)',
                re.IGNORECASE
            ),
            
            # Link indicators
            'link_in_bio': re.compile(r'(?i)link\s+(?:in|on|at)\s+(?:bio|profile)', re.IGNORECASE),
            
            # DM indicators
            'dm_request': re.compile(
                r'(?i)(?:dm|message|inbox)\s+(?:me|us|for|me\s+"[^"]+")',
                re.IGNORECASE
            ),
            
            # Comment indicators
            'comment_request': re.compile(
                r'(?i)(?:comment|type)\s+(?:"[^"]+"|\'[^']+\')\s+(?:below|to get|for)',
                re.IGNORECASE
            ),
            
            # Hindi patterns
            'hindi_link': re.compile(r'(?i)(?:लिंक|link)\s+(?:बायो|bio)\s+(?:में|in|mein)'),
            'hindi_download': re.compile(r'(?i)(?:डाउनलोड|download|pdf|पीडीएफ)'),
            
            # File types
            'file_type': re.compile(
                r'(?i)(\.pdf|\.docx?|\.xlsx?|\.pptx?|pdf|document|excel|word)',
                re.IGNORECASE
            ),
        }
    
    def extract_resources(self, caption: str, video_transcript: str = "") -> List[ResourceMention]:
        """Extract all resources mentioned in the content"""
        resources = []
        full_text = f"{caption}\n{video_transcript}"
        
        # Extract URLs first
        urls = self.patterns['url'].findall(full_text)
        
        # Analyze text for resource mentions
        paragraphs = full_text.split('\n')
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            resource = self._analyze_paragraph(para, urls)
            if resource:
                resources.append(resource)
        
        # Find specific patterns
        resources.extend(self._extract_link_in_bio(full_text, urls))
        resources.extend(self._extract_dm_resources(full_text))
        resources.extend(self._extract_comment_resources(full_text))
        
        return resources
    
    def _analyze_paragraph(self, text: str, urls: List[str]) -> Optional[ResourceMention]:
        """Analyze a paragraph for resource content"""
        text_lower = text.lower()
        
        # Check for resource type keywords
        detected_type = None
        for res_type, keywords in self.RESOURCE_TYPES.items():
            if any(kw in text_lower for kw in keywords):
                detected_type = res_type
                break
        
        if not detected_type:
            return None
        
        # Determine action required
        action = self._determine_action(text_lower)
        
        # Extract title (first sentence or important phrase)
        title = self._extract_title(text)
        
        # Calculate confidence
        confidence = self._calculate_confidence(text, detected_type, len(urls) > 0)
        
        return ResourceMention(
            resource_type=detected_type,
            title=title,
            description=text[:200],
            confidence=confidence,
            context=text,
            urls=urls[:5],  # Limit to 5 URLs
            action_required=action
        )
    
    def _extract_title(self, text: str) -> str:
        """Extract a resource title from text"""
        # Try first sentence
        sentences = text.split('.')
        if sentences:
            title = sentences[0][:100].strip()
            return title
        return text[:100]
    
    def _determine_action(self, text_lower: str) -> str:
        """Determine what action is needed to access the resource"""
        for action, keywords in self.ACTION_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return action
        return "check_bio"  # Default
    
    def _calculate_confidence(self, text: str, res_type: str, has_url: bool) -> float:
        """Calculate confidence score for resource detection"""
        confidence = 0.5  # Base confidence
        
        text_lower = text.lower()
        
        # Boost for clear indicators
        if has_url:
            confidence += 0.2
        if 'free' in text_lower:
            confidence += 0.15
        if 'download' in text_lower:
            confidence += 0.1
        if res_type in ['pdf', 'template', 'guide']:
            confidence += 0.1
        
        # Penalize for uncertainty
        if 'maybe' in text_lower or 'might' in text_lower:
            confidence -= 0.1
        
        return min(confidence, 1.0)
    
    def _extract_link_in_bio(self, text: str, urls: List[str]) -> List[ResourceMention]:
        """Extract resources mentioned as "link in bio""""
        resources = []
        
        matches = self.patterns['link_in_bio'].finditer(text)
        for match in matches:
            context = text[max(0, match.start()-100):match.end()+100]
            
            resources.append(ResourceMention(
                resource_type='bio_link',
                title='Link in Bio',
                description='Resource available via profile bio link',
                confidence=0.9,
                context=context,
                urls=urls[:3],
                action_required='check_bio',
                priority=4
            ))
        
        return resources
    
    def _extract_dm_resources(self, text: str) -> List[ResourceMention]:
        """Extract resources requiring DM to access"""
        resources = []
        text_lower = text.lower()
        
        if self.patterns['dm