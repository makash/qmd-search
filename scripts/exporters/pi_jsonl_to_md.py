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


def parse_file(path: Path) -> str:
    session: dict[str, Any] = {}
    model: dict[str, Any] = {}
    thinking_level = ""
    first_user_text = ""
    entries: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            obj = json.loads(raw_line)
            top_type = obj.get("type")

            if top_type == "session":
                session = obj
                continue
            if top_type == "model_change":
                model = obj
                continue
            if top_type == "thinking_level_change":
                thinking_level = obj.get("thinkingLevel", "")
                continue
            if top_type != "message":
                continue

            message = obj.get("message", {})
            role = message.get("role", "message")
            content = message.get("content") or []
            blocks: list[tuple[str, str, str | None]] = []

            for item in content:
                if not isinstance(item, dict):
                    continue
                kind = item.get("type")
                if kind == "text":
                    text = item.get("text", "")
                    if role == "user" and text and not first_user_text:
                        first_user_text = text
                    blocks.append(("Text", text, None))
                elif kind == "thinking":
                    blocks.append(("Thinking", truncate(item.get("thinking", ""), 2000), None))
                elif kind == "toolCall":
                    tool_view = {
                        "name": item.get("name"),
                        "arguments": item.get("arguments"),
                        "id": item.get("id"),
                    }
                    blocks.append((f"Tool Call: {item.get('name', 'unknown')}", json.dumps(tool_view, indent=2, ensure_ascii=False), "json"))
                elif kind == "image":
                    blocks.append(("Image", "Embedded image content omitted", None))

            if blocks:
                entries.append({
                    "section": role.title(),
                    "blocks": blocks,
                })

    title = summarize(first_user_text) if first_user_text else path.stem
    lines: list[str] = [
        "---",
        f'source: "pi"',
        f'session_id: "{session.get("id", path.stem)}"',
        f'timestamp: "{session.get("timestamp", "")}"',
        f'cwd: "{session.get("cwd", "")}"',
        f'provider: "{model.get("provider", "")}"',
        f'model_id: "{model.get("modelId", "")}"',
        f'thinking_level: "{thinking_level}"',
        "---",
        "",
        f"# Pi Session: {title}",
        "",
    ]

    for entry in entries:
        lines.append(f"## {entry['section']}")
        lines.append("")
        for heading, body, fence in entry["blocks"]:
            emit_block(lines, heading, truncate(body) if fence is None else body, fence)

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print("Usage: pi_jsonl_to_md.py <input.jsonl> [output.md]", file=sys.stderr)
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
