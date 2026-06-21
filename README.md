# teach-me-skill

一个 Claude Code Skill，基于用户自己的学习资料，通过持续对话进行教学。

## 功能特点

- 支持上传 PDF、Markdown、办公文档等学习资料
- 自动转换为 Markdown 并生成章节大纲
- 对话式教学：讲解、练习、反馈、补救
- 支持自定义教师风格（严师型、伙伴型、苏格拉底型、务实型，或选择历史人物/角色）
- 学习进度追踪和笔记管理
- 掌握评估和补救教学

## 安装

### 方式一：克隆仓库

```bash
git clone https://github.com/jiran214/teach-me-skill.git ~/.claude/skills/teach-me
```

### 方式二：手动安装

1. 下载或复制整个 `teach-me` 文件夹
2. 放置到 `~/.claude/skills/` 目录下

安装后目录结构：

```
~/.claude/skills/teach-me/
├── SKILL.md
├── references/
│   ├── source-ingestion.md
│   └── teacher-styles.md
├── scripts/
│   ├── convert_source.py
│   └── build_outline.py
└── ...
```

## 使用方法

1. 在 Claude Code 中，进入你想作为学习工作区的目录
2. 上传你的学习资料（PDF、Markdown 等）
3. 输入 `/teach-me` 启动教学

### 首次使用

首次使用时，Skill 会引导你完成以下设置：

- **创建 MISSION.md**：定义你的学习目标、成功标准和约束条件
- **选择教师风格**：从严师型、伙伴型、苏格拉底型、务实型中选择，或指定一个历史人物/作品角色
- **创建 TEACHER.md**：保存你的教师人设配置

### 学习流程

1. 上传学习资料 → 自动转换为 Markdown 并生成大纲
2. 开始对话教学 → AI 根据大纲章节逐步讲解
3. 完成练习 → AI 评估掌握程度并提供反馈
4. 进度追踪 → 学习进度记录在 NOTES.md 中

### 工作区结构

```
your-workspace/
├── MISSION.md          # 学习使命和目标
├── TEACHER.md          # 教师人设配置
├── NOTES.md            # 学习笔记和进度
├── sources/            # 学习资料源文件
│   ├── book.md         # 转换后的 Markdown
│   └── outline.md      # 章节大纲
├── learning-records/   # 学习记录
│   └── 0001-slug.md
└── assets/             # 辅助资产
    ├── images/
    ├── diagrams/
    ├── html/
    └── scripts/
```

## 依赖要求

- Python 3.10+
- PyMuPDF（`pip install pymupdf`）

## 许可证

本项目采用 [GNU Affero General Public License v3.0](LICENSE) 许可。
