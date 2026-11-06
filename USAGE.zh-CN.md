# pdf_organizer — 使用指南（中文）

**语言 / Languages**: [English](USAGE.md) · [中文](USAGE.zh-CN.md) · [Español](USAGE.es.md)

[README](README.zh-CN.md)（选项参考）和 [SPECIFICATION](SPECIFICATION.md)（正式细节，英文）的实用补充。这一页讲的是*日常实际怎么用好这个工具*。

---

## 1. 一句话说明

把一个装满 PDF 的文件夹交给它。它读取每个文件的前几页，判断每份文档讲什么，给无名文件（`12345.pdf`、`scan_final.pdf`、乱码）补上真实标题，然后把所有文件归入 `noise_reduction/`、`programming_python/`、`bills_utilities/` 这样的主题文件夹。不删除任何东西，每次移动都有记录，整个运行可以撤销。

## 2. 五分钟上手

```bash
pip install pymupdf

# 第 1 步 —— 先看后动（不移动任何文件）：
python pdf_organizer.py --input "D:\Messy PDFs" --dry-run

# 第 2 步 —— 读它打印出来的计划（同时保存在 .pdf_organizer_cache/plan_preview.txt）

# 第 3 步 —— 真正执行：
python pdf_organizer.py --input "D:\Messy PDFs"

# 第 4 步 —— 后悔了？一条命令全部还原：
python pdf_organizer.py --undo
```

整个流程就这么简单。本指南其余部分讲的是怎么把它用*好*。

## 3. 推荐的安全工作流

第一次在重要文件夹上运行时：

1. **复制，别冒险。** 要么用独立的输出文件夹运行（`--input 输入 --output 输出`，输入文件夹原封不动），要么先备份。或者信任 `--undo` —— 它是精确且经过测试的，但备份永远比后悔便宜。
2. **先 dry-run。** 看类别表。`uncategorized` 里出现*一些*文件是正常的 —— 那是工具在诚实行事，不是坏了（见 §7）。
3. **正式运行。** 记下打印出来的 `Undo log:` 路径。
4. **检查结果** —— 看 `rename_report.txt`（旧名 → 新名）和 `folder_manifest.txt`（每个文件去了哪）。
5. **迭代。** 有文件分错类？加一个自定义类别或调整阈值（§6），再跑一次 —— 提取缓存让重复运行很快，而且第二次只有*放错位置*的文件会动。

## 4. 日常场景

### "我的 PDF 是一大堆平铺的文件 —— 原地整理"

```bash
python pdf_organizer.py --input "E:\papers" --dry-run
python pdf_organizer.py --input "E:\papers"
```

输入和输出默认是同一个文件夹：一堆文件变成主题文件夹，坏名字变成真实标题。

### "把副本整理进一个资料库文件夹，保留我的原件和原文件名"

```bash
python pdf_organizer.py --input "C:\Users\me\Downloads" --output "D:\library" --no-rename --recursive
```

### "我的 Downloads 文件夹有些东西永远不想被碰"

```bash
python pdf_organizer.py --input "D:\In" --output "D:\Out" --recursive --ignore private receipts_*
```

（或者把同样的模式写进 `config.json` 的 `"ignore"`。）

### "我有 20,000 个 PDF，文件夹会大到没法用"

```bash
python pdf_organizer.py --input "E:\big" --nested
```

每个类别文件夹按首字母拆分：`noise_reduction/A/`、`noise_reduction/B/`……

### "我的领域有工具不认识的主题"

```json
{
  "input_folder": "E:\\thesis_chapters",
  "classifier": {
    "custom_categories": [
      { "name": "bicycle_dynamics",
        "keywords": ["bicycle dynamics", "wheel gyroscopic"],
        "weak_keywords": ["bicycle"] }
    ],
    "disable_categories": ["danish_education"]
  }
}
```

```bash
python pdf_organizer.py --config myconfig.json
```

自定义类别与内置类别打平时会胜出。查看当前所有生效的类别：

```bash
python pdf_organizer.py --list-categories
```

### "我会不断往文件夹里加新 PDF"

直接重跑同一条命令。提取结果有缓存，所以只有新文件会被读取，也只有*它们*会移动。工具也绝不会打乱自己已整理好的结果 —— 递归扫描会自动跳过输出文件夹和缓存。

### "我只想重命名，不要文件夹"（或反过来）

- 只重命名、文件都留在原地：这不是本工具的工作（它总是会分组）。
- 分组但不重命名：`--no-rename`。

## 5. 看懂输出

| 文件 | 内容 |
|---|---|
| 控制台 | 运行前的类别计划；运行后的移动/出错数量 |
| `rename_report.txt` | 每个被重命名的文件：旧名 → 新名，按文件夹分组 |
| `folder_manifest.txt` | 完整的最终布局 —— 每个 PDF 最后在哪 |
| `summary.txt` | 各类别数量 |
| `organize_log.json` | 机器可读的移动日志（`--undo` 使用） |
| `.pdf_organizer_cache/` | 提取缓存 + dry-run 生成的 `plan_preview.txt`。可安全删除。 |

## 6. 调整分类器

- **`uncategorized` 里的文件太多？** 降低证据门槛：`"classifier": { "min_score": 1.5, "min_margin": 0.3 }`。或者为你的主题添加自定义类别。或者调大 `max_pages`（默认 3）让工具读更多文本。
- **文件落到了错误的类别？** 调大 `min_margin`（如 `1.0`），只接受优势明显的胜者；在 `folder_manifest.txt` 里查看是哪个类别在"抢"它们；添加一个更具体的自定义类别 —— 自定义类别先于内置类别检查。
- **某个你永远用不到的类别在抢文件？** 停用它：`"classifier": { "disable_categories": ["fiction"] }`。

## 7. 故障排查

| 症状 | 原因与解决 |
|---|---|
| `uncategorized/` 里文件很多 | 扫描版/纯图片 PDF 没有文本可读（无 OCR）；或者前几页没有主题关键词。见 §6。 |
| 某个文件没有被重命名 | 它的文件名本来就被判定为有意义，或者文本中找不到可信的标题。手动重命名即可 —— 工具从不动它不确定的名字。 |
| `broken.pdf` 之类的文件落进了 `uncategorized/` | 损坏或加密；仍会被移动，但读不了。修复文件后重跑。 |
| Windows 上报"文件被占用" | 有查看器打开着文件。关掉后重跑 —— 缓存的提取结果让重试很便宜。 |
| 重跑后什么都没发生 | 早已整理完毕，计划为空。这是成功，不是失败。 |
| 撤销时提示 "No organize_log.json found" | 显式传路径：`--undo "D:\Out\organize_log.json"` —— 日志在这次运行的**输出**文件夹里。 |

## 8. 好习惯

- 一个文件夹，一个用途：不要把 `--recursive` 指向一个什么都有的大文件夹（比如整个用户目录）—— 你会把自己没想整理的东西也整理了。
- 能用配置文件就别写长命令行；每个项目留一个（`python pdf_organizer.py --config library.json`）。
- 大批量新增后及时重跑，别攒着：因为有缓存，增量运行很便宜。
- 脚本/CI 场景：只要有文件移动失败，进程就以退出码 1 结束，不解析输出也能发现失败。用 `--verbose` 在日志里输出各类别明细。

## 9. 深入了解

- [README.zh-CN.md](README.zh-CN.md) — 完整选项参考和内置类别列表
- [SPECIFICATION.md](SPECIFICATION.md) — 分类器如何打分、数据格式、保证（英文）
- `organizer/rules.py` — 类别模式本身，想改造类别方案就从这里入手
