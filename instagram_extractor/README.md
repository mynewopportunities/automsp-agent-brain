# Instagram Content Extractor

A complete system for extracting, analyzing, and organizing content from Instagram saved reels. Handles both English and Hindi content, identifies resources/documents mentioned, and maintains a searchable database.

## Features

- **Database Storage**: SQLite database to store all extracted reels and resources
- **Bilingual Support**: Handles both English and Hindi content
- **Resource Detection**: Automatically identifies PDFs, templates, guides, tools, links, etc.
- **Search**: Query your extracted content by type, keyword, or author
- **Export**: Export resources in JSON or CSV format

## Directory Structure

```
instagram_extractor/
├── database/
│   ├── schema.sql         # Database schema
│   └── database_manager.py # Database operations
├── extractor/
│   └── instagram_browser.py  # Instagram content extraction
├── processors/
│   └── content_analyzer.py   # Content analysis and resource detection
├── data/                  # Database storage (gitignored)
├── downloads/             # Downloaded files
├── instagram_extractor.py # Main CLI
├── config.py             # Configuration
└── requirements.txt      # Python dependencies
```

## Installation

```bash
cd /root/clawd/instagram_extractor
pip install -r requirements.txt
```

## Usage

### 1. Add a Reel Manually

```bash
python instagram_extractor.py add-url "https://instagram.com/reel/ABC123" \
  --caption "Description of the reel" \
  --author "username" \
  --date "2024-01-15"
```

### 2. Process Pending Reels

```bash
# Process all unprocessed reels
python instagram_extractor.py process-all

# Process a specific reel
python instagram_extractor.py process <reel_id>
```

### 3. Search Resources

```bash
# Search for PDF templates
python instagram_extractor.py search "pdf template"

# Search by type
python instagram_extractor.py search --type "guide"
```

### 4. Generate Report

```bash
python instagram_extractor.py report
```

### 5. Export Data

```bash
# Export to JSON
python instagram_extractor.py export resources.json

# Export to CSV
python instagram_extractor.py export resources.csv --format csv
```

## How It Works

1. **Data Collection**: You provide Instagram reel URLs (manually or via browser automation)
2. **Storage**: Reels are stored in SQLite with metadata
3. **Analysis**: NLP/Regex extracts resources mentioned (PDFs, templates, links in bio, etc.)
4. **Categorization**: Resources typed by content (document, template, guide, tool, etc.)
5. **Action Tracking**: Notes how to access each resource (click link, DM author, check bio, etc.)
6. **Search**: Query by type, keyword, author, or access method

## Resource Types Detected

- **Documents**: PDFs, Word docs, spreadsheets
- **Templates**: Canva templates, Notion templates, Excel templates
- **Guides**: Step-by-step guides, tutorials, roadmaps
- **Tools**: Software, apps, platforms mentioned
- **Courses**: Online courses, training programs
- **Links**: Bio links, external websites
- **Telegram/Discord**: Community links
- **Social**: DM requests, comment-to-access

## Database Schema

### reels
- id, instagram_id, url, caption
- author_username, author_full_name
- content_text, content_hindi, summary
- view_count, like_count, save_count
- processed, processing_status

### resources
- id, reel_id, resource_type
- title, description, url
- file_path, source_mention
- action_required, verified

## Roadmap

- [ ] Instagram API integration for automated fetching
- [ ] Video transcription with Whisper
- [ ] Auto-download of mentioned resources
- [ ] Browser automation for link following
- [ ] Telegram bot for easy access
- [ ] Web dashboard for browsing

## Notes

- Currently operates on manually provided URLs
- Requires Instagram credentials for automated fetching (use with caution)
- Respects rate limits with built-in delays
- All data stored locally in SQLite
