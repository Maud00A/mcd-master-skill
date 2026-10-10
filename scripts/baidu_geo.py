#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""百度地图 Agent Plan 轻量封装（地理编码 / 路线链接），供麦麦秘籍使用。

为什么需要它：麦当劳 MCP 的 query-nearby-stores 返回的 longitude/latitude 恒为 0，
因此门店坐标必须用「地址 → 地理编码」的真实来源补全（禁止推测坐标）。

凭证：读环境变量 BAIDU_MAP_AUTH_TOKEN
（申请：https://lbs.baidu.com/apiconsole/agentplan）

用法：
  python baidu_geo.py geocode --address "黄兴中路88号平和堂商厦负一楼" --region 长沙市
  python baidu_geo.py enrich --stores stores.json --out ../data/stores_geo.json
"""
import json
import os
import urllib.parse
import urllib.request

BASE_URL = "https://api.map.baidu.com"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO_PATH = os.path.join(BASE, "data", "stores_geo.json")

COORD_TYPE = "gcj02"


def _token():
    t = os.environ.get("BAIDU_MAP_AUTH_TOKEN", "").strip()
    if not t:
        raise SystemExit("缺少 BAIDU_MAP_AUTH_TOKEN，请到 https://lbs.baidu.com/apiconsole/agentplan 申请后设置环境变量")
    return t


def _get(path, **params):
    url = BASE_URL + path + "?" + urllib.parse.urlencode(params, encoding="utf-8")
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Bearer " + _token())
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def geocode(address, region=""):
    """地址 -> {lng, lat, name, formatted_address}"""
    p = {"address": address}
    if region:
        p["region"] = region
    d = _get("/agent_plan/v1/geocoding", **p)
    if d.get("status") != 0 or not d.get("result"):
        return None
    loc = d["result"]["location"]
    poi = (d.get("poi_infos") or [{}])[0]
    return {
        "lng": round(loc["lng"], 6),
        "lat": round(loc["lat"], 6),
        "name": poi.get("name", ""),
        "formatted_address": poi.get("formatted_address", ""),
        "confidence": d["result"].get("confidence"),
    }


def marker_url(lng, lat, title="", content=""):
    """在百度地图上查看该点"""
    return (BASE_URL + "/marker?location=%s,%s&title=%s&content=%s&output=html&coord_type=%s"
            % (lat, lng, urllib.parse.quote(title or ""), urllib.parse.quote(content or ""), COORD_TYPE))


def direction_url(olat, olng, dlat, dlng, destination_name="", mode="walking"):
    """路线规划链接（mode: driving / walking / riding / transit）"""
    return (BASE_URL + "/direction?origin=%s,%s&destination=%s,%s&mode=%s&output=html&coord_type=%s"
            % (olat, olng, dlat, dlng, mode, COORD_TYPE))


def place_mcdonald(request, region, center=None):
    """语义化 AI 地点检索，返回清洗后的 POI 列表。

    这是获取门店坐标的**首选**方式：地址地理编码对「黄兴北路与中山路交汇处」
    这类模糊路口会定位错（实测偏差达 2.9km），而 POI 检索返回的是门店真实坐标，
    且与麦当劳 MCP 的 distance 相互印证。
    """
    p = {"user_raw_request": request, "region": region}
    if center:
        p["center"] = center
        p["sort"] = "distance"
    d = _place(**p)
    out = []
    for it in (d.get("results") or []):
        loc = it.get("location") or {}
        di = it.get("detail_info") or {}
        if not loc.get("lng"):
            continue
        out.append({
            "name": it.get("name", ""),
            "address": it.get("address", ""),
            "lng": round(loc["lng"], 6),
            "lat": round(loc["lat"], 6),
            "distance": di.get("distance"),
            "rating": it.get("rating") or di.get("overall_rating"),
        })
    return {"pois": out, "resource_key": d.get("resource_key", "")}


def _place(**params):
    return _get("/agent_plan/v1/place", **params)


def _lcs(a, b):
    """最长公共子串长度，用于把麦当劳门店名与百度 POI 名对齐"""
    m = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    best = 0
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                m[i][j] = m[i - 1][j - 1] + 1
                best = max(best, m[i][j])
    return best


def resolve_stores(stores, pois):
    """把麦当劳门店与百度 POI 按名称相似度对齐，产出带真实坐标的最终列表。"""
    used, out = set(), []
    for st in stores:
        best, bi = 0, -1
        for i, p in enumerate(pois):
            if i in used:
                continue
            s = max(_lcs(st["name"], p["name"]), _lcs(st.get("address", ""), p["address"]))
            if s > best:
                best, bi = s, i
        item = dict(st)
        if bi >= 0 and best >= 3:
            p = pois[bi]
            used.add(bi)
            item.update({"lng": p["lng"], "lat": p["lat"],
                         "rating": p["rating"], "baidu_name": p["name"],
                         "distance": (str(p["distance"]) + " 米") if p["distance"] else st.get("distance")})
            item["nav"] = marker_url(p["lng"], p["lat"], st["name"], st.get("address", ""))
            item["via"] = "baidu-place"
        else:
            item["via"] = "no-match"
        out.append(item)
    return out
    """给 [{name,address,distance}] 补真实坐标与百度地图链接"""
    out = []
    for st in stores:
        g = geocode(st.get("address", ""), region) or {}
        item = dict(st)
        if g.get("lng"):
            item["lng"] = g["lng"]
            item["lat"] = g["lat"]
            item["geo_name"] = g.get("name", "")
            item["nav"] = marker_url(g["lng"], g["lat"], st.get("name", ""), st.get("address", ""))
            # route 需真实起点坐标，由调用方在拿到用户位置后补
        out.append(item)
        print("  %-28s -> %s" % (st.get("name", "")[:28], (str(g.get("lng")) + "," + str(g.get("lat"))) if g else "失败"))
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")

    g = sub.add_parser("geocode")
    g.add_argument("--address", required=True)
    g.add_argument("--region", default="")

    e = sub.add_parser("enrich")
    e.add_argument("--stores", required=True, help="[{name,address,distance}] 的 JSON 文件")
    e.add_argument("--region", default="")
    e.add_argument("--out", default=GEO_PATH)

    pl = sub.add_parser("place")
    pl.add_argument("--request", required=True)
    pl.add_argument("--region", required=True)
    pl.add_argument("--center", default="")

    rv = sub.add_parser("resolve")
    rv.add_argument("--stores", required=True, help="query-nearby-stores 得到的门店列表 JSON")
    rv.add_argument("--region", required=True)
    rv.add_argument("--center", required=True, help="参考中心 lat,lng（gcj02），须来自可靠来源")
    rv.add_argument("--request", default="附近的麦当劳餐厅")
    rv.add_argument("--out", default=GEO_PATH)

    a = ap.parse_args()
    if a.cmd == "geocode":
        print(json.dumps(geocode(a.address, a.region), ensure_ascii=False, indent=2))
    elif a.cmd == "place":
        print(json.dumps(place_mcdonald(a.request, a.region, a.center or None),
                         ensure_ascii=False, indent=2))
    elif a.cmd == "resolve":
        with open(a.stores, encoding="utf-8") as f:
            stores = json.load(f)
        r = place_mcdonald(a.request, a.region, a.center)
        print("检索到 POI %d 个" % len(r["pois"]))
        res = resolve_stores(stores, r["pois"])
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        for s in res:
            print("  %-26s %s" % (s["name"][:26], (str(s.get("lng")) + "," + str(s.get("lat"))) if s.get("lng") else "未匹配"))
        print("已写入", a.out)
    elif a.cmd == "enrich":
        with open(a.stores, encoding="utf-8") as f:
            stores = json.load(f)
        res = enrich(stores, a.region)
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print("已写入", a.out, "共", len(res), "条")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
