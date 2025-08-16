# Claude Code Auto MCP Aliases
alias claude-auto-on='export CLAUDE_AUTO_MCP=true && echo "✅ Auto MCP enabled"'
alias claude-auto-off='export CLAUDE_AUTO_MCP=false && echo "❌ Auto MCP disabled"'
alias claude-auto-status='python3 /home/opsvi/master_root/.claude/test_auto_mcp.py'
alias claude-auto-config='${EDITOR:-vim} /home/opsvi/master_root/.claude/config.json'
alias claude-auto-logs='tail -f /tmp/claude_auto_mcp.log'
alias claude-auto-metrics='cat /tmp/claude_mcp_metrics.json | python3 -m json.tool'
alias claude-auto-activate='source /home/opsvi/master_root/.claude/activate_auto_mcp.sh'
