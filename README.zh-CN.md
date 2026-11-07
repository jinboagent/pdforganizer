# pdf_organizer（中文说明）

**语言 / Languages**: [English](README.md) · [中文](README.zh-CN.md) · [Español](README.es.md)

按**文件内容**整理一个文件夹里的 PDF：工具会提取每个 PDF 前几页的文本，把文档归入一个主题类别，可以把没有意义的文件名（纯数字、代码、乱码）改成文档的真实标题，并把所有文件移动到各类别的子文件夹中。

本工具在一个 10,500 个 PDF 的混合语料库上开发和长期实测（科研论文、技术书籍、手册、账单、试卷、小说，涵盖英文/中文/丹麦文）。

## 它做什么

1. **提取** — 对每个 PDF 提取元数据标题和前几页文本（默认 3 页）。每个文件在独立的子进程中提取，带硬超时，因此一个损坏或加密的 PDF 不会拖垮整个运行。结果会缓存，重复运行速度很快。
2. **分类** — 关键词打分引擎把每个文件与约 55 个主题类别比对。文件名和标题区里的证据比正文证据权重更高；大小写敏感的缩写（HRTF、FIR、ADC …）按原大小写精确匹配。什么都匹配不上（或几个类别得分相同）的文件会进入 `uncategorized` 文件夹，而不是乱猜。
3. **重命名**（可选） — 纯数字/代码/乱码的文件名会被替换为文档的真实标题，标题取自元数据或从首页版面提取（标题行、全大写标题串、arXiv/ResearchGate 标题模式）。本身就有意义的文件名不会被改动。中文文件名会被识别为"有意义"并保留。
4. **分组** — 文件被移动到每个类别一个的文件夹。默认结构是**扁平的**（类别文件夹里不再套子文件夹）。
5. **报告** — 在输出文件夹写入三个报告文件：`rename_report.txt`（旧名 → 新名）、`folder_manifest.txt`（最终布局）、`summary.txt`（各类别数量）。

任何文件都不会被删除。每次移动都记录在 `organize_log.json` 中，用 `--undo` 可以完全撤销一次运行。

## 环境要求

- Python 3.9+
- [PyMuPDF](https://pymupdf.readthedocs.io/)

```bash
pip install -r requirements.txt
```

文档：**[USAGE.zh-CN.md](USAGE.zh-CN.md)** 是手把手的实用指南；[README.zh-CN.md](README.zh-CN.md)（本文件）是选项参考；[SPECIFICATION.md](SPECIFICATION.md) 是正式规格说明（英文）。

测试：`python tests/test_organizer.py`（自包含，自动生成测试用的 PDF）。

## 快速上手

```bash
# 原地整理一个文件夹（输入 = 输出），带重命名
python pdf_organizer.py --input "E:\my_pdfs"

# 先看看"会"发生什么 —— 不会移动任何文件
python pdf_organizer.py --input "E:\my_pdfs" --dry-run

# 只分组进文件夹，不重命名任何文件
python pdf_organizer.py --input "E:\my_pdfs" --no-rename

# 撤销上一次运行 —— 日志会被自动找到
python pdf_organizer.py --undo

# 查看所有生效的类别
python pdf_organizer.py --list-categories
```

其他 CLI 参数：`--verbose`（输出各类别移动数量 + 重命名示例）、`--version`。只要有文件移动失败，进程就以退出码 1 结束。

使用配置文件（推荐，可使用全部选项）：

```bash
cp config.example.json myconfig.json   # 编辑它，然后：
python pdf_organizer.py --config myconfig.json
```

## 配置选项

| 选项（JSON） | CLI 参数 | 默认值 | 含义 |
|---|---|---|---|
| `input_folder` | `--input` | `.` | 存放待整理 PDF 的文件夹。 |
| `output_folder` | `--output` | 同输入 | 创建类别子文件夹的位置。**默认输入和输出是同一个文件夹**，即原地整理。设置不同的文件夹可保持输入原封不动。 |
| `recursive` | `--recursive` | `false` | 同时扫描输入文件夹的子文件夹。输出文件夹和提取缓存**永远不会**被递归进入，即使它们位于输入文件夹内部。 |
| `ignore` | `--ignore a b …` | `[]` | 要跳过的文件夹/文件的 glob 模式，例如 `["private", "*_backup", "invoices"]`。匹配任意路径段或相对路径。 |
| `rename_files` | `--no-rename` 关闭 | `true` | 把无意义的文件名重命名为文档标题。`false` = 保留所有现有名称，只分组进文件夹。 |
| `dry_run` | `--dry-run` | `false` | 计算并打印完整计划（同时保存到 `.pdf_organizer_cache/plan_preview.txt`），不移动任何文件。 |
| `nested` | `--nested` | `false` | 允许**在**类别文件夹内部再建子文件夹（见 `subfolder_by`）。 |
| `subfolder_by` | — | `"none"` | `"none"` = 扁平类别文件夹。`"first_letter"`（需要 `nested: true`）= 每个类别按 `A/ … Z/` 拆分子文件夹。 |
| `uncategorized_folder` | — | `uncategorized` | 无法分类的文件进入的文件夹名。 |
| `work_folder` | — | `.pdf_organizer_cache` | 提取结果的缓存目录（让重复运行变快）。 |
| `workers` | `--workers N` | `8` | 并行提取的子进程数。 |
| `extract_timeout_sec` | — | `45` | 提取阶段每个 PDF 的硬超时。 |
| `max_pages` | — | `3` | 每个 PDF 提取文本的页数。 |
| `log_file` | — | `organize_log.json` | 写到输出文件夹的撤销日志（设为 `null` 关闭）。 |
| `reports.enabled` | — | `true` | 是否写三个报告文件。 |
| `reports.rename_report` / `reports.manifest` / `reports.summary` | — | `rename_report.txt` / `folder_manifest.txt` / `summary.txt` | 报告文件名（相对输出文件夹）。 |
| `classifier.min_score` | — | `2.0` | 接受一个类别的最低证据分。 |
| `classifier.min_margin` | — | `0.5` | 最佳类别与次佳类别之间要求的分差；调小 = 更果断，调大 = 更多文件留在 uncategorized。 |
| `classifier.custom_categories` | — | `[]` | 你自己的类别，**先于**内置类别检查。示例如下。 |
| `classifier.disable_categories` | — | `[]` | 要关闭的内置类别名（其中的文件改归其他类别或 uncategorized）。 |

## 示例

### 1. 原地整理（本工具的初衷）

```json
{
  "input_folder": "E:\\pdf_regroup",
  "output_folder": "E:\\pdf_regroup",
  "rename_files": true
}
```

输入和输出是同一个文件夹：一大堆扁平的 PDF 变成一组主题文件夹，命名糟糕的文件拿到真实标题。

### 2. 独立的输出文件夹，保留原名，忽略部分文件夹

```json
{
  "input_folder": "C:\\Users\\me\\Downloads",
  "output_folder": "D:\\library",
  "rename_files": false,
  "recursive": true,
  "ignore": ["*.tmp", "family_photos", "invoices_*"]
}
```

读取 Downloads **及其子文件夹**里的 PDF，跳过匹配 ignore 模式的内容，把副本归类到 `D:\library\<category>\`（不重命名），Downloads 文件夹原封不动。

### 3. 大型收藏：按首字母嵌套子文件夹

```json
{
  "input_folder": "E:\\papers",
  "nested": true,
  "subfolder_by": "first_letter"
}
```

生成 `E:\papers\noise_reduction\A\`、`…\B\`……这样单个文件夹里不会有几千个文件。

### 4. 自定义类别

```json
{
  "input_folder": "E:\\work_docs",
  "classifier": {
    "custom_categories": [
      { "name": "company_reports",
        "keywords": ["acme corp", "quarterly report", "ACME-202"],
        "weak_keywords": ["acme"] }
    ]
  }
}
```

提到 "acme corp" 等关键词的文件会直接进入 `company_reports` 文件夹，内置类别根本不会被考虑。

### 5. 先 dry-run（推荐）

```bash
python pdf_organizer.py --input "E:\my_pdfs" --dry-run
# 检查 .pdf_organizer_cache/plan_preview.txt，然后：
python pdf_organizer.py --input "E:\my_pdfs"
```

### 6. 撤销一次运行

```bash
python pdf_organizer.py --undo              # 自动查找 organize_log.json
# 或显式指定：
python pdf_organizer.py --undo "E:\my_pdfs\organize_log.json"
```

把每个文件恢复到原始路径，并删除这次运行创建的文件夹。

## 类别体系

默认规则编码了一套通用的知识分类标准：它来自本项目对一座真实的 10,500 PDF 混合图书馆（科研论文、教材、手册、个人行政文档、账单、小说；英文/中文/丹麦文）的整理实践，并在其上长期实测。覆盖的主题领域包括音频与语音处理、DSP 与数学、编程与计算机、个人行政事务（账单、银行/税务、旅行预订、证件）以及一般阅读材料等。

你不需要事先掌握完整清单：

- 随时查看当前生效的全部类别：`--list-categories`。
- 整个类别方案集中在一个文件 `organizer/rules.py`，想改造就从它入手。
- 通过 `classifier.custom_categories` / `classifier.disable_categories` 添加自己的主题或停用内置类别（见上文示例）。
- 报告和 `--list-categories` 会为每个类别标注其**美国国会图书馆分类（LCC）**顶级大类和 **arXiv** 学科领域 —— 工具的类别体系与人类标准知识分类保持对应（`organizer/schemes.py`）。个人实务文件（账单、证件、预订）在任何图书馆/科学体系中都没有对应类，标注留空。

## 注意事项与局限

- 分类基于关键词证据：速度快且完全离线，但如果文档前几页没有任何可识别的主题关键词，就会进入 `uncategorized`（调整 `min_score` / `min_margin`，或添加自定义类别）。
- 扫描版/纯图片 PDF 没有可提取的文本；只能按文件名证据分组。
- 损坏或加密的 PDF 仍会被移动（到 `uncategorized`），但无法根据内容重命名。
- 同一盘符内的移动是瞬间完成的；跨盘符则先复制后删除。
- 提取缓存（`.pdf_organizer_cache/`）可以安全删除；下次运行时会重建。

## 目录结构

```
pdf_organizer/
├── pdf_organizer.py        # CLI 入口
├── config.example.json     # 带注释的默认配置
├── requirements.txt
├── USAGE.md                # 手把手实用指南（英文）
├── USAGE.zh-CN.md          # 实用指南（中文）
├── SPECIFICATION.md        # 软件规格（需求、算法、数据格式，英文）
├── tests/
│   └── test_organizer.py   # 自包含测试程序
└── organizer/
    ├── config.py           # 配置加载/校验
    ├── rules.py            # 内置类别方案
    ├── extract.py          # 并行、带超时保护的提取驱动
    ├── _extract_worker.py  # 单 PDF 提取子进程
    ├── classify.py         # 打分分类器
    ├── rename.py           # 无意义文件名检测 + 标题提取
    ├── schemes.py          # LCC / arXiv 标准知识分类代码
    ├── executor.py         # 计划/执行/撤销
    └── report.py           # 三个报告文件
```
