# Playbook: laptop -> Olares -> QMD

This is the smallest working workflow we validated.

## Goal

Export local AI session logs as Markdown on the laptop, sync them to Olares, index them with QMD, and run searches.

Current sources:
- Claude Code
- Codex
- Pi

## 1. Local source paths

### Claude Code
```bash
~/.claude/projects
```

Recommended first pass:
- use **main session** `.jsonl` files
- skip `subagents/` initially

### Codex
```bash
~/.codex/sessions
```

### Pi
```bash
~/.pi/agent/sessions
```

## 2. Local export directory

Suggested layout:

```text
~/qmd-sessions/main-laptop/
  claude-code/
  codex/
  pi/
```

Create it:

```bash
mkdir -p ~/qmd-sessions/main-laptop/{claude-code,codex,pi}
```

## 3. Export Markdown on the laptop

### Claude Code -> Markdown

Use the existing Claude exporter:

```bash
uvx claude-code-log@latest \
  ~/.claude/projects/<project>/<session>.jsonl \
  -f md \
  -o ~/qmd-sessions/main-laptop/claude-code/<name>.md
```

Example:

```bash
uvx claude-code-log@latest \
  ~/.claude/projects/-Users-mainstreet-code-agent-infra-security/5157db64-bce7-4ef6-9d65-2084a42c4ef9.jsonl \
  -f md \
  -o ~/qmd-sessions/main-laptop/claude-code/agent-infra-security_5157db64.md
```

### Codex -> Markdown

```bash
python3 scripts/exporters/codex_jsonl_to_md.py \
  ~/.codex/sessions/2026/04/01/rollout-2026-04-01T18-09-44-019d490e-8e89-7c62-b395-041f9cee7ae0.jsonl \
  ~/qmd-sessions/main-laptop/codex/rollout-2026-04-01T18-09-44.md
```

### Pi -> Markdown

```bash
python3 scripts/exporters/pi_jsonl_to_md.py \
  ~/.pi/agent/sessions/--Users-mainstreet-code-syncing-resource-across-machines--/2026-04-01T13-03-34-227Z_9a0a267a-77c4-4220-bfe7-972846d33a6e.jsonl \
  ~/qmd-sessions/main-laptop/pi/2026-04-01T13-03-34.md
```

## 4. Install Node and QMD on Olares with mise

SSH in:

```bash
ssh -F ~/Documents/creds/config_ssh olares
```

Install `mise`:

```bash
curl -fsSL https://mise.run | sh
echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc
source ~/.bashrc
```

Install Node 22:

```bash
mise use -g node@22
mise install
node -v
npm -v
```

Install QMD:

```bash
npm install -g @tobilu/qmd
```

Pull models and verify GPU:

```bash
qmd pull
qmd status
```

What you want to see in `qmd status`:
- GPU detected
- offloading enabled
- VRAM shown

## 5. Sync exported markdown to Olares

Create target dir on Olares:

```bash
ssh -F ~/Documents/creds/config_ssh olares 'mkdir -p ~/qmd-sessions/main-laptop'
```

Push files from the laptop:

```bash
rsync -az --delete \
  -e "ssh -F $HOME/Documents/creds/config_ssh" \
  ~/qmd-sessions/main-laptop/ \
  olares:~/qmd-sessions/main-laptop/
```

## 6. Add the QMD collection on Olares

```bash
ssh -F ~/Documents/creds/config_ssh olares
```

Then:

```bash
qmd collection remove main-laptop-sessions || true
qmd collection add ~/qmd-sessions/main-laptop --name main-laptop-sessions --mask "**/*.md"
qmd context rm qmd://main-laptop-sessions || true
qmd context add qmd://main-laptop-sessions "Sessions exported from main laptop: Claude Code, Codex, and Pi"
```

## 7. Index and embed

```bash
qmd update
qmd embed
qmd status
```

## 8. Query examples

### Basic keyword search
```bash
qmd search "github open graph image" -c main-laptop-sessions -n 5
```

### Cross-machine/syncing topic
```bash
qmd search "syncing across laptop and two servers" -c main-laptop-sessions -n 5
```

### Feature walkthrough lookup
```bash
qmd search "remote control feature" -c main-laptop-sessions -n 5
```

### Better quality hybrid query
```bash
qmd query "how was the remote control feature implemented" -c main-laptop-sessions -n 5
```

### Fetch a specific doc
```bash
qmd get "qmd://main-laptop-sessions/path/to/file.md"
```

## 9. Current caveats

### Claude
- strongest current path
- existing exporter already works well

### Codex
- exporter works, but some sessions still contain prompt/instruction noise
- later improvement: strip more boilerplate and compact tool output better

### Pi
- exporter works, but tool results can still be noisy or long
- later improvement: better summarization of toolResult-heavy sessions

## 10. Validated result

The following was validated end-to-end:
- markdown exported on laptop
- synced to Olares
- QMD collection created
- files indexed and embedded
- real searches returned results from Claude, Codex, and Pi exports
