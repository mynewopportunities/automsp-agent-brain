-- Instagram Content Extraction Database Schema
-- Stores extracted content, resources, and metadata from saved reels

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Main table for extracted reels
CREATE TABLE IF NOT EXISTS reels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instagram_id TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL,
    caption TEXT,
    author_username TEXT,
    author_full_name TEXT,
    content_text TEXT, -- Extracted/transcribed content in English
    content_hindi TEXT, -- Original Hindi content if extracted
    summary TEXT, -- AI-generated summary
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    saved_at TIMESTAMP,
    media_type TEXT DEFAULT 'reel',
    duration INTEGER, -- in seconds
    view_count INTEGER,
    like_count INTEGER,
    share_count INTEGER,
    processed BOOLEAN DEFAULT FALSE,
    processing_status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
    error_message TEXT,
    tags TEXT -- JSON array of extracted tags
);

-- Table for resources/documents mentioned in reels
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reel_id INTEGER NOT NULL,
    resource_type TEXT NOT NULL, -- document, link, book, tool, template, course, etc.
    title TEXT,
    description TEXT,
    url TEXT,
    file_path TEXT, -- Local path if downloaded
    source_mention TEXT, -- How it was mentioned in the reel (text snippet)
    timestamp_in_reel INTEGER, -- Seconds into reel where mentioned
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (reel_id) REFERENCES reels(id) ON DELETE CASCADE
);

-- Table for categorization/taxonomy
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    parent_id INTEGER,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);

-- Junction table for reel categories
CREATE TABLE IF NOT EXISTS reel_categories (
    reel_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    confidence_score REAL,
    PRIMARY KEY (reel_id, category_id),
    FOREIGN KEY (reel_id) REFERENCES reels(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- Table for searchable keywords extracted from content
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT UNIQUE NOT NULL
);

-- Junction table for reel keywords
CREATE TABLE IF NOT EXISTS reel_keywords (
    reel_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    frequency INTEGER DEFAULT 1,
    PRIMARY KEY (reel_id, keyword_id),
    FOREIGN KEY (reel_id) REFERENCES reels(id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
);

-- Table for tracking extraction jobs
CREATE TABLE IF NOT EXISTS extraction_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type TEXT NOT NULL, -- batch, single, sync
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    total_count INTEGER DEFAULT 0,
    processed_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running', -- running, completed, failed
    error_log TEXT
);

-- Table for user notes on resources
CREATE TABLE IF NOT EXISTS resource_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id INTEGER NOT NULL,
    note TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_reels_author ON reels(author_username);
CREATE INDEX IF NOT EXISTS idx_reels_processed ON reels(processed);
CREATE INDEX IF NOT EXISTS idx_reels_saved_at ON reels(saved_at);
CREATE INDEX IF NOT EXISTS idx_resources_type ON resources(resource_type);
CREATE INDEX IF NOT EXISTS idx_resources_reel ON resources(reel_id);
CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);

-- Views for common queries
CREATE VIEW IF NOT EXISTS v_reels_with_resources AS
SELECT 
    r.*,
    COUNT(DISTINCT res.id) as resource_count
FROM reels r
LEFT JOIN resources res ON r.id = res.reel_id
GROUP BY r.id;

CREATE VIEW IF NOT EXISTS v_resources_by_category AS
SELECT 
    c.name as category,
    res.resource_type,
    COUNT(*) as count,
    GROUP_CONCAT(DISTINCT res.title) as titles
FROM resources res
JOIN reels r ON res.reel_id = r.id
JOIN reel_categories rc ON r.id = rc.reel_id
JOIN categories c ON rc.category_id = c.id
GROUP BY c.name, res.resource_type
ORDER BY count DESC;
