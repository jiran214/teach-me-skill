## 项目简介
skill名称：teach-me
这是一个Agent Skill，skill位于`SKILL.md`

## 原skill地址
https://github.com/mattpocock/skills/tree/main/skills/productivity/teach

## 遵循skill最佳实践
`skill-rules.md`

## 注意
- 请勿操作全局skill
- 暂时不需要做任何测试
- PDF解析使用PyMuPDF，通过字体大小识别标题结构
- 脚本优先使用py、shell
- 优先兼容mac，其次windows
- 读取原文Markdown的时候，你应该只读前几行，因为这个文件过于大了。
- 测试都放到tests文件夹内