#!/usr/bin/env python3
"""audit.py 正式自測（skill 內建測試）。用法：python scripts/test_audit.py"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

AUDIT_PATH = Path(__file__).parent / "audit.py"
spec = importlib.util.spec_from_file_location("audit", AUDIT_PATH)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

GOOD_HTML = """<!DOCTYPE html><html><body>
<form>
  <label for="email">Email</label>
  <input type="email" id="email" style="color:#111111; font-size:16px">
  <label for="pw">密碼</label>
  <input type="password" id="pw" style="color:#111111">
  <button type="submit" style="height:48px;width:220px">登入</button>
  <a href="#">忘記密碼？</a>
</form>
<button type="button">次要動作</button>
</body></html>"""

BAD_HTML = """<!DOCTYPE html><html><body>
<form>
  <input type="email" id="email" placeholder="輸入 email" style="color:#888888; font-size:14px">
  <input type="password" id="pw" placeholder="密碼" style="color:#888888">
  <button type="submit" style="height:48px;width:200px">登入</button>
  <button type="button" style="height:48px;width:200px">註冊</button>
</form>
<div onclick="doSomething()">按這裡</div>
<a href="#" style="height:18px">小連結</a>
</body></html>"""


class TestAudit(unittest.TestCase):
    def test_good_html_scores_high(self):
        r = audit.audit(GOOD_HTML)
        self.assertGreaterEqual(r["score"], 90, f"好案例應 ≥90，得到 {r['score']}")

    def test_bad_html_fails_gate(self):
        r = audit.audit(BAD_HTML)
        self.assertLess(r["score"], 80, f"壞案例應 <80，得到 {r['score']}")

    def test_bad_html_catches_all_categories(self):
        r = audit.audit(BAD_HTML)
        cats = {cat for _, cat, _ in r["issues"]}
        for expected in ("contrast", "semantic", "form", "hierarchy", "target-size"):
            self.assertIn(expected, cats, f"缺少 [{expected}] 檢查")

    def test_good_html_no_label_for_false_positive(self):
        r = audit.audit(GOOD_HTML)
        cats = {cat for _, cat, _ in r["issues"]}
        self.assertNotIn("form", cats, "label for 關聯不應誤報")

    def test_json_serializable(self):
        r = audit.audit(BAD_HTML)
        json.dumps({"score": r["score"], "issues": r["issues"]}, ensure_ascii=False)

    def test_file_input_matches_string_input(self):
        r_str = audit.audit(BAD_HTML)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.html"
            p.write_text(BAD_HTML, encoding="utf-8")
            r_file = audit.audit(p.read_text(encoding="utf-8"))
        self.assertEqual(r_file["score"], r_str["score"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
