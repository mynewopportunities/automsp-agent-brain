"""
Configuration for Instagram Content Extractor
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class InstagramConfig:
    """Configuration for Instagram extraction"""
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent
    DATA_DIR: Path = BASE_DIR / "data"
    DOWNLOADS_DIR: Path = BASE_DIR / "downloads"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # Database
    DB_PATH: Path = DATA_DIR / "instagram_content.db"
    
    # Instagram Settings
    REQUEST_DELAY: float = 2.0  # Seconds between requests
    MAX_RETRIES: int = 3
    TIMEOUT: int = 30
    
    # Browser Settings
    HEADLESS: bool = False
    WINDOW_WIDTH: int = 1920
    WINDOW_HEIGHT: int = 1080
    
    # Content Processing
    MIN_CONFIDENCE: float = 0.5
    MAX_RESOURCES_PER_REEL: int = 20
    
    # Export Settings
    DEFAULT_EXPORT_FORMAT: str = "json"
    
    def __post_init__(self):
        # Create directories
        for dir_path in [self.DATA_DIR, self.DOWNLOADS_DIR, self.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Load from environment
        self.INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME', '')
        self.INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD', '')
        self.SESSION_FILE = os.getenv('INSTAGRAM_SESSION', str(self.DATA_DIR / 'session.json'))


CONFIG = InstagramConfig()
