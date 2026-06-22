#!/usr/bin/env python3
"""测试 convert_source.py 对 EPUB 的 NCX 标题提取能力。

构造一个模拟"PDF转EPUB"场景的测试文件：HTML用<b>做标题（无<h1>），
NCX中有完整的层级目录。这正是 markitdown 处理不好的情况。

运行方式：
  uv run pytest tests/test_epub_mysql.py -v
"""

import sys
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from convert_source import (
    _parse_ncx_from_epub,
    convert_epub_to_markdown,
    convert_to_markdown,
    save_markdown,
)


# ── 模拟 EPUB 构建 ────────────────────────────────────────────────


def _build_mock_epub(tmp_path: Path) -> Path:
    """构建一个模拟"PDF转EPUB"的测试文件。

    结构：
      第1章 MySQL入门        (h1)
        1.1 客户端架构        (h2)
        1.2 安装与配置        (h2)
          1.2.1 Windows安装   (h3)
          1.2.2 Linux安装     (h3)
      第2章 存储引擎          (h1)
        2.1 InnoDB简介        (h2)
        2.2 MyISAM简介        (h2)

    HTML中标题用<b>标签（模拟pdftohtml输出），不用<h1>。
    """
    # ── HTML 内容 ──
    html1 = """\
<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>ch1</title></head>
<body>
<p><b>第1章 MySQL入门</b></p>
<p>MySQL是一个关系型数据库管理系统，由瑞典MySQL AB公司开发。</p>
<p>它是目前最流行的开源数据库之一，广泛应用于Web应用。</p>
<p><b>1.1 客户端架构</b></p>
<p>MySQL采用客户端/服务器架构，客户端通过TCP/IP连接服务器。</p>
<p>服务器负责处理SQL查询并返回结果集。</p>
<p><b>1.2 安装与配置</b></p>
<p>MySQL支持多种操作系统，安装方式各有不同。</p>
<p><b>1.2.1 Windows安装</b></p>
<p>在Windows上可以通过MSI安装包或ZIP压缩包进行安装。</p>
<p>安装完成后需要初始化数据目录并启动服务。</p>
<p><b>1.2.2 Linux安装</b></p>
<p>在Linux上推荐使用包管理器安装，如apt或yum。</p>
<p>安装后需要运行mysql_secure_installation进行安全配置。</p>
</body>
</html>"""

    html2 = """\
<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>ch2</title></head>
<body>
<p><b>第2章 存储引擎</b></p>
<p>MySQL支持多种存储引擎，每种引擎有不同的特性。</p>
<p>选择合适的存储引擎对性能至关重要。</p>
<p><b>2.1 InnoDB简介</b></p>
<p>InnoDB是MySQL的默认存储引擎，支持事务和行级锁。</p>
<p>它使用B+树索引结构，支持外键约束。</p>
<p><b>2.2 MyISAM简介</b></p>
<p>MyISAM是早期的默认引擎，不支持事务但读取速度快。</p>
<p>它适用于读多写少的场景。</p>
</body>
</html>"""

    # ── NCX 目录 ──
    ncx = """\
<?xml version='1.0' encoding='utf-8'?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<head>
  <meta name="dtb:uid" content="test-mock-epub"/>
</head>
<docTitle><text>Mock MySQL Book</text></docTitle>
<navMap>
  <navPoint id="ch1" playOrder="1" class="chapter">
    <navLabel><text>第1章 MySQL入门</text></navLabel>
    <content src="ch1.xhtml"/>
    <navPoint id="s1_1" playOrder="2" class="chapter">
      <navLabel><text>1.1 客户端架构</text></navLabel>
      <content src="ch1.xhtml"/>
    </navPoint>
    <navPoint id="s1_2" playOrder="3" class="chapter">
      <navLabel><text>1.2 安装与配置</text></navLabel>
      <content src="ch1.xhtml"/>
      <navPoint id="s1_2_1" playOrder="4" class="chapter">
        <navLabel><text>1.2.1 Windows安装</text></navLabel>
        <content src="ch1.xhtml"/>
      </navPoint>
      <navPoint id="s1_2_2" playOrder="5" class="chapter">
        <navLabel><text>1.2.2 Linux安装</text></navLabel>
        <content src="ch1.xhtml"/>
      </navPoint>
    </navPoint>
  </navPoint>
  <navPoint id="ch2" playOrder="6" class="chapter">
    <navLabel><text>第2章 存储引擎</text></navLabel>
    <content src="ch2.xhtml"/>
    <navPoint id="s2_1" playOrder="7" class="chapter">
      <navLabel><text>2.1 InnoDB简介</text></navLabel>
      <content src="ch2.xhtml"/>
    </navPoint>
    <navPoint id="s2_2" playOrder="8" class="chapter">
      <navLabel><text>2.2 MyISAM简介</text></navLabel>
      <content src="ch2.xhtml"/>
    </navPoint>
  </navPoint>
</navMap>
</ncx>"""

    # ── OPF ──
    opf = """\
<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0"
         unique-identifier="uuid_id">
  <metadata>
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Mock MySQL Book</dc:title>
    <dc:language xmlns:dc="http://purl.org/dc/elements/1.1/">zh</dc:language>
    <dc:identifier xmlns:dc="http://purl.org/dc/elements/1.1/"
                   id="uuid_id">test-mock-epub</dc:identifier>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="ch1"/>
    <itemref idref="ch2"/>
  </spine>
</package>"""

    # ── 写入 EPUB（ZIP格式）──
    epub_path = tmp_path / "mock_mysql.epub"
    with zipfile.ZipFile(str(epub_path), "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", """\
<?xml version='1.0' encoding='utf-8'?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
        zf.writestr("content.opf", opf)
        zf.writestr("toc.ncx", ncx)
        zf.writestr("ch1.xhtml", html1)
        zf.writestr("ch2.xhtml", html2)

    return epub_path


# ── fixtures ─────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def mock_epub(tmp_path_factory) -> Path:
    """生成模拟"PDF转EPUB"的测试文件。"""
    tmp = tmp_path_factory.mktemp("epub_build")
    return _build_mock_epub(tmp)


@pytest.fixture(scope="module")
def converted_markdown(mock_epub) -> str:
    """转换 mock EPUB 并返回 markdown。"""
    return convert_epub_to_markdown(mock_epub)


# ── NCX 解析测试 ─────────────────────────────────────────────────


class TestNCXParsing:
    def test_ncx_entry_count(self, mock_epub):
        entries = _parse_ncx_from_epub(mock_epub)
        assert len(entries) == 8

    def test_ncx_hierarchy_levels(self, mock_epub):
        entries = _parse_ncx_from_epub(mock_epub)
        levels = [e["level"] for e in entries]
        assert levels == [1, 2, 2, 3, 3, 1, 2, 2]

    def test_ncx_titles(self, mock_epub):
        entries = _parse_ncx_from_epub(mock_epub)
        titles = [e["title"] for e in entries]
        assert titles[0] == "第1章 MySQL入门"
        assert titles[3] == "1.2.1 Windows安装"
        assert titles[5] == "第2章 存储引擎"

    def test_ncx_src_mapping(self, mock_epub):
        entries = _parse_ncx_from_epub(mock_epub)
        assert all(e["src"].startswith("ch") for e in entries)
        # 第1章的条目都指向 ch1.xhtml
        assert entries[0]["src"] == "ch1.xhtml"
        assert entries[5]["src"] == "ch2.xhtml"


# ── 标题层级提取测试 ─────────────────────────────────────────────


class TestMetadata:
    def test_title_extracted(self, converted_markdown):
        """书名应从 OPF 元数据提取并作为 # 标题输出。"""
        assert converted_markdown.startswith("# Mock MySQL Book")

    def test_language_present(self, converted_markdown):
        assert "**Language:** zh" in converted_markdown


class TestHeadingExtraction:
    def test_h1_chapters(self, converted_markdown):
        import re
        h1s = re.findall(r"^# .+", converted_markdown, re.MULTILINE)
        # 第一个是元数据标题，后面是章节标题
        assert h1s[0] == "# Mock MySQL Book"
        assert "# 第1章 MySQL入门" in h1s
        assert "# 第2章 存储引擎" in h1s

    def test_h2_sections(self, converted_markdown):
        import re
        h2s = re.findall(r"^## .+", converted_markdown, re.MULTILINE)
        assert len(h2s) == 4
        assert "## 1.1 客户端架构" in h2s
        assert "## 1.2 安装与配置" in h2s
        assert "## 2.1 InnoDB简介" in h2s
        assert "## 2.2 MyISAM简介" in h2s

    def test_h3_subsections(self, converted_markdown):
        import re
        h3s = re.findall(r"^### .+", converted_markdown, re.MULTILINE)
        assert len(h3s) == 2
        assert "### 1.2.1 Windows安装" in h3s
        assert "### 1.2.2 Linux安装" in h3s

    def test_heading_ordering(self, converted_markdown):
        """章节标题应按文档顺序出现。"""
        import re
        headings = re.findall(r"^#{1,3} .+", converted_markdown, re.MULTILINE)
        # 用完整标题前缀匹配，避免子串误匹配（如 "2.1" 匹配到 "1.2.1"）
        def find_idx(prefix):
            return next(i for i, h in enumerate(headings) if h.startswith(prefix) or h.startswith("# " + prefix))

        assert find_idx("# 第1章") < find_idx("## 1.1")
        assert find_idx("## 1.1") < find_idx("## 1.2 安装")
        assert find_idx("## 1.2 安装") < find_idx("### 1.2.1")
        assert find_idx("### 1.2.2") < find_idx("# 第2章")
        assert find_idx("# 第2章") < find_idx("## 2.1")
        assert find_idx("## 2.1") < find_idx("## 2.2 MyISAM")


# ── 正文内容测试 ─────────────────────────────────────────────────


class TestBodyContent:
    def test_body_text_present(self, converted_markdown):
        assert "关系型数据库管理系统" in converted_markdown
        assert "B+树索引结构" in converted_markdown
        assert "行级锁" in converted_markdown

    def test_no_bold_heading_artifacts(self, converted_markdown):
        """标题不应保留<b>标签转换的**粗体**格式。"""
        import re
        # 标题行不应以 ** 开头
        for line in converted_markdown.split("\n"):
            if line.startswith("#"):
                assert not line.endswith("**"), f"标题行有粗体残留: {line}"

    def test_image_tags_removed(self, converted_markdown):
        """HTML中的<img>标签不应出现在输出中。"""
        assert "<img" not in converted_markdown


# ── 降级测试（无NCX时走markitdown）────────────────────────────────


class TestFallback:
    def test_no_ncx_falls_back_to_markitdown(self, tmp_path):
        """EPUB 3（无NCX）应降级到 markitdown。"""
        import ebooklib
        from ebooklib import epub

        book = epub.EpubBook()
        book.set_identifier("fallback-test")
        book.set_title("Fallback Test")
        book.set_language("en")
        ch = epub.EpubHtml(title="Chapter", file_name="ch.xhtml", lang="en")
        ch.content = "<html><body><h1>Title</h1><p>Content</p></body></html>"
        book.add_item(ch)
        book.add_item(epub.EpubNav())
        book.spine = ["nav", ch]

        epub_path = tmp_path / "no_ncx.epub"
        epub.write_epub(str(epub_path), book)

        # 应该不报错，走 markitdown 路径
        md = convert_to_markdown(epub_path)
        assert "Title" in md
        assert "Content" in md


# ── 保存功能测试 ─────────────────────────────────────────────────


class TestSaveOutput:
    def test_save_with_title(self, mock_epub, converted_markdown, tmp_path):
        sources_dir = tmp_path / "sources"
        sources_dir.mkdir()
        md_path = save_markdown(converted_markdown, mock_epub, sources_dir, title="MySQL是怎样运行的")
        content = md_path.read_text(encoding="utf-8")
        assert content.startswith("# MySQL是怎样运行的")
        assert "# 第1章 MySQL入门" in content
