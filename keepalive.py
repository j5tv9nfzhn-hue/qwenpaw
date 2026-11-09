# -*- coding: utf-8 -*-
"""QwenPaw 云沙箱保活脚本

每 6 小时（GitHub Actions cron）走一遍控制台鉴权链路并打官方心跳，
重置平台的 48 小时无操作关机计时器。零 LLM token 消耗。

用法（环境变量）:
    QP_ACCOUNT  平台登录账号
    QP_PASSWORD 平台登录密码
"""
import json, os, sys, urllib.request, urllib.error

PLATFORM = "https://platform.agentscope.io"

def req(url, method="GET", headers=None, data=None, timeout=20):
    h = {"User-Agent": "Mozilla/5.0"}
    if headers: h.update(headers)
    body = json.dumps(data).encode() if data is not None else None
    if body is not None: h.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def keepalive(account, password):
    ok = True
    # 1) 登录
    code, body = req(f"{PLATFORM}/api/v1/auth/login", "POST",
                     data={"account": account, "password": password})
    at = json.loads(body).get("data", {}).get("accessToken")
    if not at:
        print("login failed")
        return False
    auth = {"Authorization": f"Bearer {at}", "accept": "application/json"}

    # 2) 列出名下全部沙箱（新增机器无需改动脚本）
    code, body = req(f"{PLATFORM}/api/v1/app/list", "GET", headers=auth)
    items = json.loads(body).get("data") or []
    if isinstance(items, dict):
        items = items.get("list") or []
    if not items:
        print("no sandbox found")
        return False

    # 3) 逐台打官方心跳；失败降级 console_token → push-messages
    for it in items:
        sid = it.get("id") or it.get("appId")
        c, _ = req(f"{PLATFORM}/api/v1/app/heartbeat", "POST",
                   headers=auth, data={"appId": sid})
        print(f"  {sid[:13]}… heartbeat: HTTP {c}")
        if c == 200:
            continue
        ok = False
        c2, b2 = req(f"{PLATFORM}/api/v1/qwenpaw/{sid}", "GET", headers=auth)
        ct = json.loads(b2).get("data", {}).get("console_token")
        if ct:
            c3, _ = req(f"https://{sid}.qwenpaw.platform.agentscope.io/api/console/push-messages",
                        headers={"x-agent-id": "default",
                                 "Cookie": f"qwenpaw_console_token={ct}"})
            print(f"    fallback push-messages: HTTP {c3}")
            if c3 == 200:
                ok = True
        else:
            print("    console_token unavailable")
    return ok

if __name__ == "__main__":
    account = os.environ.get("QP_ACCOUNT", "")
    password = os.environ.get("QP_PASSWORD", "")
    if not account or not password:
        print("QP_ACCOUNT / QP_PASSWORD required")
        sys.exit(2)
    sys.exit(0 if keepalive(account, password) else 1)
