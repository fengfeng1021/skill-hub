# Skill Hub

我的 AI Agent Skills 收藏庫。收錄好用的 skill，每一個都附一段可以直接貼給 AI 的安裝提示詞 —— 貼過去，AI 自己就把 skill 裝好了。可以複選多個 skill，一次組成一段安裝指令。

網站用 GitHub Pages 直接發佈，同時提供 JSON 接口與 `llms.txt` 給 AI 讀。

## 網站有三頁

| 頁面 | 內容 |
| --- | --- |
| `index.html` | 首頁。介紹怎麼用，下方放幾個精選 skill |
| `skills.html` | Skills 庫。全部收錄，可搜尋、篩選、多選一次複製安裝指令 |
| `api.html` | AI 接口說明。有一段可以直接貼給 AI 的提示詞 |

`design-system.html` 是開發用的元件與動效總覽，刻意不掛在導覽列上（也標了 `noindex`）。

---

## 快速開始

```bash
npm run validate && npm run build && npm run dev
```

`npm run dev` 會在 http://localhost:4321 開起本機預覽。

> 直接用瀏覽器開 `docs/index.html`（`file://`）會失敗，瀏覽器不允許 `file://` 底下的 `fetch`。一定要用 `npm run dev`。

## 第一次設定

編輯 `site.config.json`，把 `owner` 換成你的 GitHub 帳號：

```json
{
  "owner": "你的GitHub帳號",
  "repo": "skill-hub",
  "branch": "main"
}
```

改完重新 `npm run build`。這是發佈 GitHub Pages 用的，同時也是 local 託管 skill 的下載網址來源 —— 沒改的話那些 skill 會下載失敗（只索引外部 repo 的 skill 不受影響）。

## 發佈到 GitHub Pages

1. 建一個 repo（名稱要和 `site.config.json` 的 `repo` 一致），把整包推上去
2. repo → **Settings → Pages → Source** 選 **GitHub Actions**
3. 之後每次 push 到 `main`，`.github/workflows/pages.yml` 會自動 validate → build → 部署

網址會是 `https://<帳號>.github.io/skill-hub/`。

---

## 怎麼收錄新的 skill

**不用手動編輯 JSON。** 三頁下方都有一塊「打名字或貼網址」的輸入框：填上 skill 的名字或 GitHub 網址，
它會產生一段話，複製貼給任何一個 AI，AI 自己去查出處、寫 registry、驗證、build。可以選「只收錄」或「收錄並安裝」。

輸入框會自己判斷你給的是什麼：

| 你輸入 | 判定 |
| --- | --- |
| `https://github.com/xxx/yyy` | 網址 |
| `xxx/yyy` | GitHub repo 簡寫，自動補成完整網址 |
| `shadcn ui` | 只有名字，產生的提示詞會要求 AI 先找出處、找到多個先讓你確認 |

或者開著這個資料夾直接跟 AI 說：

> 我找到一個不錯的 skill：https://github.com/xxx/yyy，幫我收進去

> 這個資料夾是我自己寫的 skill，收錄一下

AI 會照 [CLAUDE.md](CLAUDE.md) 的流程判斷來源類型、抓 SKILL.md、寫 registry、重新 build。外部維護中的 repo 只做索引（`source.kind: "github"`），自製或已無人維護的則把檔案複製進 `skills/<id>/` 由本 repo 託管（`local`）。

一套 skill 被官方拆成好幾個資料夾（例如 GSAP 的 core / timeline / scrolltrigger …）時，收成**一筆**、用 `parts` 列出每一份，安裝提示詞會要求整組一起裝。

### summary 要寫成白話一句話

卡片上只會顯示 `summary` 這一句。標準只有一個：**完全不懂程式的人看一眼就知道這是幹嘛的**。

| | |
| --- | --- |
| ✅ | 讓網頁上的東西會動起來，淡入、滑動、跟著捲動都行。 |
| ❌ | GreenSock 官方動畫 skill 全套：tween、時間軸、ScrollTrigger、外掛與效能。 |

繁體中文、25 字內、只講「能幫我做到什麼」，不要術語、不要功能羅列。技術細節寫進 `description`，那是點開卡片才看的。`npm run validate` 會抓太長、術語與羅列句型並警告。

這條規則也寫進了 `api/index.json` 的 `forAI.howToContribute`，其他 AI 讀接口時會照著做。

要手動加的話：

```bash
node scripts/add-skill.mjs --help
```

---

## 給 AI 的接口

| 路徑 | 內容 |
| --- | --- |
| `docs/llms.txt` | 純文字總覽，一次讀完整個庫 |
| `docs/api/index.json` | 全部資料 + 安裝提示詞模板（主要接口） |
| `docs/api/skills/<id>.json` | 單一 skill，`installPrompt` 欄位可直接貼給 AI |
| `docs/api/tags.json` | 分類與標籤統計 |
| `docs/api/skills.md` | 人類可讀的表格清單 |

發佈後同樣的路徑接在網站網址後面即可，例如 `https://<帳號>.github.io/skill-hub/api/index.json`。

**這些全部是 build 產物，不要手改。** 要改就改 `registry/skills/*.json` 再 `npm run build`。

---

## 專案結構

```
registry/skills/*.json      唯一的資料來源，收錄就是改這裡
registry/schema.json        registry 欄位定義
skills/<id>/                local 託管的 skill 實體檔案
scripts/
  build.mjs                 產生 docs/api/*、llms.txt、skills.md
  validate.mjs              檢查 registry 格式與必填欄位
  add-skill.mjs             指令式新增／更新
  serve.mjs                 本機預覽伺服器
docs/                       GitHub Pages 根目錄
  index.html                首頁：介紹 + 精選幾個 skill
  skills.html               Skills 庫：搜尋、篩選、多選安裝
  api.html                  AI 接口說明
  design-system.html        元件與動效總覽 ← 改設計先改這裡（不掛導覽列）
  assets/css/tokens.css     設計 token（顏色／間距／圓角／動畫曲線）
  assets/css/components.css 所有元件樣式
  assets/css/site.css       頁面區塊樣式（頁首、步驟、接口卡、CTA …）
  assets/js/motion.js       所有 GSAP 共用動效
  assets/js/components.js   元件行為（modal / 複製 / 主題切換 …）
  assets/js/overlays.js     三頁共用的浮層（詳情、安裝提示詞、操作列、toast）
  assets/js/request-box.js  三頁共用的收錄請求：打名字或貼網址 → 產生給 AI 的提示詞
  assets/js/app.js          首頁與 Skills 庫的資料串接
  assets/js/page.js         AI 接口頁的資料串接
site.config.json            GitHub 帳號、repo、安裝路徑設定
```

## 設計方式

元件先做好、再放進頁面 —— 不在頁面裡臨時做元件再一個個微調。

- 樣式只用 `tokens.css` 的變數，不寫死色碼與秒數
- 動效全部集中在 `motion.js`，頁面上用 `data-motion="..."` 綁定，不寫一次性的 `gsap.to()`
- 新元件先進 `design-system.html` 驗過，再用到實際頁面
- 三頁共用的浮層寫在 `overlays.js`，不在每個 HTML 各複製一份
- 動效統一走 `gsap.matchMedia()`，`prefers-reduced-motion` 自動生效

動畫用 GSAP 3（core + ScrollTrigger + Flip，CDN 載入，無建置步驟）。

## 需求

Node.js 18 以上。零相依套件，不需要 `npm install`。
