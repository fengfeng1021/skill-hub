import asyncio, json, urllib.request, sys

# 用法: python make_batch.py <起始index> [names.json路徑]
# 前置: Hermes browser_click 已開啟「新增使用者」表單（URL=/ac/user/bulkadd）
NAMES_PATH = sys.argv[2] if len(sys.argv) > 2 else r"D:\Hermes\skills\google-admin\cloud-identity-account-ops\scripts\names.json"
NAMES = json.load(open(NAMES_PATH, encoding="utf-8"))

async def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    with urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=5) as r:
        tabs = json.load(r)
    tab = next((t for t in tabs if t.get("type") == "page" and "admin.google.com" in t.get("url", "")), None)
    if not tab:
        print("NO_TAB"); return
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
        async def eval_js(expr):
            res = await cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True})
            return res.get("result", {}).get("result", {}).get("value")

        # 1. 等待表單載入（新增其他使用者按鈕出現）
        for _ in range(15):
            has_btn = await eval_js("""
            (function() {
                return Array.from(document.querySelectorAll('button')).some(b => b.textContent.includes('新增其他使用者'));
            })()
            """)
            if has_btn:
                break
            await asyncio.sleep(1)

        # 2. 嘗試加行到 40 inputs（10 行）；失敗則用現有行數
        for _ in range(12):
            n = int(await eval_js("document.querySelectorAll('input').length") or 0)
            if n >= 40:
                break
            await eval_js("""
            (function() {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('新增其他使用者'));
                if (btn) { btn.click(); return true; }
                return false;
            })()
            """)
            await asyncio.sleep(1.0)
        n = int(await eval_js("document.querySelectorAll('input').length") or 0)
        rows = n // 4
        print(f"[{start//10+1}] INPUTS: {n} = {rows} 行")
        if rows < 1:
            print("!! 表單無欄位"); return

        async def rect_of(idx):
            await cmd("Runtime.evaluate", {"expression": f"""
                (function() {{
                    const el = document.querySelectorAll('input')[{idx}];
                    el.scrollIntoView({{block: 'center'}});
                    return true;
                }})()
            """})
            await asyncio.sleep(0.3)
            return await eval_js(f"""
                (function() {{
                    const el = document.querySelectorAll('input')[{idx}];
                    const r = el.getBoundingClientRect();
                    return [r.x + r.width/2, r.y + r.height/2];
                }})()
            """)

        async def fill(idx, val):
            rx, ry = await rect_of(idx)
            await cmd("Input.dispatchMouseEvent", {"type": "mousePressed", "x": rx, "y": ry, "button": "left", "clickCount": 1})
            await cmd("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": rx, "y": ry, "button": "left", "clickCount": 1})
            await asyncio.sleep(0.12)
            await cmd("Input.dispatchKeyEvent", {"type": "keyDown", "modifiers": 2, "key": "a", "code": "KeyA", "windowsVirtualKeyCode": 65})
            await cmd("Input.dispatchKeyEvent", {"type": "keyUp", "modifiers": 2, "key": "a", "code": "KeyA", "windowsVirtualKeyCode": 65})
            await asyncio.sleep(0.08)
            await cmd("Input.insertText", {"text": val})
            await asyncio.sleep(0.12)

        # 3. 填 rows 行
        for row in range(rows):
            info = NAMES[start + row]
            await fill(row*4 + 0, info["first"])
            await fill(row*4 + 1, info["last"])
            await fill(row*4 + 2, info["acc"])
        print(f"填寫 {NAMES[start]['acc']}~{NAMES[start+rows-1]['acc']}")

        # 4. blur + 驗證修正
        await cmd("Input.dispatchMouseEvent", {"type": "mousePressed", "x": 400, "y": 100, "button": "left", "clickCount": 1})
        await cmd("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 400, "y": 100, "button": "left", "clickCount": 1})
        await asyncio.sleep(1.5)
        vals = await eval_js("Array.from(document.querySelectorAll('input')).map(el => el.value)")
        fixed = False
        for row in range(rows):
            if vals[row*4 + 0] != NAMES[start + row]["first"]:
                print(f"!! 修名 {row}"); await fill(row*4 + 0, NAMES[start + row]["first"]); fixed = True
            if vals[row*4 + 1] != NAMES[start + row]["last"]:
                print(f"!! 修姓 {row}"); await fill(row*4 + 1, NAMES[start + row]["last"]); fixed = True
            if vals[row*4 + 2] != NAMES[start + row]["acc"]:
                print(f"!! 修郵 {row}"); await fill(row*4 + 2, NAMES[start + row]["acc"]); fixed = True
        if fixed:
            await cmd("Input.dispatchMouseEvent", {"type": "mousePressed", "x": 400, "y": 100, "button": "left", "clickCount": 1})
            await cmd("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 400, "y": 100, "button": "left", "clickCount": 1})
            await asyncio.sleep(1.5)

        # 5. 等「繼續」啟用並點擊
        st = False
        for _ in range(10):
            st = await eval_js("""
            (function() {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('繼續'));
                return btn ? !btn.disabled : false;
            })()
            """)
            if st:
                break
            await asyncio.sleep(1)
        if not st:
            print("!! 繼續未啟用"); return
        await eval_js("""
        (function() {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('繼續'));
            btn.click(); return true;
        })()
        """)
        print("已提交，等待建立...")

        # 6. 等「關閉」啟用或「已新增使用者」出現
        done = False
        success_text = False
        for _ in range(40):
            await asyncio.sleep(2)
            success_text = bool(await eval_js("document.body.textContent.includes('已新增使用者')"))
            done = await eval_js("""
            (function() {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '關閉');
                return btn ? !btn.disabled : false;
            })()
            """)
            if done:
                break
        if not done and success_text:
            # 帳號已建立但關閉未啟用：嘗試點擊（可能點後啟用）
            await eval_js("""
            (function() {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '關閉');
                if (btn) { btn.click(); return true; }
                return false;
            })()
            """)
            await asyncio.sleep(2)
            done = True
        if not done:
            print("!! 等待建立超時"); return
        if done:
            await eval_js("""
            (function() {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '關閉');
                if (btn && !btn.disabled) { btn.click(); return true; }
                return false;
            })()
            """)
            await asyncio.sleep(3)
        url = await eval_js("location.href")
        print(f"✅ 完成 {NAMES[start]['acc']}~{NAMES[start+rows-1]['acc']} | URL={url}")

asyncio.run(main())
