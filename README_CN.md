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

技能本体位于 `skills/journal-abbrev/`（包含 `SKILL.md` 和 `jabbrv.py`）。
推荐通过插件市场安装，会自动处理升级：

```bash
# Claude Code 插件市场（推荐）
/plugin marketplace add Agents365-ai/365-skills
/plugin install journal-abbrev

# 任意 Agent（Claude Code、Cursor、Copilot 等）
npx skills add Agents365-ai/365-skills -g
```

也发布在 [ClawHub](https://clawhub.ai/) 与 [SkillsMP](https://skillsmp.com)
上 —— 各自的市场都会处理升级。

也可以手动把 skill bundle 安装到任意支持 `SKILL.md` 的平台：

| 平台 | 安装命令 |
|---|---|
| **Claude Code**（全局） | `git clone https://github.com/Agents365-ai/journal-abbrev.git /tmp/ja && cp -r /tmp/ja/skills/journal-abbrev ~/.claude/skills/ && rm -rf /tmp/ja` |
| **Claude Code**（项目） | `git clone https://github.com/Agents365-ai/journal-abbrev.git /tmp/ja && cp -r /tmp/ja/skills/journal-abbrev .claude/skills/ && rm -rf /tmp/ja` |
| **OpenClaw**（全局） | 把上面命令里的 `~/.claude/skills/` 换成 `~/.openclaw/skills/` |

或者直接克隆仓库运行 CLI —— 纯 Python 3.9+ 标准库实现，
无任何第三方依赖，在 macOS、Linux、Windows 上均可运行：

```bash
git clone https://github.com/Agents365-ai/journal-abbrev.git
cd journal-abbrev/skills/journal-abbrev
python3 jabbrv.py lookup "Nature Medicine"
python3 jabbrv.py schema              # 完整机器可读的 CLI 契约
```

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
python3 jabbrv.py bib refs.bib --idempotency-key run-001   # 可安全重试

# 批量查询（每行一个期刊名）
python3 jabbrv.py batch journals.txt
python3 jabbrv.py batch journals.txt --stream   # NDJSON 流式输出

# 缓存管理
python3 jabbrv.py cache status                # 查看本地缓存状态
python3 jabbrv.py cache update                # 下载缺失的缓存文件
python3 jabbrv.py cache update --dry-run      # 预览将下载哪些文件
python3 jabbrv.py cache rebuild --yes         # 原子破坏性刷新（带审计标记）
python3 jabbrv.py cache rebuild --dry-run     # 预览将删除哪些文件，不实际写入

# 抑制 stderr 进度（stdout 信封不受影响）
python3 jabbrv.py --quiet cache update

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

`error.code` 字段稳定。主要的错误码：

| 错误码 | 可重试 | 退出码 | 含义 |
|--------|--------|--------|------|
| `not_found` | 否 | 3 | 查询完成，但所有数据源都未命中 |
| `upstream_unavailable` | **是** | 1 | 至少一个上游 API（AbbrevISO、NLM）瞬时失败。`error.sources[]` 列出每个失败源 —— 稍后重试 |
| `file_not_found` / `validation_error` | 否 | 2 | 输入不合法 |
| `runtime_error` | 是 | 1 | 未预期的内部错误 |

请基于 `error.code` + `error.retryable` 来分支重试逻辑，不要只看退出码 —— 退出
`1` 同时覆盖瞬时错误和运行时错误。可用 `--format json|table|human` 强制格式
（`--json` 是旧版兼容别名）；所有全局参数可以放在子命令前或后。完整的机器可读
错误码列表：`python3 jabbrv.py schema` → `data.error_codes`。

### 智能体重试循环

按 `error.code` 与 `error.retryable` 分支：限定重试次数，瞬时失败时退避；
不要重试确定性的 miss 或校验错误。重试 `bib` 时复用 `--idempotency-key`，
信封会直接从缓存返回，无需重新执行：

```python
import json, subprocess, time

def jabbrv_bib(path, key, *, max_attempts=4):
    for attempt in range(1, max_attempts + 1):
        p = subprocess.run(
            ["python3", "jabbrv.py", "bib", path,
             "--idempotency-key", key, "--format", "json"],
            capture_output=True, text=True,
        )
        env = json.loads(p.stdout)
        if env["ok"] is True:
            return env  # 重放时 meta.idempotent_replay 为 True
        err = env["error"]
        if not err["retryable"] or attempt == max_attempts:
            raise RuntimeError(f"{err['code']}: {err['message']}")
        time.sleep(2 ** attempt)  # 指数退避
```

### 原子缓存重建

`cache rebuild` 把新一轮下载暂存到一个兄弟目录，只有当全部文件都下载成功
后才会原子替换。任何一个文件失败都会保留现有缓存，并返回
`error.code = upstream_unavailable`（可重试）。加上 `--yes` 会把
`meta.confirmed: true` 写入信封以便审计；CLI 本身从不交互式提问，所以
`--yes` 不是门槛，只是显式意图。

### 环境变量

由宿主/沙盒设置，而非由智能体通过 argv 传递 —— agent-native 设计中的信任边界：

| 变量 | 作用 |
|------|------|
| `JABBRV_CACHE_DIR` | 覆盖缓存目录（默认：`<安装目录>/cache`）。在安装目录只读、或需要按租户隔离时很有用。 |
| `JABBRV_OFFLINE` | 真值（`1`/`true`/`yes`/`on`）禁用 AbbrevISO 和 NLM，仅查询本地 JabRef 缓存。离线模式下查不到的结果直接返回 `not_found`（而非 `upstream_unavailable`），因为宿主已明确禁止访问上游。每个信封都会带上 `meta.offline: true`，让调用方能看到当前策略。 |
| `NO_COLOR` | 遵循 https://no-color.org 约定：任何非空值都禁用色彩。CLI 当前不输出 ANSI，但设置后 `meta.no_color: true` 会出现在信封里，方便调用方看到策略。 |

Schema 内省：`python3 jabbrv.py schema` → `data.global_env`。每个命令的安全
等级（`read` / `write` / `destructive`）通过 `data.commands.<name>.mutates`
暴露。

## 依赖

- Python 3.9+（无需安装第三方包）

## 💬 社区

- **Discord:** https://discord.gg/79JF5Atuk
- **微信:** 扫描下方二维码

<p align="center">
  <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/agents365ai_wechat_1.png" width="200" alt="微信交流群">
</p>

## ❤️ 支持

如果这个技能对你有帮助，欢迎打赏支持作者：

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
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/awarding/award.gif" width="180" alt="打赏">
      <br>
      <b>打赏</b>
    </td>
  </tr>
</table>

## 👤 作者

**Agents365-ai**

- GitHub: https://github.com/Agents365-ai
- B站: https://space.bilibili.com/441831884

## 📄 License

MIT
