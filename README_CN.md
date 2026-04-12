# Journal Abbrev — 期刊名称缩写查询技能

[English](README.md)

一个用于查询期刊/杂志名称标准缩写的 Claude Code 技能。支持 ISO 4 和 MEDLINE 两种缩写标准，覆盖 25,000+ 期刊。

## 功能特性

| 功能 | 原生 Claude Code | Journal Abbrev |
|------|-----------------|----------------|
| 期刊名缩写查询 | 需要手动猜测 | 多源级联查询，结果准确 |
| 缩写反查全名 | 不支持 | 双向查询 |
| BibTeX 批量处理 | 不支持 | 自动替换 journal 字段 |
| 模糊搜索 | 不支持 | 支持部分名称匹配 |
| 离线查询 | 不支持 | 本地缓存 25K+ 期刊 |

## 数据来源

1. **JabRef 数据库** — 25,000+ 期刊，CC0 开源，首次运行自动下载
2. **AbbrevISO API** — 基于 LTWA 的 ISO 4 算法缩写（正向查询）
3. **NLM Catalog** — 生物医学期刊双向查询（MEDLINE 标准）

## 安装

`jabbrv` 是一个 **agent-native CLI** —— 输出稳定的 JSON 信封、提供 `schema`
自描述子命令、使用不同退出码区分错误类别。这意味着所有 AI 智能体平台都使用完全
相同的调用方式（`python3 jabbrv.py <cmd>`）。各平台之间唯一的区别是
*智能体如何发现这个工具的存在*。根据你的平台选择下面对应的层级即可。

### 层级 1 —— 原生支持 `SKILL.md` 的平台

这些平台会自动加载 `SKILL.md`，无需额外配置文件。

| 平台 | 安装命令 |
|---|---|
| **Claude Code**（全局） | `git clone https://github.com/Agents365-ai/journal-abbrev.git ~/.claude/skills/journal-abbrev` |
| **Claude Code**（项目） | `git clone https://github.com/Agents365-ai/journal-abbrev.git .claude/skills/journal-abbrev` |
| **OpenClaw**（全局） | `git clone https://github.com/Agents365-ai/journal-abbrev.git ~/.openclaw/skills/journal-abbrev` |
| **OpenClaw**（项目） | `git clone https://github.com/Agents365-ai/journal-abbrev.git skills/journal-abbrev` |
| **ClawHub** | `clawhub install journal-abbrev` |
| **SkillsMP** | 在 [skillsmp.com](https://skillsmp.com) 搜索 `journal-abbrev` |

### 层级 2 —— 支持 `AGENTS.md` 约定的平台

这些平台遵循 [`agents.md`](https://agents.md) 规范，会自动发现仓库根目录下的
`AGENTS.md`。克隆到任意位置，告诉智能体从该路径使用此工具即可——其余工作由
`AGENTS.md` 文件完成。

| 平台 | 说明 |
|---|---|
| **OpenAI Codex CLI** | `AGENTS.md` 是其原生约定 |
| **Gemini CLI** | 在没有 `GEMINI.md` 时会回退到 `AGENTS.md` |
| **Claude Code** | 在没有 `CLAUDE.md` 时会回退到 `AGENTS.md`（更推荐层级 1 的方式） |
| **Cursor**（近期版本） | 在没有 `.cursor/rules` 时会识别 `AGENTS.md` |
| **Aider** | 将 `AGENTS.md` 识别为项目约定 |
| **其他支持该约定的智能体** | 自动生效 |

项目级安装示例：

```bash
git clone https://github.com/Agents365-ai/journal-abbrev.git vendor/journal-abbrev
# 在下一次智能体会话中指向 vendor/journal-abbrev/AGENTS.md，
# 或直接告诉智能体："使用 vendor/journal-abbrev 中的 journal-abbrev 工具"
```

### 层级 3 —— 使用自定义规则文件的平台

对于使用自有规则文件约定的智能体，在规则文件中加入一行指向 `AGENTS.md` 的引用
即可，避免重复编写内容。

| 平台 | 编辑的文件 | 加入的片段 |
|---|---|---|
| **GitHub Copilot Chat** | `.github/copilot-instructions.md` | `See ./vendor/journal-abbrev/AGENTS.md for how to use the journal-abbrev tool.` |
| **Continue.dev** | `.continue/config.yaml` 的 `systemMessage:` 字段 | `"For journal abbreviation tasks, follow vendor/journal-abbrev/AGENTS.md."` |
| **Windsurf** | `.windsurfrules` | `When the user asks about journal abbreviations, use vendor/journal-abbrev/AGENTS.md.` |
| **Cursor**（旧版） | `.cursor/rules/journal-abbrev.mdc` | 一行规则，指向 `vendor/journal-abbrev/AGENTS.md` |

### 层级 4 —— 手动调用 / 任意 Shell

没有智能体？没有规则文件？CLI 本身是自包含的，克隆到任意位置直接运行即可：

```bash
git clone https://github.com/Agents365-ai/journal-abbrev.git
cd journal-abbrev
python3 jabbrv.py lookup "Nature Medicine"
python3 jabbrv.py schema              # 完整机器可读契约
```

纯 Python 3.9+ 标准库实现——无需 `pip install`、无需虚拟环境、无第三方依赖。
在 macOS、Linux 和 Windows 上均可运行。

## 使用方法

### 自然语言

直接向 Claude 提问：

- "Nature Medicine 的缩写是什么？"
- "J. Biol. Chem. 是哪个期刊？"
- "帮我把 refs.bib 里的期刊名都改成缩写"
- "查一下 biolog chem 相关的期刊"

### 命令行

```bash
# 自动检测方向
python3 jabbrv.py lookup "Nature Medicine"

# 全名 → 缩写
python3 jabbrv.py abbrev "Journal of Biological Chemistry"

# 缩写 → 全名
python3 jabbrv.py expand "Nat. Med."

# 模糊搜索（支持分页）
python3 jabbrv.py search "biolog chem" --limit 10 --offset 0

# 处理 BibTeX 文件（先预览再写入）
python3 jabbrv.py bib refs.bib --dry-run
python3 jabbrv.py bib refs.bib --output refs_final.bib

# 批量查询（每行一个期刊名）
python3 jabbrv.py batch journals.txt
python3 jabbrv.py batch journals.txt --stream   # NDJSON 流式输出

# 缓存管理
python3 jabbrv.py cache status     # 查看本地缓存状态
python3 jabbrv.py cache update     # 下载缺失的缓存文件
python3 jabbrv.py cache rebuild    # 删除并重新下载全部缓存

# 机器可读的命令契约（供 AI 智能体或自动化工具使用）
python3 jabbrv.py schema
python3 jabbrv.py schema lookup
```

### Agent-native 输出契约

当标准输出不是终端（例如被管道捕获、被智能体运行时读取）时，`stdout` 默认输出
稳定的 JSON 信封；在终端下则输出人类友好的表格或缩进视图。所有响应共用同一信封结构：

- 成功: `{"ok": true, "data": ..., "meta": {"schema_version", "cli_version", "cache", "latency_ms"}}`
- 部分成功（batch）: `{"ok": "partial", "data": {"succeeded": [...], "failed": [...]}}`
- 错误: `{"ok": false, "error": {"code", "message", "retryable", ...}}`

退出码按失败类别区分：`0` 成功、`1` 运行时错误、`2` 参数/输入错误、`3` 未找到。
可用 `--format json|table|human` 强制格式（`--json` 是旧版兼容别名）；
所有全局参数可以放在子命令前或后。

## 依赖

- Python 3.9+（无需安装第三方包）

## 支持作者

如果这个项目对你有帮助，欢迎支持作者：

<table>
  <tr>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/wechat-pay.png" width="180" alt="微信支付">
      <br>
      <b>微信支付</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/alipay.png" width="180" alt="支付宝">
      <br>
      <b>支付宝</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/buymeacoffee.png" width="180" alt="Buy Me a Coffee">
      <br>
      <b>Buy Me a Coffee</b>
    </td>
  </tr>
</table>

## 作者

**Agents365-ai**

- B站: https://space.bilibili.com/441831884
- GitHub: https://github.com/Agents365-ai

## 许可证

MIT
