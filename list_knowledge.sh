#!/bin/bash
# Lists all knowledge files with first line as description
echo "=== AutoMSP Knowledge Base ==="
echo ""
for agent_dir in /root/clawd/agents/*/; do
    agent=$(basename "$agent_dir")
    knowledge_dir="$agent_dir/knowledge"
    if [ -d "$knowledge_dir" ]; then
        files=$(ls "$knowledge_dir"/*.md 2>/dev/null)
        if [ -n "$files" ]; then
            echo "🤖 $agent"
            for f in "$knowledge_dir"/*.md; do
                [ -f "$f" ] || continue
                lines=$(wc -l < "$f")
                first=$(head -1 "$f" | sed 's/# //')
                echo "   📄 $(basename $f) ($lines lines) — $first"
            done
            echo ""
        fi
    fi
done
