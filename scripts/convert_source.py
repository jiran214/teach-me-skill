#!/usr/bin/env python3
"""将学习资料转换为markdown格式并保存到sources目录。

支持格式：PDF, EPUB, DOCX, Markdown (.md/.markdown)，以及 markitdown 支持的其他格式。

PDF 使用 PyMuPDF 手动提取字体大小来识别标题层级。
其他格式统一交给 markitdown 处理。

标题指定：
  python convert_source.py file1.pdf "file2.epub:自定义标题" file3.docx
  冒号前是文件路径，冒号后是标题。文件路径本身含冒号时，自动检测路径是否存在来区分。
"""

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


def parse_file_arg(arg: str) -> tuple[Path, str | None]:
    """解析 file:title 格式的参数。

    返回 (文件路径, 标题或None)。
    文件路径本身可能含冒号（macOS/Linux），所以从右往左尝试切分，
    找到第一个左边部分是已存在文件的切分点。
    """
    colon_positions = [i for i, c in enumerate(arg) if c == ":"]

    if not colon_positions:
        return Path(arg), None

    for pos in reversed(colon_positions):
        left = arg[:pos]
        right = arg[pos + 1:]
        if left and Path(left).exists():
            return Path(left), right or None

    return Path(arg), None


# ── PDF（PyMuPDF 手动提取，标题识别更精准）────────────────────────


def extract_font_sizes_from_pdf(pdf_path: Path) -> list[dict]:
    """从 PDF 提取所有文本块及其字体大小信息。"""
    doc = fitz.open(str(pdf_path))
    text_blocks = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block.get("type") != 0:
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

    size_counter = Counter()
    for block in text_blocks:
        if len(block["text"]) > 5:
            size_counter[block["size"]] += 1

    if not size_counter:
        return {}

    sorted_sizes = sorted(size_counter.keys(), reverse=True)
    body_size = size_counter.most_common(1)[0][0]
    heading_sizes = [s for s in sorted_sizes if s > body_size]

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

        if size in size_to_level and len(block["text"]) <= 2:
            parts = [block["text"]]
            j = i + 1
            while j < len(text_blocks):
                next_block = text_blocks[j]
                if (next_block["size"] == size
                        and next_block["page"] <= block["page"] + 1
                        and len(next_block["text"]) <= 2
                        and size in size_to_level):
                    parts.append(next_block["text"])
                    j += 1
                else:
                    break
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
    if not size_to_level:
        fail(
            f"PDF 没有可识别的标题结构: {pdf_path}\n"
            "该文件可能为扫描件或纯图片 PDF，请导入带有文字排版格式的资源。"
        )

    text_blocks = _merge_heading_spans(text_blocks, size_to_level)

    lines = []
    current_paragraph = []

    for block in text_blocks:
        text = block["text"]
        size = block["size"]

        if size in size_to_level:
            if current_paragraph:
                lines.append(" ".join(current_paragraph))
                lines.append("")
                current_paragraph = []

            heading_prefix = size_to_level[size]
            lines.append(f"{heading_prefix} {text}")
            lines.append("")
        else:
            if text:
                current_paragraph.append(text)

    if current_paragraph:
        lines.append(" ".join(current_paragraph))

    result = "\n".join(lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip() + "\n"


# ── EPUB（NCX + HTML 合成，标题结构从目录提取）────────────────────


def _parse_ncx_from_epub(epub_path: Path) -> list[dict]:
    """从 EPUB 的 NCX 文件解析目录结构。

    返回 [{title, src, level}, ...]，level 从 1 开始。
    NCX 不存在或解析失败时返回空列表。
    """
    import zipfile
    from xml.dom.minidom import parseString

    with zipfile.ZipFile(str(epub_path), "r") as zf:
        # 找 OPF 路径
        container = parseString(zf.read("META-INF/container.xml"))
        opf_rel = container.getElementsByTagName("rootfile")[0].getAttribute("full-path")

        # 从 OPF 找 NCX 路径
        opf_dir = str(Path(opf_rel).parent)
        opf = parseString(zf.read(opf_rel))
        ncx_href = None
        for item in opf.getElementsByTagName("item"):
            mt = item.getAttribute("media-type")
            if "ncx" in mt:
                ncx_href = item.getAttribute("href")
                break
        if not ncx_href:
            return []

        ncx_path = f"{opf_dir}/{ncx_href}" if opf_dir != "." else ncx_href
        ncx = parseString(zf.read(ncx_path))

    # 递归解析 navMap
    entries: list[dict] = []

    def walk_navpoints(nodes, depth: int):
        for node in nodes:
            if node.nodeType != node.ELEMENT_NODE or node.tagName != "navPoint":
                continue
            label_el = node.getElementsByTagName("navLabel")
            text_el = label_el[0].getElementsByTagName("text") if label_el else []
            title = text_el[0].firstChild.nodeValue.strip() if text_el and text_el[0].firstChild else ""

            content_el = node.getElementsByTagName("content")
            src = content_el[0].getAttribute("src") if content_el else ""

            if title:
                entries.append({"title": title, "src": src, "level": depth})

            walk_navpoints(node.childNodes, depth + 1)

    navmap = ncx.getElementsByTagName("navMap")
    if navmap:
        walk_navpoints(navmap[0].childNodes, 1)

    return entries


def _extract_paragraphs_from_html(html_bytes: bytes) -> list[str]:
    """从 HTML 提取所有段落文本，返回文本列表（保持顺序）。"""
    from xml.dom.minidom import parseString

    try:
        doc = parseString(html_bytes)
    except Exception:
        return []

    paragraphs: list[str] = []
    for p in doc.getElementsByTagName("p"):
        parts = []
        for child in p.childNodes:
            if child.nodeType == child.TEXT_NODE:
                parts.append(child.nodeValue)
            elif child.nodeType == child.ELEMENT_NODE:
                if child.tagName == "img":
                    continue
                text = child.firstChild.nodeValue if child.firstChild else ""
                if text:
                    parts.append(text)
        line = "".join(parts).strip()
        if line:
            paragraphs.append(line)

    return paragraphs


def _normalize(text: str) -> str:
    """去除多余空白，用于标题匹配比较。"""
    return re.sub(r"\s+", "", text)


def _extract_epub_metadata(opf_doc) -> dict[str, str]:
    """从 OPF 文档提取元数据（标题、作者、语言等）。"""
    metadata = {}
    dc_ns = "http://purl.org/dc/elements/1.1/"

    def get_dc(tag: str) -> str:
        els = opf_doc.getElementsByTagNameNS(dc_ns, tag)
        if not els:
            els = opf_doc.getElementsByTagName(f"dc:{tag}")
        if els and els[0].firstChild:
            return els[0].firstChild.nodeValue.strip()
        return ""

    metadata["title"] = get_dc("title")
    metadata["authors"] = get_dc("creator")
    metadata["language"] = get_dc("language")
    metadata["date"] = get_dc("date")
    metadata["identifier"] = get_dc("identifier")
    return {k: v for k, v in metadata.items() if v}


def convert_epub_to_markdown(epub_path: Path) -> str:
    """将 EPUB 转换为 markdown，标题结构从 NCX 目录提取。"""
    import zipfile

    ncx_entries = _parse_ncx_from_epub(epub_path)
    if not ncx_entries:
        # NCX 不存在（EPUB 3 可能只有 NAV），降级到 markitdown
        return convert_with_markitdown(epub_path)

    # 按 src 分组，src 可能含 #anchor，只取文件名部分
    src_to_entries: dict[str, list[dict]] = {}
    for entry in ncx_entries:
        file_key = entry["src"].split("#")[0]
        src_to_entries.setdefault(file_key, []).append(entry)

    # 读取 OPF 获取 spine 顺序和元数据
    with zipfile.ZipFile(str(epub_path), "r") as zf:
        from xml.dom.minidom import parseString

        container = parseString(zf.read("META-INF/container.xml"))
        opf_rel = container.getElementsByTagName("rootfile")[0].getAttribute("full-path")
        opf_dir = str(Path(opf_rel).parent)
        opf = parseString(zf.read(opf_rel))

        # 提取元数据
        metadata = _extract_epub_metadata(opf)

        # manifest: id → href
        manifest: dict[str, str] = {}
        for item in opf.getElementsByTagName("item"):
            manifest[item.getAttribute("id")] = item.getAttribute("href")

        # spine 顺序
        spine_refs: list[str] = []
        spine = opf.getElementsByTagName("spine")
        if spine:
            for itemref in spine[0].getElementsByTagName("itemref"):
                ref_id = itemref.getAttribute("idref")
                if ref_id in manifest:
                    spine_refs.append(manifest[ref_id])

        # 按 spine 顺序处理每个 HTML 文件
        all_sections: list[str] = []
        for href in spine_refs:
            file_path = f"{opf_dir}/{href}" if opf_dir != "." else href
            try:
                html_bytes = zf.read(file_path)
            except KeyError:
                continue

            paragraphs = _extract_paragraphs_from_html(html_bytes)
            if not paragraphs:
                continue

            # 获取该文件对应的 NCX 条目
            entries_for_file = src_to_entries.get(href, [])
            if not entries_for_file:
                # 无标题，直接输出正文
                all_sections.append("\n\n".join(paragraphs))
                continue

            # 匹配标题：NCX 标题可能跨多个 HTML 段落，需要累积拼接后比较
            ncx_idx = 0
            used = [False] * len(entries_for_file)
            result_parts: list[str] = []
            acc_paras: list[str] = []  # 累积的段落（尚未决定归属）

            for para in paragraphs:
                acc_paras.append(para)
                acc_text = "".join(acc_paras)
                acc_norm = _normalize(acc_text)

                matched = False
                if ncx_idx < len(entries_for_file):
                    norm_title = _normalize(entries_for_file[ncx_idx]["title"])

                    if acc_norm == norm_title:
                        # 精确匹配：累积文本恰好是标题
                        level = entries_for_file[ncx_idx]["level"]
                        heading = "#" * min(level, 6)
                        result_parts.append(f"{heading} {entries_for_file[ncx_idx]['title']}")
                        used[ncx_idx] = True
                        ncx_idx += 1
                        acc_paras.clear()
                        matched = True
                    elif acc_norm.startswith(norm_title):
                        # 累积文本以标题开头，标题后有剩余
                        level = entries_for_file[ncx_idx]["level"]
                        heading = "#" * min(level, 6)
                        result_parts.append(f"{heading} {entries_for_file[ncx_idx]['title']}")
                        used[ncx_idx] = True
                        ncx_idx += 1
                        # 找到原始文本中标题结束的位置（逐字符规范化比较）
                        norm_count = 0
                        title_end = 0
                        for ci, ch in enumerate(acc_text):
                            if not ch.isspace():
                                norm_count += 1
                            if norm_count == len(norm_title):
                                title_end = ci + 1
                                break
                        leftover = acc_text[title_end:].strip()
                        acc_paras = [leftover] if leftover else []
                        matched = True

                if not matched and len(acc_paras) > 1:
                    # 累积了多个段落仍未匹配，输出最早的段落作为正文
                    # （保留最后一个段落继续累积，因为它可能是标题的前半部分）
                    for p in acc_paras[:-1]:
                        result_parts.append(p)
                    acc_paras = [acc_paras[-1]]

            # 输出剩余累积段落
            result_parts.extend(acc_paras)

            # 处理未匹配到的标题（追加到末尾）
            for i, entry in enumerate(entries_for_file):
                if not used[i]:
                    level = entry["level"]
                    heading = "#" * min(level, 6)
                    result_parts.append(f"{heading} {entry['title']}")

            all_sections.append("\n\n".join(result_parts))

    # 拼接元数据和正文
    meta_lines = []
    if metadata.get("title"):
        meta_lines.append(f"# {metadata['title']}")
    if metadata.get("authors"):
        meta_lines.append(f"**Authors:** {metadata['authors']}")
    if metadata.get("language"):
        meta_lines.append(f"**Language:** {metadata['language']}")
    if metadata.get("date"):
        meta_lines.append(f"**Date:** {metadata['date']}")

    parts = []
    if meta_lines:
        parts.append("\n".join(meta_lines))
    parts.extend(all_sections)

    result = "\n\n".join(parts)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip() + "\n"


# ── 非 PDF/EPUB 格式（markitdown 统一处理）────────────────────────


def is_markdown_file(path: Path) -> bool:
    return path.suffix.lower() in (".md", ".markdown")


def convert_with_markitdown(source_path: Path) -> str:
    """使用 markitdown 转换非 PDF 文件。"""
    from markitdown import MarkItDown

    converter = MarkItDown()
    result = converter.convert(str(source_path))
    text = getattr(result, "text_content", "")
    if not text or not text.strip():
        fail(f"converter produced no text for: {source_path}")

    if not re.search(r"^#{1,6}\s", text, re.MULTILINE):
        fail(
            f"文件缺少标题结构: {source_path}\n"
            "转换后的内容没有检测到标题层级，请导入带有格式（标题、层级）的资源。"
        )

    return text.strip() + "\n"


def convert_to_markdown(source_path: Path) -> str:
    """根据文件类型选择合适的转换方式。PDF 用 PyMuPDF，EPUB 用 NCX+HTML，其他用 markitdown。"""
    suffix = source_path.suffix.lower()

    if suffix == ".pdf":
        return convert_pdf_to_markdown(source_path)

    if suffix == ".epub":
        return convert_epub_to_markdown(source_path)

    return convert_with_markitdown(source_path)


def save_markdown(markdown: str, source_path: Path, sources_dir: Path, title: str | None = None) -> Path:
    if title:
        # 使用自定义标题作为文件名，清理非法字符
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title).strip()
        md_filename = safe_title + ".md"
        markdown = f"# {title}\n\n{markdown}"
    else:
        md_filename = source_path.stem + ".md"
    md_path = sources_dir / md_filename
    md_path.write_text(markdown, encoding="utf-8")
    return md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将学习资料转换为markdown并保存到sources目录。",
        epilog=(
            "标题指定方式:\n"
            "  python convert_source.py file1.pdf 'file2.epub:自定义标题'\n"
            "  冒号前是文件路径，冒号后是标题。文件路径本身含冒号时自动识别。\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("files", nargs="+", help="要转换的文件，支持 file:title 语法指定标题")
    parser.add_argument(
        "--workspace",
        default=".",
        help="学习工作区根目录，默认为当前目录。",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="(已废弃) 对所有文件使用同一标题，请改用 file:title 语法。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    sources_dir = workspace / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    file_entries: list[tuple[Path, str | None]] = []
    for raw_arg in args.files:
        path, title = parse_file_arg(raw_arg)
        file_entries.append((path, title))

    # 兼容旧的 --title 参数
    if args.title and all(t is None for _, t in file_entries):
        file_entries = [(p, args.title) for p, _ in file_entries]

    for source_path, title in file_entries:
        if is_markdown_file(source_path):
            md_path = copy_to_sources(source_path, sources_dir)
            if title:
                content = md_path.read_text(encoding="utf-8")
                content = f"# {title}\n\n{content}"
                md_path.write_text(content, encoding="utf-8")
            md_rel = md_path.resolve().relative_to(workspace).as_posix()
            print(f"copied: {md_rel}")
        else:
            source_path = copy_to_sources(source_path, sources_dir)
            markdown = convert_to_markdown(source_path)
            md_path = save_markdown(markdown, source_path, sources_dir, title=title)
            md_rel = md_path.resolve().relative_to(workspace).as_posix()
            print(f"converted: {md_rel}")


if __name__ == "__main__":
    main()
