# qmd-search

qmd-search turns AI coding session logs from Claude Code, Codex, and Pi into searchable Markdown for QMD, with a practical playbook for syncing and indexing them on a remote GPU server.

Minimal exporters and a deployment playbook for indexing local AI session logs with [QMD](https://github.com/tobi/qmd).

Current scope:
- **Codex JSONL -> Markdown** exporter
- **Pi JSONL -> Markdown** exporter
- playbook for:
  - exporting sessions on a laptop
  - installing Node + QMD on a remote GPU server with `mise`
  - syncing markdown to a remote server
  - indexing and querying with QMD

For **Claude Code**, this repo currently recommends using the existing external exporter:
- `uvx claude-code-log@latest`

## Repo contents

- `scripts/exporters/codex_jsonl_to_md.py`
- `scripts/exporters/pi_jsonl_to_md.py`
- `docs/index-ai-coding-session-logs-with-qmd-on-a-remote-gpu-server.md`

## Quick start

### Codex
```bash
python3 scripts/exporters/codex_jsonl_to_md.py \
  ~/.codex/sessions/YYYY/MM/DD/rollout-<session-id>.jsonl \
  ~/qmd-sessions/main-laptop/codex/<session-id>.md
```

### Pi
```bash
python3 scripts/exporters/pi_jsonl_to_md.py \
  ~/.pi/agent/sessions/<encoded-cwd>/<timestamp>_<session-id>.jsonl \
  ~/qmd-sessions/main-laptop/pi/<session-id>.md
```

### Claude Code
```bash
uvx claude-code-log@latest \
  ~/.claude/projects/<encoded-project>/<session-id>.jsonl \
  -f md \
  -o ~/qmd-sessions/main-laptop/claude-code/<session-id>.md
```

Then follow `docs/index-ai-coding-session-logs-with-qmd-on-a-remote-gpu-server.md`.

## Notes

- QMD can index raw JSONL, but Markdown works better.
- The current Codex and Pi exporters are intentionally small first-pass converters.
- Claude Code main-session files are the best first source. Excluding `subagents/` initially is recommended.

## License

MIT
