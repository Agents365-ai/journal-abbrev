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

### Claude Code

```bash
# 全局安装
git clone https://github.com/Agents365-ai/journal-abbrev.git ~/.claude/skills/journal-abbrev

# 项目级安装
git clone https://github.com/Agents365-ai/journal-abbrev.git .claude/skills/journal-abbrev
```

### OpenClaw

```bash
git clone https://github.com/Agents365-ai/journal-abbrev.git ~/.openclaw/skills/journal-abbrev
```

### SkillsMP

在 [skillsmp.com](https://skillsmp.com) 搜索 `journal-abbrev` 并安装。

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

# 模糊搜索
python3 jabbrv.py search "biolog chem"

# 处理 BibTeX 文件
python3 jabbrv.py bib refs.bib

# 批量查询（每行一个期刊名）
python3 jabbrv.py batch journals.txt

# 更新本地缓存
python3 jabbrv.py update-cache
```

所有命令均支持 `--json` 参数输出 JSON 格式。

## 依赖

- Python 3.6+（无需安装第三方包）

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
