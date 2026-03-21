-- Personal CRM Database Schema
-- SQLite with WAL mode recommended

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Contact discovery patterns (learned skip patterns)
CREATE TABLE skip_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL UNIQUE,
    pattern_type TEXT NOT NULL CHECK (pattern_type IN ('domain', 'email_prefix', 'subject_keyword', 'sender_name')),
    confidence REAL DEFAULT 0.0,
    manual_add INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Auto-add mode setting
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO settings (key, value) VALUES 
    ('auto_add_mode', 'false'),
    ('decision_threshold', '50'),
    ('last_sync', '1970-01-01');

-- Contacts table
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE NOT NULL,
    company TEXT,
    role TEXT,
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    relationship_score REAL DEFAULT 50.0 CHECK (relationship_score >= 0 AND relationship_score <= 100),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'auto_filtered')),
    discovered_via TEXT CHECK (discovered_via IN ('email', 'calendar', 'manual', 'auto')),
    discovery_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    first_interaction TIMESTAMP,
    last_interaction TIMESTAMP,
    metadata TEXT, -- JSON: {source_domain, email_count, meeting_count, etc.}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interactions (emails, meetings, calls)
CREATE TABLE interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('email', 'meeting', 'call', 'text', 'other')),
    direction TEXT CHECK (direction IN ('incoming', 'outgoing', 'bidirectional')),
    title TEXT,
    content_preview TEXT, -- First 500 chars
    external_id TEXT, -- Gmail message ID, calendar event ID, etc.
    source_url TEXT,
    metadata TEXT, -- JSON: thread_id, attendees, etc.
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
);

-- Follow-ups and reminders
CREATE TABLE follow_ups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    due_date TIMESTAMP NOT NULL,
    snoozed_until TIMESTAMP,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled', 'snoozed')),
    priority INTEGER DEFAULT 3,
    source_interaction_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
    FOREIGN KEY (source_interaction_id) REFERENCES interactions(id)
);

-- Contact context entries with vector embeddings
CREATE TABLE contact_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    entry_type TEXT NOT NULL CHECK (entry_type IN ('interaction_summary', 'meeting_note', 'email_summary', 'manual_note', 'insight', 'topic')),
    content TEXT NOT NULL,
    embedding BLOB, -- 768-dimensional float vector stored as bytes
    source TEXT, -- Reference to source interaction or manual entry
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
);

-- LLM-generated relationship summaries
CREATE TABLE contact_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL UNIQUE,
    relationship_summary TEXT,
    communication_style TEXT, -- JSON: {formality: "casual", brevity: "concise", tone: "friendly"}
    key_topics TEXT, -- JSON array
    last_meeting_summary TEXT,
    next_suggested_action TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
);

-- Meeting records (synced from meeting recorder)
CREATE TABLE meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE, -- From meeting recorder
    title TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    transcript TEXT,
    summary TEXT,
    meeting_type TEXT CHECK (meeting_type IN ('video', 'audio', 'in_person', 'hybrid')),
    platform TEXT, -- zoom, meet, teams, etc.
    recording_url TEXT,
    organizer_id INTEGER,
    metadata TEXT, -- JSON: attendees list with emails, recording duration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organizer_id) REFERENCES contacts(id)
);

-- Meeting to contact mapping (many-to-many)
CREATE TABLE meeting_attendees (
    meeting_id INTEGER NOT NULL,
    contact_id INTEGER NOT NULL,
    attended INTEGER DEFAULT 1, -- Boolean: actually attended
    response_status TEXT CHECK (response_status IN ('accepted', 'tentative', 'declined', 'needs_action')),
    PRIMARY KEY (meeting_id, contact_id),
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
);

-- Action items extracted from meetings
CREATE TABLE meeting_action_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL,
    contact_id INTEGER, -- Assignee
    description TEXT NOT NULL,
    owner_is_user INTEGER DEFAULT 0, -- 1 if user owns this action item
    external_task_link TEXT, -- Link to todoist/asana/notion
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'completed', 'cancelled')),
    due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

-- Company news/high-signal items
CREATE TABLE company_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    headline TEXT NOT NULL,
    summary TEXT,
    source TEXT,
    url TEXT,
    published_at TIMESTAMP,
    relevance_score REAL DEFAULT 0.0, -- 0-100
    user_notified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Discovery decisions log (for learning)
CREATE TABLE discovery_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_email TEXT NOT NULL,
    candidate_name TEXT,
    candidate_company TEXT,
    source_type TEXT NOT NULL CHECK (source_type IN ('email', 'calendar')),
    source_preview TEXT, -- Email subject or meeting title
    pattern_matches TEXT, -- JSON: which patterns matched
    decision TEXT NOT NULL CHECK (decision IN ('approved', 'rejected', 'auto_approved')),
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email drafts
CREATE TABLE email_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    thread_id TEXT, -- Gmail thread ID
    subject TEXT,
    proposed_body TEXT,
    proposed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'proposed' CHECK (status IN ('proposed', 'approved', 'rejected', 'drafted')),
    approved_at TIMESTAMP,
    external_draft_id TEXT, -- Gmail draft ID after creation
    model_context TEXT, -- JSON: what context was fed to LLM
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

-- Intent query log (for improving NLP)
CREATE TABLE query_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_query TEXT NOT NULL,
    detected_intent TEXT NOT NULL,
    confidence REAL,
    parameters TEXT, -- JSON: extracted entities
    successful INTEGER, -- Whether user was satisfied
