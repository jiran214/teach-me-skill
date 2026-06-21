#!/usr/bin/env python3
"""测试PDF解析：目录提取和切分策略"""

import sys
from pathlib import Path

# 添加scripts目录到path以便导入
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from convert_source import convert_to_markdown
from build_outline import guess_title, split_sections, build_chunks


def test_markdown_conversion(pdf_path: Path) -> str:
    """测试PDF转markdown"""
    print("=" * 60)
    print("测试1: PDF转Markdown")
    print("=" * 60)

    markdown = convert_to_markdown(pdf_path)
    print(f"转换成功，生成 {len(markdown)} 字符的markdown")
    print("\n前500字符预览:")
    print("-" * 40)
    print(markdown[:500])
    print("-" * 40)
    return markdown


def test_title_extraction(markdown: str, pdf_path: Path) -> str:
    """测试标题提取"""
    print("\n" + "=" * 60)
    print("测试2: 标题提取")
    print("=" * 60)

    title = guess_title(markdown, pdf_path.name)
    print(f"提取的标题: {title}")
    return title


def test_section_splitting(markdown: str, title: str) -> list:
    """测试章节切分"""
    print("\n" + "=" * 60)
    print("测试3: 章节切分")
    print("=" * 60)

    sections = split_sections(markdown, title)
    print(f"切分出 {len(sections)} 个章节:")
    for i, section in enumerate(sections, 1):
        body_preview = section.body[:80].replace("\n", " ")
        print(f"  {i}. [{section.heading}] ({len(section.body)} 字符)")
        print(f"     预览: {body_preview}...")
    return sections


def test_chunk_building(sections: list, title: str, source_rel: str) -> list:
    """测试chunk构建"""
    print("\n" + "=" * 60)
    print("测试4: Chunk构建")
    print("=" * 60)

    chunks = build_chunks(source_rel, title, sections, 0, 9000)
    print(f"生成 {len(chunks)} 个chunks:")
    for chunk in chunks:
        print(f"  - {chunk.filename}")
        print(f"    section: {chunk.section}")
        print(f"    size: {len(chunk.body)} 字符")
        print(f"    prev: {chunk.previous or '(无)'}")
        print(f"    next: {chunk.next or '(无)'}")
    return chunks


def test_toc_extraction(markdown: str) -> None:
    """测试目录提取 - 检查是否包含章节结构"""
    print("\n" + "=" * 60)
    print("测试5: 目录结构验证")
    print("=" * 60)

    expected_headings = [
        "Chapter 1",
        "Chapter 2",
        "Chapter 3",
        "1.1",
        "1.2",
        "1.3",
        "2.1",
        "2.2",
        "3.1",
        "3.2",
        "3.3",
    ]

    found = []
    missing = []
    for heading in expected_headings:
        if heading in markdown:
            found.append(heading)
        else:
            missing.append(heading)

    print(f"找到 {len(found)}/{len(expected_headings)} 个预期标题")
    if missing:
        print(f"缺失的标题: {missing}")
    else:
        print("所有预期标题都已找到!")


def main():
    # 生成测试PDF
    pdf_path = Path(__file__).parent / "sample_book.pdf"
    if not pdf_path.exists():
        print("生成测试PDF...")
        from generate_test_pdf import create_test_pdf
        create_test_pdf(str(pdf_path))

    # 运行测试
    markdown = test_markdown_conversion(pdf_path)
    title = test_title_extraction(markdown, pdf_path)
    sections = test_section_splitting(markdown, title)
    chunks = test_chunk_building(sections, title, "sources/sample_book.pdf")
    test_toc_extraction(markdown)

    # 保存转换后的markdown供检查
    md_output = Path(__file__).parent / "sample_book_output.md"
    md_output.write_text(markdown, encoding="utf-8")
    print(f"\n转换后的markdown已保存到: {md_output}")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
