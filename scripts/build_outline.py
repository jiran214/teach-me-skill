#!/usr/bin/env python3
"""基于sources目录中的markdown文件，生成outline（含行号索引）。"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


@dataclass
class HeadingEntry:
    level: int
    title: str
    line: int  # 1-based line number


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def ensure_dirs(workspace: Path) -> None:
    (workspace / "sources").mkdir(parents=True, exist_ok=True)


def clean_heading(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value.strip("#").strip() or "Untitled"


def guess_title(markdown: str, source_name: str) -> str:
    book_name_match = re.search(r"^(?:书名|title)[：:]\s*(.+)$", markdown, re.MULTILINE | re.IGNORECASE)
    if book_name_match:
        return book_name_match.group(1).strip()

    match = HEADING_RE.search(markdown)
    if match:
        return clean_heading(match.group(2))
    return Path(source_name).stem


def extract_headings(markdown: str) -> list[HeadingEntry]:
    """提取markdown中所有标题及其行号（1-based）。"""
    entries: list[HeadingEntry] = []
    for line_num, line in enumerate(markdown.splitlines(), start=1):
        match = HEADING_RE.match(line)
        if match:
            level = len(match.group(1))
            title = clean_heading(match.group(2))
            entries.append(HeadingEntry(level=level, title=title, line=line_num))
    return entries


def build_outline_for_source(source_rel: str, title: str, headings: list[HeadingEntry]) -> list[str]:
    """为单个源文件生成outline行。"""
    if not headings:
        return []

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")

    for entry in headings:
        indent = "  " * max(entry.level - 1, 0)
        lines.append(f"{indent}- [{entry.title}]({source_rel}#L{entry.line})")

    lines.append("")
    return lines


def rebuild_outline(workspace: Path, sources: dict[str, tuple[str, list[HeadingEntry]]]) -> None:
    """重建sources/outline.md。

    sources: {source_rel: (title, headings)}
    """
    outline_path = workspace / "sources" / "outline.md"
    all_lines: list[str] = []

    for source_rel in sorted(sources):
        title, headings = sources[source_rel]
        all_lines.extend(build_outline_for_source(source_rel, title, headings))

    outline_path.write_text("\n".join(all_lines).rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="基于sources中的markdown文件生成sources/outline.md（含行号索引）。"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="要处理的markdown文件。如不指定，处理sources目录下所有.md文件。",
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="学习工作区根目录，默认为当前目录。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    ensure_dirs(workspace)
    sources_dir = workspace / "sources"

    if args.files:
        md_files = [Path(f) for f in args.files]
    else:
        md_files = sorted(sources_dir.glob("*.md"))
        if not md_files:
            fail(f"no markdown files found in {sources_dir}")

    sources: dict[str, tuple[str, list[HeadingEntry]]] = {}

    for md_path in md_files:
        if not md_path.exists():
            fail(f"file not found: {md_path}")

        markdown = md_path.read_text(encoding="utf-8")
        source_rel = md_path.resolve().relative_to(workspace).as_posix()
        title = guess_title(markdown, md_path.name)
        headings = extract_headings(markdown)
        sources[source_rel] = (title, headings)
        print(f"indexed {source_rel}: {len(headings)} headings")

    rebuild_outline(workspace, sources)
    print(f"updated sources/outline.md")


if __name__ == "__main__":
    main()
