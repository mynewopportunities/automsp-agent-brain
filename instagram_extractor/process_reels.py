import json
import os

# Path to the JSON file
json_path = '/root/clawd/instagram_extractor/apify_results_with_cookies.json'
memory_dir = '/root/clawd/memory'

# Define mapping of keywords to agent identifiers
agent_keywords = {
    'spark': ['ai', 'automation', 'machine learning', 'deep learning', 'neural network', 'artificial intelligence'],
    'proof': ['sales', 'outreach', 'pitch', 'conversion', 'demo', 'client meeting'],
    'herald': ['linkedin', 'linkedin post', 'linkedin article', 'linkedin carousel'],
    'trace': ['market research', 'industry analysis', 'trend', 'insight', 'analysis'],
    'robin': ['lead gen', 'lead generation', 'qualify', 'prospect', 'lead capture'],
    'analyst': ['seo', 'search engine optimization', 'keyword', 'backlink', 'search ranking']
}

# Helper to determine the best agent for an item based on keywords
def assign_agent(caption):
    lower = caption.lower()
    for agent, keywords in agent_keywords.items():
        if any(kw in lower for kw in keywords):
            return agent
    return None

# Prepare a dict to hold items per agent
agent_items = {agent: [] for agent in agent_keywords}

# Load JSON data
try:
    with open(json_path, 'r') as f:
        data = json.load(f)
except Exception as e:
    print(f'Error reading JSON: {e}')
    exit(1)

# Process each entry; assume each entry has a 'caption' field
if isinstance(data, dict) and 'items' in data:
    # Some Apify outputs wrap items in an 'items' key
    entries = data['items']
else:
    entries = data

for entry in entries:
    # Try to get caption; fallback to any string fields
    caption = entry.get('caption') or entry.get('description') or ''
    agent = assign_agent(caption)
    if agent:
        agent_items[agent].append(entry)

# Ensure memory directory exists
os.makedirs(memory_dir, exist_ok=True)

# Write summary files for each agent
for agent, items in agent_items.items():
    summary_path = os.path.join(memory_dir, f'{agent}-intel.md')
    with open(summary_path, 'w') as f:
        f.write(f'# {agent.upper()} INTEL SUMMARY\n\n')
        if items:
            # Collect distinct insights: we can take unique words from captions
            insight_lines = []
            seen = set()
            for item in items:
                caption = item.get('caption', '') or ''
                for line in caption.split('.'):
                    line = line.strip()
                    if line and line not in seen:
                        seen.add(line)
                        insight_lines.append(line)
            f.write('## Key Insights\n\n')
            insights = '\n'.join(insight_lines[:50])  # Limit to first 50 insights
            f.write(insights)
            if len(insight_lines) > 50:
                f.write('\n... (truncated)')
        else:
            f.write('No relevant reels assigned yet.')
    print(f'Written intel summary for {agent} to {summary_path}')