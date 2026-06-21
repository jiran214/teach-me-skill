**Claude Skill = 给 Claude 的“专项工作手册”**：一个文件夹，里面有 `SKILL.md`、参考资料、脚本、模板，让 Claude 在特定任务中自动加载对应流程。官方定义里，Skill 是可动态加载的 instructions / scripts / resources，用来处理特定任务。

---

## 官方最核心原则：渐进式加载

不要把所有内容都塞进主提示词。

Claude Skill 的加载逻辑是：

```txt
启动时：只读 skill 名称和 description
触发时：读取完整 SKILL.md
需要时：再读取 references / scripts / assets
```

官方把这叫 **progressive disclosure**，目的是避免上下文窗口被大量规则撑爆。

所以 Skill 应该这样设计：

```txt
SKILL.md：只放核心流程、触发说明、文件导航
references/：放详细文档
examples/：放案例
scripts/：放可执行脚本
assets/：放模板、图片、数据
```

---

## 最佳实践总结

### 1. 一个 Skill 只解决一个重复任务

官方建议 Skill 要解决**具体、可重复**的任务，并且聚焦一个 workflow，而不是试图什么都做。

好的例子：

```txt
git-commit-message
pdf-form-fill
ui-review
api-design-conventions
wechat-miniprogram-code-review
```

不好的例子：

```txt
coding-helper
project-helper
document-processing
ai-assistant
```

原因：大而全的 Skill 容易误触发，也难维护。

---

### 2. `description` 最重要

`description` 不是简介，而是**触发器**。

Claude 会用它判断什么时候加载 Skill。官方明确说 description 应该说明“做什么”和“什么时候用”，而且要把关键用例放前面。description必须使用纯英文。

推荐写法：

```yaml
---
name: wechat-miniprogram-review
description: Review WeChat Mini Program code for WXML, WXSS, setData performance, routing, login, request domain, and common mini program pitfalls.
---
```

不推荐：

```yaml
description: 小程序相关技能
```

更好的写法要包含用户可能说的关键词：

```txt
微信小程序
WXML
WXSS
setData
登录
wx.request
分包
审核
性能
```

官方排查 Skill 不触发时，也首先建议检查 description 是否包含用户自然会说的关键词。

---

### 3. `SKILL.md` 要短，细节外置

Claude Code 官方建议：**保持 SKILL.md 简洁**，因为 Skill 一旦加载，它的内容会在后续上下文中持续占用 token。官方还建议 `SKILL.md` 控制在 **500 行以内**，详细材料移动到独立文件。

推荐结构：

```txt
my-skill/
├── SKILL.md
├── references/
│   └── api-rules.md
├── examples/
│   └── good-output.md
├── scripts/
│   └── validate.py
└── templates/
    └── report-template.md
```

`SKILL.md` 里写：

```md
## Resources

- 详细 API 规则看 references/api-rules.md
- 输出示例看 examples/good-output.md
- 需要校验时运行 scripts/validate.py
```

这样 Claude 只有需要时才读。

---

### 4. 先写 Markdown，再加脚本

官方建议 **Start simple**：先用 Markdown 指令实现，确认有效后再加 scripts。

适合脚本处理的部分：

```txt
格式转换
校验
批量扫描
读取文件结构
生成图表
检查依赖
构建报告
```

不适合让模型纯生成的事，尽量交给脚本。Anthropic 工程博客也提到，排序、解析、PDF 字段提取这类确定性任务，用代码比让模型“想出来”更可靠、更省 token。

---

### 5. 写“步骤”，不要写散文

官方建议 Skill 内容要写“做什么”，不要长篇解释“为什么”。

推荐：

```md
## Workflow

1. Read the changed files.
2. Identify UI, state, and API changes.
3. Check for risky patterns.
4. Suggest minimal fixes.
5. Output in this format:
   - Summary
   - Risks
   - Fixes
```

不推荐：

```md
你是一个非常优秀的高级工程师，你需要认真思考项目的架构意义……
```

Skill 更像 SOP，不是角色扮演提示词。

---

### 6. 明确什么时候自动触发，什么时候只能手动触发

Claude Code 支持：

```yaml
disable-model-invocation: true
```

意思是：**Claude 不会自动调用，只能你手动 `/skill-name` 调用。**

官方建议有副作用的任务，比如部署、提交、发消息，应该设置成手动触发，避免 Claude 自己判断“可以部署了”。([Claude API Docs][3])

适合自动触发：

```txt
代码规范
UI 检查
文档格式
API 约定
小程序坑点检查
```

适合手动触发：

```txt
deploy
commit
send-message
release
publish
delete-files
```

---

### 7. 用测试驱动 Skill 迭代

官方工程博客建议：先用代表性任务观察 Claude 哪里失败，再增量构建 Skill，而不是一开始写一个很大的 Skill。

测试方法：

```txt
1. 准备 3-5 个真实任务
2. 不开 Skill 跑一次
3. 开 Skill 跑一次
4. 看是否更稳定、更少追问、更少犯错
5. 根据失败点修改 description / workflow / examples
```

Claude.ai 官方也建议上传前检查清晰度、description 是否准确、引用文件是否存在；上传后用应该触发的 prompt 测试，并根据结果迭代 description。

---

### 8. 不要把密钥、账号、私密信息写进 Skill

官方安全建议：

```txt
不要硬编码 API key / 密码
启用下载的 Skill 前先审查
外部服务访问尽量用 MCP
```

Anthropic 工程博客也提醒：恶意 Skill 可能引导 Claude 泄露数据或执行非预期操作，所以第三方 Skill 要审查脚本、依赖、资源和外部网络连接。

---

## 一个适合你的 Skill 模板

比如你可以做一个 **微信小程序开发 Skill**：

```txt
.claude/skills/wechat-miniprogram-dev/
├── SKILL.md
├── references/
│   ├── miniapp-pitfalls.md
│   ├── api-checklist.md
│   └── review-rules.md
├── examples/
│   └── review-output.md
└── scripts/
    └── scan-miniapp.js
```

`SKILL.md` 可以这样写：

```md
---
name: wechat-miniprogram-dev
description: Use for WeChat Mini Program development, WXML, WXSS, setData, wx.request, routing, login, package size, review, debugging, and mini program performance checks.
---

# WeChat Mini Program Development

Use this skill when working on WeChat Mini Program code.

## Workflow

1. Identify whether the task involves WXML, WXSS, JS/TS, app.json, page routing, login, request, or cloud functions.
2. Check for common mini program pitfalls:
   - excessive setData
   - missing request domain configuration
   - large package size
   - incorrect lifecycle usage
   - unsafe user info handling
   - weak error handling
3. Prefer small, direct code changes.
4. Explain differences from normal web development when relevant.

## Resources

- For common pitfalls, read references/miniapp-pitfalls.md
- For review checklist, read references/review-rules.md
- For output format, read examples/review-output.md
```

---
