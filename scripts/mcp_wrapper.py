#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦当劳 MCP 轻量客户端（仅用于调试 / 无 WorkBuddy 时测试连通性）。
注意：WorkBuddy 已原生支持 mcd-mcp，本 Skill 在 WorkBuddy 内直接调用 MCP 工具即可，
通常不需要此脚本。此脚本供你在 WorkBuddy 之外验证 Token 与接口用。

用法：
  python mcp_wrapper.py --token <TOKEN> list
  python mcp_wrapper.py --token <TOKEN> call available-coupons '{}'
  python mcp_wrapper.py --token <TOKEN> call query-nearby-stores '{"address":"长沙市芙蓉区"}'
"""
import sys
import json
import argparse
import urllib.request
import urllib.error

MCD_URL = "https://mcp.mcd.cn"


def _post(url, token, body, session_id=None):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    req.add_header("Authorization", "Bearer " + token)
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as e:
        return None, e.headers, e.read().decode("utf-8", "ignore")
    sid = resp.headers.get("Mcp-Session-Id")
    raw = resp.read().decode("utf-8", "ignore")
    return _parse(raw), sid, None


def _parse(raw):
    if raw.strip().startswith("{"):
        return json.loads(raw)
    out = None
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            try:
                out = json.loads(line[5:].strip())
            except Exception:
                pass
    return out


def init(token):
    body = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18",
                       "clientInfo": {"name": "mcd-wrapper", "version": "0.1"},
                       "capabilities": {}}}
    res, sid, err = _post(MCD_URL, token, body)
    if err:
        print("initialize failed:", err)
        sys.exit(1)
    note = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    _post(MCD_URL, token, note, sid)
    return sid


def list_tools(token, sid):
    body = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    res, _, _ = _post(MCD_URL, token, body, sid)
    tools = (res or {}).get("result", {}).get("tools", [])
    for t in tools:
        print("-", t.get("name"), ":", t.get("description", ""))
    return tools


def call_tool(token, sid, name, args):
    body = {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": name, "arguments": args}}
    res, _, _ = _post(MCD_URL, token, body, sid)
    print(json.dumps((res or {}).get("result", {}), ensure_ascii=False, indent=2))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--token", required=True)
    p.add_argument("action", choices=["list", "call"])
    p.add_argument("tool", nargs="?")
    p.add_argument("args", nargs="?", default="{}")
    a = p.parse_args()
    sid = init(a.token)
    if a.action == "list":
        list_tools(a.token, sid)
    else:
        call_tool(a.token, sid, a.tool, json.loads(a.args))


if __name__ == "__main__":
    main()
