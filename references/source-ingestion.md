# 资料导入

处理用户提供的学习材料或修改导入流程时参考本文档。

## 默认流程

1. 将原始文件放入 `sources/`。
2. 使用 `scripts/convert_source.py` 将文档转换为 Markdown 并保存。
3. 使用 `scripts/build_outline.py` 基于 Markdown 生成 outline（含行号索引）。
4. 教学前先查看 `sources/outline.md`。
5. 通过 outline 中的行号链接，用 `Read(source.md, offset, limit)` 读取源文件的相关章节。禁止完整读取源文件，必须按行读取。行数范围以 outline 章节行号为锚点，根据上下文灵活扩展，确保语义完整。

## 导入脚本

### 步骤1：转换文件

在用户学习工作区中运行：

```bash
python {SKILL_DIR}/scripts/convert_source.py ./path/to/file.pdf --workspace "{WORKSPACE}"
```

可选指定标题：

```bash
python {SKILL_DIR}/scripts/convert_source.py ./path/to/file.pdf --title "书名" --workspace "{WORKSPACE}"
```

处理多个文件：

```bash
python {SKILL_DIR}/scripts/convert_source.py file1.pdf file2.docx --workspace "{WORKSPACE}"
```

脚本会将原始文件复制到 `sources/`，同时生成对应的 `.md` 文件。

### 步骤2：生成 outline

```bash
python {SKILL_DIR}/scripts/build_outline.py --workspace "{WORKSPACE}"
```

默认处理 `sources/` 目录下所有 `.md` 文件。也可以指定特定文件：

```bash
python {SKILL_DIR}/scripts/build_outline.py sources/file1.md sources/file2.md --workspace "{WORKSPACE}"
```

生成的 `sources/outline.md` 包含章节标题及其在源文件中的行号，格式如：

```markdown
# 书名

- [第一章 标题](sources/file.md#L10)
  - [1.1 小节](sources/file.md#L25)
- [第二章 标题](sources/file.md#L50)
```

## 基于资料教学

不要仅因为资料库存在就加载全部内容。从 `sources/outline.md` 出发，识别相关章节，通过行号链接读取源文件对应段落。严禁一次性读取整个源文件，始终使用 `Read(source.md, offset, limit)` 按需读取。

如果资料内容缺失、矛盾或可能过时：

- 说明已有资料覆盖了什么、没覆盖什么。
- 除非用户已要求补充，否则使用外部材料前应先询问。
- 将基于资料的教学与外部补充明确区分。
