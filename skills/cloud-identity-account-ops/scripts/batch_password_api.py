import asyncio, json, urllib.request, urllib.parse, sys

# 用法: python batch_password_api.py [網域] [密碼] [數量] [起始號]
# 例: python batch_password_api.py example.com REDACTED_SECRET 50 1
# 前置: OAuth Playground 已授權 admin.directory.user scope（token 從 Playground 頁面讀取）
DOMAIN = sys.argv[1] if len(sys.argv) > 1 else "example.com"
PWD = sys.argv[2] if len(sys.argv) > 2 else "REDACTED_SECRET"
COUNT = int(sys.argv[3]) if len(sys.argv) > 3 else 50
START = int(sys.argv[4]) if len(sys.argv) > 4 else 1

async def main():
    # 1. 從 OAuth Playground 讀取 access token
    with urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=5) as r:
        tabs = json.load(r)
    tab = next((t for t in tabs if t.get("type") == "page" and "oauthplayground" in t.get("url", "")), None)
    if not tab:
        print("NO_PLAYGROUND_TAB"); return
    import websockets
    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=10_000_000) as ws:
        mid = [0]
        async def cmd(method, params=None):
            mid[0] += 1
            await ws.send(json.dumps({"id": mid[0], "method": method, "params": params or {}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == mid[0]:
                    return msg
        res = await cmd("Runtime.evaluate", {"expression": "document.getElementById('access_token_field').value", "returnByValue": True})
        token = res.get("result", {}).get("result", {}).get("value")
    if not token:
        print("NO_TOKEN"); return
    print(f"Token 獲取成功（長度 {len(token)}）")

    # 2. 生成帳號清單（支援命名 a01..a99 或指定規則）
    users = [f"a{i:02d}@{DOMAIN}" for i in range(START, START + COUNT)]

    # 3. 批量重設密碼（Directory API）
    ok_count = 0
    fail_list = []
    for email in users:
        url = f"https://admin.googleapis.com/admin/directory/v1/users/{urllib.parse.quote(email)}"
        body = json.dumps({
            "password": PWD,
            "changePasswordAtNextLogin": False
        }).encode()
        req = urllib.request.Request(url, data=body, method="PUT")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                status = resp.status
                if status == 200:
                    ok_count += 1
                    print(f"✅ {email}: 密碼已設定")
                else:
                    fail_list.append(email)
                    print(f"⚠️ {email}: HTTP {status}")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode(errors="ignore")[:150]
            fail_list.append(email)
            print(f"❌ {email}: HTTP {e.code} {err_body}")
        except Exception as e:
            fail_list.append(email)
            print(f"❌ {email}: {e}")
        await asyncio.sleep(0.3)

    print(f"\n=== 完成：{ok_count}/50 成功 ===")
    if fail_list:
        print("失敗清單:", fail_list)

asyncio.run(main())
