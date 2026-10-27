#!/usr/bin/env python3
"""gate_bib.py — literature.bib 机械门禁：条目可解析、key 唯一、必备字段、计数报告。"""
import re, sys, pathlib
BIB = pathlib.Path(__file__).resolve().parent.parent / "literature.bib"
if not BIB.exists():
    print("FATAL: literature.bib 不存在"); sys.exit(1)
text = BIB.read_text()
# 本仓格式每条记录从行首开始；注释中的示例不算条目。
text = re.sub(r'^\s*%.*$', '', text, flags=re.M)
entries = re.findall(r'^@(\w+)\{([^,]+),(.*?)\n\}', text, re.S | re.M)
errs, warns, keys = [], [], []
starts = re.findall(r'^@\w+\{', text, re.M)
if len(starts) != len(entries):
    errs.append(f"条目结构不完整：起始 {len(starts)}，闭合解析 {len(entries)}；检查缺失结束括号")
for etype, key, body in entries:
    keys.append(key)
    if not re.search(r'title\s*=', body):
        errs.append(f"{key}: 缺 title")
    if etype in ("article", "phdthesis", "incollection") and not re.search(r'year\s*=', body):
        errs.append(f"{key}: 学术条目缺 year")
    if etype == "article" and not (re.search(r'doi\s*=', body) or re.search(r'url\s*=', body)):
        warns.append(f"{key}: article 无 doi/url")
dups = {k for k in keys if keys.count(k) > 1}
if dups:
    errs.append(f"key 重复: {sorted(dups)}")
print(f"条目总数: {len(keys)}；错误 {len(errs)}；警告 {len(warns)}")
for e in errs: print("ERROR:", e)
for w in warns: print("WARN:", w)
sys.exit(1 if errs else 0)
