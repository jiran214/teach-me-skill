#!/usr/bin/env python3
"""将学习资料转换为markdown格式并保存到sources目录。"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

import fitz  # PyMuPDF


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def next_available_source_path(sources_dir: Path, original_name: str) -> Path:
    candidate = sources_dir / original_name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    index = 2
    while True:
        numbered = sources_dir / f"{stem}-{index}{suffix}"
        if not numbered.exists():
            return numbered
        index += 1


def copy_to_sources(path: Path, sources_dir: Path) -> Path:
    resolved = path.resolve()
    if not resolved.exists():
        fail(f"source file not found: {path}")
    if not resolved.is_file():
        fail(f"source path is not a file: {path}")

    try:
        resolved.relative_to(sources_dir.resolve())
        return resolved
    except ValueError:
        destination = next_available_source_path(sources_dir, path.name)
        shutil.copy2(resolved, destination)
        return destination


def extract_font_sizes_from_pdf(pdf_path: Path) -> list[dict]:
    """从 PDF 提取所有文本块及其字体大小信息。"""
    doc = fitz.open(str(pdf_path))
    text_blocks = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block.get("type") != 0:  # 只处理文本块
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text:
                        text_blocks.append({
                            "text": text,
                            "size": span["size"],
                            "font": span["font"],
                            "page": page_num + 1,
                            "bold": "Bold" in span["font"] or "bold" in span["font"],
                        })

    doc.close()
    return text_blocks


def classify_heading_levels(text_blocks: list[dict]) -> dict[float, str]:
    """根据字体大小分布，将字体大小映射到 markdown 标题层级。"""
    if not text_blocks:
        return {}

    # 统计字体大小出现次数（只统计较长的文本，过滤掉页码等）
    size_counter = Counter()
    for block in text_blocks:
        if len(block["text"]) > 5:  # 只统计有意义的文本
            size_counter[block["size"]] += 1

    if not size_counter:
        return {}

    # 按字体大小降序排列
    sorted_sizes = sorted(size_counter.keys(), reverse=True)

    # 找出正文大小（出现最多的字体大小）
    body_size = size_counter.most_common(1)[0][0]

    # 只保留比正文大的字体作为标题候选
    heading_sizes = [s for s in sorted_sizes if s > body_size]

    # 映射到标题层级（最多支持 h1-h4）
    size_to_level = {}
    for i, size in enumerate(heading_sizes[:4]):
        if i == 0:
            size_to_level[size] = "#"
        elif i == 1:
            size_to_level[size] = "##"
        elif i == 2:
            size_to_level[size] = "###"
        elif i == 3:
            size_to_level[size] = "####"

    return size_to_level


def _merge_heading_spans(text_blocks: list[dict], size_to_level: dict[float, str]) -> list[dict]:
    """合并连续的同字号短文本标题span（如逐字拆分的章节标题）。"""
    merged = []
    i = 0
    while i < len(text_blocks):
        block = text_blocks[i]
        size = block["size"]

        # 只对标题级别的span做合并，且当前span是短文本（单字或标点）
        if size in size_to_level and len(block["text"]) <= 2:
            parts = [block["text"]]
            j = i + 1
            while j < len(text_blocks):
                next_block = text_blocks[j]
                # 合并条件：同字号、同页面（或相邻页面）、短文本、标题级别
                if (next_block["size"] == size
                        and next_block["page"] <= block["page"] + 1
                        and len(next_block["text"]) <= 2
                        and size in size_to_level):
                    parts.append(next_block["text"])
                    j += 1
                else:
                    break
            # 合并后如果超过2个片段，认为是被拆散的标题
            if len(parts) > 2:
                merged.append({
                    "text": "".join(parts),
                    "size": size,
                    "font": block["font"],
                    "page": block["page"],
                    "bold": block["bold"],
                })
                i = j
                continue
        merged.append(block)
        i += 1
    return merged


def convert_pdf_to_markdown(pdf_path: Path) -> str:
    """将 PDF 转换为 markdown，保留标题结构。"""
    text_blocks = extract_font_sizes_from_pdf(pdf_path)
    if not text_blocks:
        fail(f"no text extracted from: {pdf_path}")

    size_to_level = classify_heading_levels(text_blocks)
    text_blocks = _merge_heading_spans(text_blocks, size_to_level)

    # 构建 markdown
    lines = []
    current_paragraph = []

    for block in text_blocks:
        text = block["text"]
        size = block["size"]

        # 判断是否是标题
        if size in size_to_level:
            # 先结束当前段落
            if current_paragraph:
                lines.append(" ".join(current_paragraph))
                lines.append("")
                current_paragraph = []

            # 添加标题
            heading_prefix = size_to_level[size]
            lines.append(f"{heading_prefix} {text}")
            lines.append("")
        else:
            # 普通文本，积累成段落
            if text:
                current_paragraph.append(text)

    # 处理最后一个段落
    if current_paragraph:
        lines.append(" ".join(current_paragraph))

    # 清理多余的空行
    result = "\n".join(lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip() + "\n"


def convert_to_markdown(source_path: Path) -> str:
    """根据文件类型选择合适的转换方式。"""
    suffix = source_path.suffix.lower()

    if suffix == ".pdf":
        return convert_pdf_to_markdown(source_path)
    else:
        # 对于非 PDF 文件，使用 markitdown 或其他方式
        # 这里先简单处理，后续可以扩展
        try:
            from markitdown import MarkItDown
            converter = MarkItDown()
            result = converter.convert(str(source_path))
            text = getattr(result, "text_content", "")
            if not text or not text.strip():
                fail(f"converter produced no text for: {source_path}")
            return text.strip() + "\n"
        except ImportError:
            fail(f"unsupported file type {suffix} and markitdown not installed")


def save_markdown(markdown: str, source_path: Path, sources_dir: Path, title: str | None = None) -> Path:
    md_filename = source_path.stem + ".md"
    md_path = sources_dir / md_filename
    if title:
        markdown = f"# {title}\n\n{markdown}"
    md_path.write_text(markdown, encoding="utf-8")
    return md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将学习资料转换为markdown并保存到sources目录。"
    )
    parser.add_argument("files", nargs="+", help="要转换的文件")
    parser.add_argument(
        "--workspace",
        default=".",
        help="学习工作区根目录，默认为当前目录。",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="文档标题。如不指定，从文件内容自动推断。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    sources_dir = workspace / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    for raw_file in args.files:
        source_path = copy_to_sources(Path(raw_file), sources_dir)
        markdown = convert_to_markdown(source_path)
        md_path = save_markdown(markdown, source_path, sources_dir, title=args.title)
        md_rel = md_path.resolve().relative_to(workspace).as_posix()
        print(f"converted: {md_rel}")


if __name__ == "__main__":
    main()
