# TOOLS.md - Local Notes

Skills define *how* tools work. This file is for *your* specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:
- Camera names and locations
- SSH hosts and aliases  
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras
- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH
- home-server → 192.168.1.100, user: admin

### TTS
- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.


## Task Accountability Board
- Notion DB ID: `32526c87-996c-818a-b9f2-ebd12c4743db`
- URL: https://www.notion.so/32526c87996c818ab9f2ebd12c4743db
- MANDATORY: Log every task you receive with status updates
- Set status to ✅ Done with output path when complete
- Set status to ❌ Failed with reason if you cannot complete
- n8n monitors every 5 min and escalates overdue tasks to Jarvis

## Shell Tools (use via exec)
- **log_task.sh**: Log a task to Notion Task Board
  Usage: `bash /root/clawd/log_task.sh "Task" "AGENT" "Expected Output" "Path" "🔴 High"`
- **notion_query.sh**: Query any Notion database
  Usage: `bash /root/clawd/notion_query.sh "DB_ID" '{"filter":{}}'`
