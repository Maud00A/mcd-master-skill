#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦麦秘籍 · 投稿前脱敏清理脚本
================================

按 SKILL.md「隐私红线」要求：把真实存档（data/secrets.json）里的可识别信息
（门店真实地址、LIVE- 订单号、任何姓名/手机/地址类字段）抹掉，产出一份脱敏的
样例存档 data/secrets_demo.json，用于提交到公开的 GitHub 比赛仓库。

设计原则：
- 只做「副本脱敏」，不动原始 data/secrets.json（它仍由 render/archive 本地使用）。
- 保留数据结构与条目数量，只改「能定位到具体人或地点」的字段，让演示页照常好看。
- 防御式剥离：遇到 phone / address / recipient / customer / id_card 等敏感键直接丢弃。

用法：
    python scripts/sanitize.py                 # secrets.json -> secrets_demo.json
    python scripts/sanitize.py --in x.json --out y.json
    python scripts/sanitize.py --check         # 仅扫描并报告敏感字段，不写文件
"""
import argparse
import json
import os
import re
import sys

# 绝对不能进公开仓库的字段
PII_KEYS = ("phone", "mobile", "tel", "address", "recipient", "recipient_name",
            "customer", "customer_name", "id_card", "idcard", "realname", "name_phone")

# LIVE- 前缀（真实订单）统一改成 DEMO-
LIVE_RE = re.compile(r"^LIVE-", re.I)

# 门店名里剥掉具体地名，只留「示例门店」
def mask_store(name: str) -> str:
    if not name:
        return "麦当劳示例门店"
    # 去掉「城市+路/区+具体楼宇」等定位信息：保留「麦当劳」开头的示例字样
    s = re.sub(r"(长沙|北京|上海|广州|深圳|杭州|成都|武汉|南京|西安|重庆|天津|苏州|青岛|厦门|长沙).*?(餐厅|店|门店)", "示例门店", name)
    if "示例门店" not in s:
        s = "麦当劳示例门店"
    return s


def mask_order(order: str) -> str:
    if not order:
        return "DEMO-0000"
    if LIVE_RE.match(order):
        return "DEMO-" + re.sub(r"[^0-9A-Za-z]", "", order[len("LIVE-"):])[:8] or "DEMO-0000"
    return order  # 已经是 MCD-/DEMO- 之类脱敏格式的保留


def sanitize_record(rec: dict) -> dict:
    out = {}
    for k, v in rec.items():
        lk = k.lower()
        if any(p in lk for p in PII_KEYS):
            # 敏感字段：丢弃
            continue
        if k == "store":
            out[k] = mask_store(v if isinstance(v, str) else "")
        elif k == "order":
            out[k] = mask_order(v if isinstance(v, str) else "")
        else:
            out[k] = v
    return out


def scan_sensitive(data: dict):
    """返回所有发现的敏感字段/值，用于 --check 与报告。"""
    hits = []
    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                lk = k.lower()
                if any(p in lk for p in PII_KEYS) and v not in (None, "", []):
                    hits.append((path + "/" + k, v))
                # store 字段若含具体地名（非示例门店）视为可定位信息
                if k == "store" and isinstance(v, str) and "示例门店" not in v:
                    hits.append((path + "/" + k, v))
                walk(v, path + "/" + k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")
    walk(data)
    return hits


def main():
    ap = argparse.ArgumentParser(description="麦麦秘籍 投稿前脱敏清理")
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    ap.add_argument("--in", dest="inp", default=os.path.join(root, "data", "secrets.json"),
                    help="真实存档（默认 data/secrets.json）")
    ap.add_argument("--out", dest="out", default=os.path.join(root, "data", "secrets_demo.json"),
                    help="脱敏样例输出（默认 data/secrets_demo.json）")
    ap.add_argument("--check", action="store_true", help="只扫描报告，不写文件")
    args = ap.parse_args()

    if not os.path.exists(args.inp):
        print(f"[错误] 找不到输入文件：{args.inp}", file=sys.stderr)
        sys.exit(2)

    with open(args.inp, encoding="utf-8") as f:
        data = json.load(f)

    # 扫描敏感字段
    hits = scan_sensitive(data)
    print(f"[扫描] 输入：{args.inp}")
    print(f"[扫描] 发现敏感字段 {len(hits)} 处：")
    for path, val in hits:
        print(f"    - {path} = {val}")

    if args.check:
        print("[check] 仅扫描，未写文件。")
        sys.exit(0)

    # 脱敏
    if "secrets" in data and isinstance(data["secrets"], list):
        data["secrets"] = [sanitize_record(r) for r in data["secrets"]]

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 二次校验：输出里不应再有任何 LIVE- 与敏感字段
    post = scan_sensitive(data)
    live_left = sum(1 for r in data.get("secrets", []) if str(r.get("order", "")).upper().startswith("LIVE-"))
    print(f"[完成] 已写出脱敏样例：{args.out}")
    print(f"[校验] 残留 LIVE- 订单：{live_left}；残留敏感字段：{len(post)}")
    if live_left or post:
        print("[警告] 仍检测到未脱敏内容，请人工复核后再提交 GitHub。", file=sys.stderr)
        sys.exit(1)
    print("[OK] 样例安全，可提交公开仓库。")


if __name__ == "__main__":
    main()
