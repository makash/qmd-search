# qmd-unified

Minimal exporters and a deployment playbook for indexing local AI session logs with [QMD](https://github.com/tobi/qmd).

Current scope:
- **Codex JSONL -> Markdown** exporter
- **Pi JSONL -> Markdown** exporter
- playbook for:
  - exporting sessions on a laptop
  - installing Node + QMD on Olares with `mise`
  - syncing markdown to Olares
  - indexing and querying with QMD

For **Claude Code**, this repo currently recommends using the existing external exporter:
- `uvx claude-code-log@latest`

## Repo contents

- `scripts/exporters/codex_jsonl_to_md.py`
- `scripts/exporters/pi_jsonl_to_md.py`
- `docs/PLAYBOOK.md`

## Quick start

### Codex
```bash
python3 scripts/exporters/codex_jsonl_to_md.py \
  ~/.codex/sessions/2026/04/01/rollout-...jsonl \
  ~/qmd-sessions/main-laptop/codex/sample.md
```

### Pi
```bash
python3 scripts/exporters/pi_jsonl_to_md.py \
  ~/.pi/agent/sessions/.../2026-04-01T13-03-34-227Z_....jsonl \
  ~/qmd-sessions/main-laptop/pi/sample.md
```

### Claude Code
```bash
uvx claude-code-log@latest \
  ~/.claude/projects/<project>/<session>.jsonl \
  -f md \
  -o ~/qmd-sessions/main-laptop/claude-code/sample.md
```

Then follow `docs/PLAYBOOK.md`.

## Notes

- QMD can index raw JSONL, but Markdown works better.
- The current Codex and Pi exporters are intentionally small first-pass converters.
- Claude Code main-session files are the best first source. Excluding `subagents/` initially is recommended.
