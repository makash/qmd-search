#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Any


def summarize(text: str, limit: int = 80) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def truncate(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n\n[truncated {len(text) - limit} chars]"


def emit_block(lines: list[str], heading: str, body: str, fence: str | None = None) -> None:
    body = body.strip("\n")
    if not body:
        return
    lines.append(f"### {heading}")
    lines.append("")
    if fence:
        lines.append(f"```{fence}")
        lines.append(body)
        lines.append("```")
    else:
        lines.append(body)
    lines.append("")


def render_tool_call(payload: dict[str, Any]) -> tuple[str, str, str | None]:
    item_type = payload.get("type")
    if item_type == "function_call":
        body = {
            "name": payload.get("name"),
            "arguments": truncate(payload.get("arguments", "")),
            "call_id": payload.get("call_id"),
        }
        return (f"Tool Call: {payload.get('name', 'unknown')}", json.dumps(body, indent=2, ensure_ascii=False), "json")
    if item_type == "custom_tool_call":
        body = {
            "name": payload.get("name"),
            "status": payload.get("status"),
            "call_id": payload.get("call_id"),
            "input": truncate(payload.get("input", "")),
        }
        return (f"Custom Tool Call: {payload.get('name', 'unknown')}", json.dumps(body, indent=2, ensure_ascii=False), "json")
    body = {
        "status": payload.get("status"),
        "query": ((payload.get("action") or {}).get("query")),
        "queries": ((payload.get("action") or {}).get("queries")),
    }
    return ("Web Search Call", json.dumps(body, indent=2, ensure_ascii=False), "json")


def parse_file(path: Path) -> str:
    session_meta: dict[str, Any] = {}
    entries: list[dict[str, Any]] = []
    first_user_text = ""

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            obj = json.loads(raw_line)
            top_type = obj.get("type")
            payload = obj.get("payload", {})

            if top_type == "session_meta":
                session_meta = payload
                continue

            if top_type != "response_item":
                continue

            item_type = payload.get("type")
            role = payload.get("role")

            if item_type == "message":
                content = payload.get("content") or []
                blocks: list[tuple[str, str, str | None]] = []
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    kind = item.get("type")
                    if kind in {"input_text", "output_text"}:
                        text = item.get("text", "")
                        if role == "developer":
                            continue
                        stripped = text.lstrip()
                        if role == "user" and text and not stripped.startswith("<") and not stripped.startswith("# AGENTS.md instructions") and not first_user_text:
                            first_user_text = text
                        if stripped.startswith("<environment_context>") or stripped.startswith("<app-context>") or stripped.startswith("# AGENTS.md instructions"):
                            continue
                        blocks.append(("Text", text, None))
                    elif kind == "input_image":
                        image_url = item.get("image_url") or item.get("file_id") or "embedded image"
                        blocks.append(("Image", f"Image input: {image_url}", None))
                if blocks:
                    entries.append({
                        "section": role.title() if isinstance(role, str) else "Message",
                        "blocks": blocks,
                    })
                continue

            if item_type == "reasoning":
                summary_items = payload.get("summary") or []
                summary_texts = [item.get("text", "") for item in summary_items if isinstance(item, dict) and item.get("text")]
                if summary_texts:
                    entries.append({
                        "section": "Assistant Reasoning",
                        "blocks": [("Summary", "\n\n".join(summary_texts), None)],
                    })
                continue

            if item_type in {"function_call", "custom_tool_call", "web_search_call"}:
                entries.append({
                    "section": "Assistant Tooling",
                    "blocks": [render_tool_call(payload)],
                })
                continue

            if item_type in {"function_call_output", "custom_tool_call_output"}:
                output = payload.get("output", "")
                rendered = output if isinstance(output, str) else json.dumps(output, indent=2, ensure_ascii=False)
                rendered = truncate(rendered)
                fence = "json" if rendered.strip().startswith("{") else None
                entries.append({
                    "section": "Tool Result",
                    "blocks": [("Output", rendered, fence)],
                })
                continue

    title = summarize(first_user_text) if first_user_text else path.stem
    session_id = session_meta.get("id", path.stem)
    cwd = session_meta.get("cwd", "")
    git = session_meta.get("git") or {}

    lines: list[str] = [
        "---",
        f'source: "codex"',
        f'session_id: "{session_id}"',
        f'timestamp: "{session_meta.get("timestamp", "")}"',
        f'cwd: "{cwd}"',
        f'originator: "{session_meta.get("originator", "")}"',
        f'cli_version: "{session_meta.get("cli_version", "")}"',
        f'git_branch: "{git.get("branch", "")}"',
        f'git_repository_url: "{git.get("repository_url", "")}"',
        "---",
        "",
        f"# Codex Session: {title}",
        "",
    ]

    for entry in entries:
        lines.append(f"## {entry['section']}")
        lines.append("")
        for heading, body, fence in entry["blocks"]:
            emit_block(lines, heading, body, fence)

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print("Usage: codex_jsonl_to_md.py <input.jsonl> [output.md]", file=sys.stderr)
        return 1

    input_path = Path(sys.argv[1]).expanduser()
    output = parse_file(input_path)

    if len(sys.argv) == 3:
        output_path = Path(sys.argv[2]).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
