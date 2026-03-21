#!/bin/bash
# Usage: search_knowledge.sh "search term"
# Searches all agent knowledge files for a term
QUERY="${1:-""}"
echo "=== Knowledge Base Search: '$QUERY' ==="
echo ""
find /root/clawd/agents -name "*.md" | while read f; do
    if grep -qi "$QUERY" "$f" 2>/dev/null; then
        echo "📄 $f"
        grep -i "$QUERY" "$f" | head -3
        echo "---"
    fi
done
