#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「演示卷轴」data/scroll_demo.html —— 用真实麦当劳菜单/门店/营养数据填充，
   展示四卷（秘籍卷/门店卷/订单卷/成就墙）全貌。
   注意：本脚本只写 data/secrets_demo.json 与 data/scroll_demo.html，
   不会动真实存档 data/secrets.json。
"""
import os
import json
import urllib.parse

import local_engine as E

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_SECRET = os.path.join(BASE, "data", "secrets_demo.json")
DEMO_OUT = os.path.join(BASE, "data", "scroll_demo.html")

# 演示用：日期/时间 Patterns 覆盖各类行为成就（early/night/noon/midnight/streak/weekend）
# 餐品名、价格、热量全部来自真机 query-meals + list-nutrition-foods
# (时间, 名称, 类别, 热量, 到手价)
PLAN = [
    # 早鸟档 07:10 × 连续 5 天 → 点亮「早起的人儿有汉堡吃」
    ("2026-10-01 07:10", "巨无霸", "burger", 513, 25.5),
    ("2026-10-02 07:10", "巨无霸", "burger", 513, 25.5),
    ("2026-10-03 07:10", "巨无霸三件套", "combo", 949, 36.5),
    ("2026-10-04 07:10", "板烧鸡腿堡三件套", "combo", 827, 34.5),
    ("2026-10-05 07:10", "巨无霸", "burger", 513, 25.5),
    # 正午档 × 仅 2 天 → 故意差 3 天，让「正午食客」保持灰暗
    ("2026-10-06 12:30", "麦香鸡套餐", "combo", 805, 28.0),
    ("2026-10-07 12:30", "麦香鸡", "burger", 369, 17.0),
    # 夜宵档 × 仅 3 天 → 故意差 2 天，让「夜宵大王」保持灰暗
    ("2026-10-08 21:40", "麦辣鸡腿汉堡三件套", "combo", 921, 33.5),
    ("2026-10-09 21:40", "麦辣鸡腿汉堡+中薯条", "burger_plus_side", 774, 36.0),
    ("2026-10-10 21:40", "双层吉士汉堡套餐", "combo", 865, 34.0),
    # 凌晨档 → 点亮「凌晨独醒」
    ("2026-10-11 03:20", "板烧鸡腿堡+麦乐鸡", "burger_plus_side", 604, 37.5),
]

# 演示用门店（已脱敏：仅示例，不含任何真实地名/坐标；真实门店由运行时 MCP + 百度地图拉取）
STORES = [
    ("麦当劳示例门店（中心店）", "示例商业区A座1层", "196 米"),
    ("麦当劳示例门店（二店）", "示例街区中心路口", "530 米"),
    ("麦当劳示例门店（三店）", "示例购物中心地下一层", "553 米"),
    ("麦当劳示例门店（四店）", "示例大厦1层", "591 米"),
    ("麦当劳示例门店（五店）", "示例广场1层1013A", "632 米"),
]

ORDERS = [
    {"no": "MCD20261009001", "items": "巨无霸 x1（到店自取）", "status": "已送达"},
    {"no": "MCD20261009002", "items": "板烧鸡腿堡三件套 x1", "status": "制作中"},
    {"no": "MCD20261009003", "items": "麦辣鸡腿汉堡+中薯条 x1", "status": "已接单"},
]


def main():
    # 切到演示存档，避免污染真实 secrets.json
    E.SECRETS_PATH = DEMO_SECRET
    E.OUTPUT_PATH = DEMO_OUT
    if os.path.exists(DEMO_SECRET):
        os.remove(DEMO_SECRET)

    for t, name, cat, kcal, price in PLAN:
        a = type("A", (), {
            "item": '{"name": "%s", "category": "%s", "kcal": %s, "price": %s}' % (name, cat, kcal, price),
            "store": "麦当劳示例门店",
            "order": "MCD-" + t.replace(" ", "-").replace(":", ""),
            "time": t,
        })()
        E.cmd_archive(a)

    st = E.load_state()
    # 故意压到「刚好差一点」：抽签 12 次(差 18 次满 30)、卡包 16 张(差 14 张满 30)
    # 这样成就墙同时呈现「已点亮」与「未解之谜」两种状态，展示隐藏式彩蛋感
    st["draw_count"] = 12
    st["coupon_count"] = 16
    E.save_json(DEMO_SECRET, st)

    class AC:
        coupons = 16
    res = __import__("json").loads(E.cmd_achievements(AC()))
    print("演示版解锁成就数：", len(res["unlocked"]))
    print("   " + " / ".join(u["name"] for u in res["unlocked"]))

    # 演示门店一律用脱敏的示例门店（不读取任何真实坐标文件，避免泄露真实位置）
    stores = [{
        "name": n, "address": a, "distance": d,
        "nav": "https://uri.amap.com/search?keyword=" + urllib.parse.quote(n),
    } for n, a, d in STORES]
    print("门店坐标来源：示例门店（已脱敏，不含真实位置）")

    import json as _json
    R = type("R", (), {
        "stores": _json.dumps(stores, ensure_ascii=False),
        "orders": _json.dumps(ORDERS, ensure_ascii=False),
    })()
    print(E.cmd_render(R))


if __name__ == "__main__":
    main()
