#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦麦秘籍 本地引擎：抽签 / 存档 / 成就(含行为模式) / 健身搭档 / 卷轴渲染。纯标准库，无需联网。
健身搭档热量模型：运动消耗来自《Compendium of Physical Activities》及各国卫生机构运动消耗表
（70kg 成人、休闲/中等强度 MET 值，kcal/min = MET×70/60）。每日总消耗 TDEE 取 70kg 轻度活动参考值 2250 kcal。
用法：
  python local_engine.py draw [--pref 牛肉 不辣] [--category burger|combo|burger_plus_side]
  python local_engine.py archive --item '{"name":"巨无霸","kcal":563,...}' --store 店名 --order 订单号 [--time '2026-10-09 07:10']
  python local_engine.py fitness --kcal 820
  python local_engine.py fitness --name 麦辣鸡腿堡套餐
  python local_engine.py achievements [--coupons 30]
  python local_engine.py render [--stores ...] [--orders ...]
"""
import json
import random
import os
import datetime
import argparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MENU_PATH = os.path.join(BASE, "data", "menu_sample.json")
SECRETS_PATH = os.path.join(BASE, "data", "secrets.json")
TEMPLATE_PATH = os.path.join(BASE, "assets", "scroll_template.html")
OUTPUT_PATH = os.path.join(BASE, "data", "scroll.html")

CATEGORY_NAMES = {
    "burger": "单堡",
    "combo": "套餐",
    "burger_plus_side": "堡+小食",
}

# 健身搭档参数
WEIGHT_KG = 70
TDEE = 2250.0  # 70kg 成人每日总消耗（轻度活动参考值）
# 运动消耗：休闲/中等强度 MET 值（70kg），kcal/min = MET*WEIGHT_KG/60
# 来源：Compendium of Physical Activities + 各国卫生机构运动消耗表
EXERCISES = [
    {"key": "walk",      "name": "散步",   "verb": "溜达",   "emoji": "🚶", "kcal_per_min": 5.3},
    {"key": "run",       "name": "跑步",   "verb": "跑",     "emoji": "🏃", "kcal_per_min": 9.6},
    {"key": "badminton", "name": "羽毛球", "verb": "打羽毛球", "emoji": "🏸", "kcal_per_min": 6.4},
    {"key": "pingpong",  "name": "乒乓球", "verb": "打乒乓球", "emoji": "🏓", "kcal_per_min": 4.9},
    {"key": "swim",      "name": "游泳",   "verb": "游",     "emoji": "🏊", "kcal_per_min": 7.4},
    {"key": "bike",      "name": "骑自行车", "verb": "骑",    "emoji": "🚴", "kcal_per_min": 4.7},
    {"key": "rope",      "name": "跳绳",   "verb": "跳",     "emoji": "🤾", "kcal_per_min": 9.8},
    {"key": "yoga",      "name": "瑜伽",   "verb": "练",     "emoji": "🧘", "kcal_per_min": 3.5},
]

# 成就体系（全部围绕「吃 / 行为模式」，不含纯运动维度）
# key -> (名称, 描述)
ACHIEVEMENTS = {
    # A 入门 / 进度
    "first_secret":   ("初入江湖",     "收藏第一条麦麦秘籍"),
    "draw_10":        ("十全十美",     "累计抽签满 10 次"),
    "draw_30":        ("百抽不倦",     "累计抽签满 30 次"),
    "all_categories": ("三门精通",     "集齐 单堡 / 套餐 / 堡+小食 三类秘籍"),
    "coupon_30":      ("券王附体",     "累计领取优惠券满 30 张"),
    "combo_master":   ("套餐行家",     "收藏套餐类秘籍满 5 条"),
    "burger_fan":     ("单堡行家",     "收藏单堡类秘籍满 5 条"),
    # B 时段行为（基于点单时间）
    "early_bird":     ("早起的人儿有汉堡吃", "连续 5 天在 07:30 前点单"),
    "night_owl":      ("夜宵大王",     "连续 5 天在 21:30 后点单"),
    "noon_regular":   ("正午食客",     "连续 5 天在 11:00–14:00 点单"),
    "midnight_ghost": ("凌晨独醒",     "在 00:00–05:00 点过单"),
    # C 频率节奏
    "daily_streak":   ("一日不可无麦", "连续 7 个自然日都有点单"),
    "weekend_warrior":("周末战士",     "点单覆盖满 3 个不同周末"),
    "check_in":       ("打卡狂魔",     "累计收藏秘籍满 20 条"),
    # D 彩蛋
    "bigmac_fan":     ("巨无霸主义者", "点过「巨无霸」满 3 条"),
    "saver":          ("羊毛出在牛身上", "累计领券满 50 张"),
}


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_state():
    s = load_json(SECRETS_PATH, None)
    if s is None:
        s = {"secrets": [], "draw_count": 0, "coupon_count": 0,
             "total_kcal": 0, "achievements": []}
    s.setdefault("secrets", [])
    s.setdefault("draw_count", 0)
    s.setdefault("coupon_count", 0)
    s.setdefault("total_kcal", 0)
    s.setdefault("achievements", [])
    return s


# 偏好别名：中文口语（牛肉/鸡肉/不辣/辣）也能命中英文菜单标签
PREF_ALIAS = {"牛肉": "beef", "鸡肉": "chicken", "不辣": "not_spicy", "辣": "spicy",
              "beef": "beef", "chicken": "chicken", "not_spicy": "not_spicy", "spicy": "spicy"}

def filter_by_pref(items, pref):
    if not pref:
        return items
    pref = [PREF_ALIAS.get(p, p) for p in pref]
    out = []
    for it in items:
        tags = set(it.get("tags", []))
        if any(p in tags for p in pref):
            out.append(it)
    return out or items


def calc_fitness(kcal):
    """热量换算：结合每日总消耗给出占比 + 随机推荐一种运动的额外抵消时长。"""
    if not kcal:
        return None
    details = [dict(e, minutes=max(1, round(kcal / e["kcal_per_min"]))) for e in EXERCISES]
    rec = random.choice(details)
    return {
        "kcal": kcal,
        "daily_pct": round(kcal / TDEE * 100),
        "rest_hours": round(kcal / (TDEE / 24), 1),
        "recommended": {"key": rec["key"], "name": rec["name"], "verb": rec["verb"],
                        "emoji": rec["emoji"], "minutes": rec["minutes"]},
        "details": details,
    }


def _parse_time(secret):
    try:
        return datetime.datetime.strptime(secret.get("time", ""), "%Y-%m-%d %H:%M")
    except Exception:
        return None


def _longest_streak(date_list):
    """date_list: 日期集合，返回最长连续自然日序列长度。"""
    ds = sorted(set(date_list))
    if not ds:
        return 0
    best = cur = 1
    for i in range(1, len(ds)):
        if (ds[i] - ds[i - 1]).days == 1:
            cur += 1
        else:
            cur = 1
        best = max(best, cur)
    return best


def cmd_draw(args):
    menu = load_json(MENU_PATH, {"items": []})
    items = menu.get("items", [])
    if args.category:
        items = [i for i in items if i.get("category") == args.category]
    items = filter_by_pref(items, args.pref or [])
    if not items:
        return json.dumps({"error": "没有符合偏好的餐品，换换口味？"}, ensure_ascii=False)
    pick = random.choice(items)
    pick["fitness"] = calc_fitness(pick.get("kcal"))
    state = load_state()
    state["draw_count"] += 1
    save_json(SECRETS_PATH, state)
    return json.dumps({"pick": pick, "draw_count": state["draw_count"]}, ensure_ascii=False)


def cmd_archive(args):
    state = load_state()
    item = json.loads(args.item) if args.item else {}
    fit = calc_fitness(item.get("kcal"))
    rec = fit["recommended"] if fit else None
    when = args.time or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    secret = {
        "id": "S%03d" % (len(state["secrets"]) + 1),
        "name": item.get("name", "神秘餐品"),
        "category": item.get("category", "burger"),
        "kcal": item.get("kcal"),
        "price": item.get("price"),
        "fitness": fit,
        "exercise": rec["key"] if rec else None,
        "fit_minutes": rec["minutes"] if rec else 0,
        "store": args.store or "",
        "order": args.order or "",
        "paid": True,
        "time": when,
    }
    state["secrets"].append(secret)
    if item.get("kcal"):
        state["total_kcal"] = state["total_kcal"] + item["kcal"]
    save_json(SECRETS_PATH, state)
    return json.dumps({"secret": secret, "total": len(state["secrets"]),
                       "total_kcal": state["total_kcal"]}, ensure_ascii=False)


def cmd_fitness(args):
    menu = load_json(MENU_PATH, {"items": []})
    kcal = args.kcal
    if kcal is None and args.name:
        for it in menu.get("items", []):
            if it.get("name") == args.name:
                kcal = it.get("kcal")
                break
    fit = calc_fitness(kcal)
    if fit is None:
        return json.dumps({"error": "未提供热量或找不到该餐品"}, ensure_ascii=False)
    return json.dumps({"name": args.name or "该餐品", "fitness": fit}, ensure_ascii=False)


def cmd_achievements(args):
    state = load_state()
    if args.coupons is not None:
        state["coupon_count"] = max(state["coupon_count"], args.coupons)
    secrets = state["secrets"]
    cats = {s.get("category") for s in secrets}
    combo_n = sum(1 for s in secrets if s.get("category") == "combo")
    burger_n = sum(1 for s in secrets if s.get("category") == "burger")
    bigmac_n = sum(1 for s in secrets if "巨无霸" in (s.get("name") or ""))
    dts = [_parse_time(s) for s in secrets]
    dts = [d for d in dts if d]
    dates = [d.date() for d in dts]
    early_dates = [d.date() for d in dts if d.hour < 7 or (d.hour == 7 and d.minute < 30)]
    late_dates = [d.date() for d in dts if d.hour > 21 or (d.hour == 21 and d.minute >= 30)]
    noon_dates = [d.date() for d in dts if 11 <= d.hour < 14]
    midnight_dates = [d.date() for d in dts if 0 <= d.hour < 5]
    weekend_keys = set()
    for d in dates:
        if d.weekday() >= 5:  # 周六/周日
            monday = d - datetime.timedelta(days=d.weekday())
            weekend_keys.add(monday)
    checks = {
        "first_secret": len(secrets) >= 1,
        "draw_10": state["draw_count"] >= 10,
        "draw_30": state["draw_count"] >= 30,
        "all_categories": {"burger", "combo", "burger_plus_side"} <= cats,
        "coupon_30": state["coupon_count"] >= 30,
        "combo_master": combo_n >= 5,
        "burger_fan": burger_n >= 5,
        "early_bird": _longest_streak(early_dates) >= 5,
        "night_owl": _longest_streak(late_dates) >= 5,
        "noon_regular": _longest_streak(noon_dates) >= 5,
        "midnight_ghost": len(midnight_dates) >= 1,
        "daily_streak": _longest_streak(dates) >= 7,
        "weekend_warrior": len(weekend_keys) >= 3,
        "check_in": len(secrets) >= 20,
        "bigmac_fan": bigmac_n >= 3,
        "saver": state["coupon_count"] >= 50,
    }
    unlocked = []
    for k, ok in checks.items():
        if ok and k not in state["achievements"]:
            state["achievements"].append(k)
            unlocked.append({"key": k, "name": ACHIEVEMENTS[k][0], "desc": ACHIEVEMENTS[k][1]})
    save_json(SECRETS_PATH, state)
    return json.dumps({"unlocked": unlocked, "all": state["achievements"]}, ensure_ascii=False)


def cmd_render(args):
    state = load_state()
    stores = json.loads(args.stores) if args.stores else []
    orders = json.loads(args.orders) if args.orders else []
    for s in state["secrets"]:
        if "fitness" not in s:
            s["fitness"] = calc_fitness(s.get("kcal"))
    data = {
        "secrets": state["secrets"],
        "stores": stores,
        "orders": orders,
        # 菜单池：让卷轴页「签筒」可离线抽签（无 Token 也能玩），保证通用性
        "menu": load_json(MENU_PATH, {"items": []}).get("items", []),
        "total_kcal": state.get("total_kcal", 0),
        # 隐藏式成就：未点亮的**不向页面下发**真名/描述（只给 got:false），
        # 保证「彩蛋感」——查看网页源码也看不到未解锁成就是什么。
        "achievements": [
            ({"key": k, "name": ACHIEVEMENTS[k][0], "desc": ACHIEVEMENTS[k][1], "got": True}
             if k in state["achievements"]
             else {"got": False})
            for k in ACHIEVEMENTS
        ],
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()
    html = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    return json.dumps({"output": OUTPUT_PATH, "secrets": len(state["secrets"])}, ensure_ascii=False)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    pd = sub.add_parser("draw")
    pd.add_argument("--pref", nargs="*", default=[])
    pd.add_argument("--category", default=None)
    pa = sub.add_parser("archive")
    pa.add_argument("--item", default=None)
    pa.add_argument("--store", default=None)
    pa.add_argument("--order", default=None)
    pa.add_argument("--time", default=None)
    pf = sub.add_parser("fitness")
    pf.add_argument("--kcal", type=float, default=None)
    pf.add_argument("--name", default=None)
    pc = sub.add_parser("achievements")
    pc.add_argument("--coupons", type=int, default=None)
    pr = sub.add_parser("render")
    pr.add_argument("--stores", default=None)
    pr.add_argument("--orders", default=None)
    args = p.parse_args()
    if args.cmd == "draw":
        print(cmd_draw(args))
    elif args.cmd == "archive":
        print(cmd_archive(args))
    elif args.cmd == "fitness":
        print(cmd_fitness(args))
    elif args.cmd == "achievements":
        print(cmd_achievements(args))
    elif args.cmd == "render":
        print(cmd_render(args))
    else:
        p.print_help()


if __name__ == "__main__":
    main()
