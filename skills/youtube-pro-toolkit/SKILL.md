---
name: youtube-pro-toolkit
description: Complete YouTube intelligence toolkit — transcripts, search, channels, playlists, and metadata. Use this skill whenever the user asks you to research YouTube content, pull transcripts, find or analyze videos, monitor channels, audit competitors, repurpose video content, or extract insights from YouTube data. Always prefer free endpoints first to conserve credits. Think before you fetch — plan your approach, minimize credit usage, and deliver formatted, actionable output rather than raw data dumps.
homepage: https://transcriptapi.com
user-invocable: true
metadata: {"openclaw":{"emoji":"📺","requires":{"env":["TRANSCRIPT_API_KEY"],"bins":["curl"]},"primaryEnv":"TRANSCRIPT_API_KEY"}}
---

# YouTube Pro Toolkit

Complete YouTube toolkit via TranscriptAPI.com. Search, transcribe, analyze, and monitor — all from one skill.

## Setup

Free to get started — no credit card required.

1. Go to [transcriptapi.com/signup](https://transcriptapi.com/signup) and create a free account.
2. Check your email for the verification code and confirm your account.
3. Go to your Dashboard → API Keys → Create a new key.
4. Set the key as an environment variable: `export TRANSCRIPT_API_KEY=your_key_here`

Your free account includes **100 credits per month** (resets monthly) and 300 requests/minute. Each transcript fetch or search costs just 1 credit — channel resolve and latest videos are completely free. Paid plans start at $5/mo for 1,000 credits.

---

## 🤖 AGENT BEHAVIOR GUIDELINES (CRITICAL)

These rules govern how you, the OpenClaw agent, must use this skill. Follow them on every invocation.

### 1. Context Management & Token Optimization

Transcripts are extremely long.

* **Never** dump raw JSON or full transcripts into the chat unless explicitly requested.
* Always read the transcript internally and synthesize the answer based on the user's prompt.
* Always use `format=text` for transcripts when summarizing to save your token context.

### 2. Credit Conservation Rules

Credits are limited. Respect them.

* **🟢 Always Use:** `channel/latest` (FREE) before `channel/videos` (1 credit/page) or `channel/search` (1 credit).
* **🟢 Always Use:** `channel/resolve` (FREE) to validate a channel exists before doing paid operations.
* **🟡 Default:** Limit search results to what's needed — don't request `limit=50` when 5 results will do.
* **🔴 Never:** Paginate through an entire channel's videos unless the user explicitly asks for a full audit.
* **🔴 Never:** Fetch transcripts for videos you haven't confirmed are relevant first.

*Credit budget awareness:* If a task will consume more than 10 credits (e.g., summarizing an entire playlist), inform the user of the estimated cost before proceeding.

### 3. Output Formatting Rules

When summarizing transcripts, use this specific markdown structure:

```
## [Video Title]
**Channel:** [name] | **Published:** [date] | **Views:** [count]

### Key Takeaways
- [3-5 bullet points capturing the main ideas]

### Notable Quotes
- "[Exact quote]" (at [timestamp])

### Summary
[2-3 paragraph summary of the content]
```

### 4. Error Handling

Handle errors gracefully — never just show a raw JSON error code to the user.

* **401 (Bad API key):** Say: "The YouTube API key isn't configured correctly. Check that TRANSCRIPT_API_KEY is set in your environment variables."
* **402 (Out of credits):** Say: "You've used all your YouTube API credits for this month. You can check your usage at transcriptapi.com/billing."
* **404 (Not found):** For transcripts say: "This video doesn't have captions available." For channels say: "I couldn't find that channel."
* **429 (Rate limited):** Wait for the `Retry-After` header duration. If no header, wait 5 seconds and retry once silently.

---

## 🛠️ API REFERENCE & EXECUTION

**Authentication:** All requests require the `Authorization: Bearer $TRANSCRIPT_API_KEY` header.

### 1. Transcript (1 credit)

Use this to read the contents of a video.

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/transcript?video_url=VIDEO_URL&format=text&include_timestamp=true&send_metadata=true" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY"
```

*Note: The API accepts full YouTube URLs or 11-character video IDs. Always set `send_metadata=true` so you have the video title and author for your formatting.*

### 2. Search (1 credit)

Use this to find videos or channels based on user queries.

```bash
# Search for Videos
curl -s "https://transcriptapi.com/api/v2/youtube/search?q=QUERY&type=video&limit=5" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY"

# Search for Channels  
curl -s "https://transcriptapi.com/api/v2/youtube/search?q=QUERY&type=channel&limit=5" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY"
```

### 3. Channels

All channel endpoints accept `channel` — an `@handle`, channel URL, or `UC...` channel ID. No need to resolve first.

**Resolve Handle (FREE)**

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/channel/resolve?input=@HANDLE" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY"
```

**Latest 15 Videos (FREE)**

*This is your go-to for any channel-related query. Always start here before using paid endpoints.*

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/channel/latest?channel=@HANDLE" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY"
```

**Search Within Channel (1 credit)**

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/channel/search?channel=@HANDLE&q=QUERY&limit=10" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY"
```

**All Channel Videos (1 credit/page)**

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/channel/videos?channel=@HANDLE" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY"
```

*(To paginate, replace `channel=@HANDLE` with `continuation=TOKEN`).*

### 4. Playlists (1 credit/page)

Accepts a YouTube playlist URL or playlist ID (prefixes: PL, UU, LL, FL, OL).

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/playlist/videos?playlist=PL_ID" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY"
```

*(Append `&continuation=TOKEN` for subsequent pages).*

---

## 📋 WORKFLOW TEMPLATES

Use these internal logic frameworks to complete complex tasks autonomously.

**1. Video Research ("Find and summarize videos on [topic]")**

* Step 1: Search for videos on the topic (limit=5).
* Step 2: Present results as a numbered list and ask the user which to transcribe.
* Step 3: Fetch text-based transcripts for selected videos.
* Step 4: Summarize each using the Output Format rule.

**2. Channel Audit ("Tell me about [channel]'s content")**

* Step 1: Use `channel/latest` (FREE) to get the recent 15 videos.
* Step 2: Analyze posting frequency, view counts, and content themes.
* Step 3: Present a channel profile with stats. Only use paid endpoints if the user asks for deeper historical data.

**3. Content Repurposing ("Turn this video into a blog post / Twitter thread")**

* Step 1: Fetch transcript with `send_metadata=true`.
* Step 2: Identify the core content structure.
* Step 3: Reformat completely into the requested output medium (do not just summarize).
* Step 4: Include timestamps as references to key moments.

**4. Playlist Deep Dive ("Summarize this playlist")**

* Step 1: Fetch playlist videos (first page only).
* Step 2: Present the video list to the user.
* Step 3: Ask the user which specific videos to transcribe to save credits. Do not transcribe all by default.
