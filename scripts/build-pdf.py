#!/usr/bin/env python3
"""Build PDF from mdbook HTML output using headless Chromium.
Concatenates all chapters into a single HTML, then prints to PDF.
"""
import subprocess, os, sys, re, glob
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parent.parent
BOOK_HTML = BOOK_DIR / "book"
OUT_DIR = BOOK_DIR / "output"
OUT_DIR.mkdir(exist_ok=True)

# Chapter order (matches SUMMARY.md)
CHAPTERS = [
    "序言：一封来自 2026 年的信",
    "第 1 章 · 当 Agent 开始写代码",
    "第 2 章 · 多 Agent 协同的架构模式",
    "第 3 章 · 范式革命还是框架内演进？",
    "第 4 章 · 角色坍缩：谁留下，谁消失",
    "第 5 章 · Context Engineering：2026 年的承重技能",
    "第 6 章 · Agent 编排实战",
    "第 7 章 · 速度与质量的永恒张力",
    "第 8 章 · 成为 AI Systems Architect",
    "第 9 章 · 我搞砸的那些事",
    "附录 A · 术语表",
    "附录 B · 参考文献与延伸阅读",
    "附录 C · Agent 编排工具对比",
    "附录 D · 番外篇：Agentic 软件工程的未来",
    "附录 E · 关于本书的说明",
    "附录 F · 12 个月转型计划",
    "关于作者",
]

# Map chapter names to HTML files
html_files = list(BOOK_HTML.glob("*.html"))
name_to_file = {}
for f in html_files:
    with open(f) as fh:
        content = fh.read(5000)
    m = re.search(r"<title>(.+?)</title>", content)
    if m:
        name_to_file[m.group(1)] = f.name

# Find each chapter's HTML file
chapter_htmls = []
for ch_name in CHAPTERS:
    found = None
    for title, filename in name_to_file.items():
        if ch_name in title:
            found = filename
            break
    if found:
        chapter_htmls.append(found)
    else:
        print(f"  ⚠  Chapter not found: {ch_name}")

print(f"Found {len(chapter_htmls)}/{len(CHAPTERS)} chapters")

# Read CSS from the built book
css_parts = []

# 1. Book CSS (variables, general, chrome, print)
for cssf in sorted(BOOK_HTML.glob("css/*.css")):
    css_parts.append(f"/* {cssf.name} */\n{cssf.read_text()}")

# 2. Custom theme CSS
custom_css = BOOK_DIR / "theme" / "custom.css"
if custom_css.exists():
    css_parts.append(f"/* custom.css */\n{custom_css.read_text()}")

css_content = "\n".join(css_parts)

# Add print-specific and CJK font CSS
print_css = """
/* === CJK font stack === */
html, body {
    font-family: "Noto Sans SC", "Source Han Sans SC", "WenQuanYi Micro Hei",
                 "PingFang SC", "Microsoft YaHei", "SimHei", sans-serif !important;
}
h1, h2, h3, h4, h5, h6 {
    font-family: "Noto Sans SC", "Source Han Sans SC", "WenQuanYi Micro Hei",
                 "PingFang SC", "Microsoft YaHei", "SimHei", sans-serif !important;
}
code, pre {
    font-family: "Noto Sans Mono SC", "Fira Code", "Consolas", monospace !important;
}

/* === Print layout === */
@media print {
  body { font-size: 11pt; line-height: 1.6; }
  .chapter { page-break-before: always; }
  h1 { page-break-before: always; font-size: 18pt; }
  h2 { font-size: 14pt; }
  h3 { font-size: 12pt; }
  pre, code { font-size: 9pt; }
  table { font-size: 9pt; }
  @page { margin: 2cm; }
}
"""

# Build concatenated HTML with <base> for correct relative path resolution
base_url = BOOK_HTML.as_uri() + "/"

full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<base href="{base_url}">
<title>代码之后：成为 AI 系统架构师</title>
<style>
{css_content}
{print_css}
body {{ max-width: 100%; margin: 0; padding: 2cm; }}
</style>
</head>
<body>
"""

for hf in chapter_htmls:
    filepath = BOOK_HTML / hf
    content = filepath.read_text()
    # Extract body content (between <body> and </body>)
    m = re.search(r"<body[^>]*>(.*?)</body>", content, re.DOTALL)
    if m:
        body = m.group(1)
        # Remove nav/sidebar elements
        body = re.sub(r"<nav[^>]*>.*?</nav>", "", body, flags=re.DOTALL)
        body = re.sub(
            r'<div[^>]*class="[^"]*sidebar[^"]*".*?</div>',
            "",
            body,
            flags=re.DOTALL,
        )
        full_html += body + "\n"

full_html += "</body>\n</html>"

# Write combined HTML
combined_path = OUT_DIR / "combined.html"
combined_path.write_text(full_html)
print(f"Combined HTML: {combined_path} ({len(full_html)} chars)")

# Print to PDF using headless Chromium (try multiple binary names)
pdf_path = OUT_DIR / "代码之后-AI系统架构师.pdf"

chromium_bins = [
    "chromium-browser",
    "chromium",
    "google-chrome",
    "google-chrome-stable",
]
chromium = None
for b in chromium_bins:
    if subprocess.run(["which", b], capture_output=True).returncode == 0:
        chromium = b
        break

if not chromium:
    print("  ⚠  No Chromium found, skipping PDF")
    sys.exit(0)

result = subprocess.run(
    [
        chromium,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        f"file://{combined_path}",
    ],
    capture_output=True,
    text=True,
    timeout=120,
)

if result.returncode == 0:
    size_kb = pdf_path.stat().st_size / 1024
    print(f"  ✓ PDF: {pdf_path} ({size_kb:.0f} KB)")
else:
    print(f"  ✗ PDF failed: {result.stderr}")
    sys.exit(1)
