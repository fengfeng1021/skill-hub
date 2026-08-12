# Skill Hub — 給 AI 的操作說明

這是一個 **跨 Agent Skills 收藏庫**（Codex、Claude Code、Cursor、Hermes 等環境都能用）。使用者會用自然語言請你收錄 skill，例如：

> 「我找到一個不錯的 skill：https://github.com/xxx/yyy，幫我收進去」
> 「這個資料夾是我自己寫的 skill，收錄一下」
> 「幫我把 abc skill 的說明更新一下」

也可能是網站上那塊「打名字或貼網址」產生的提示詞（`docs/assets/js/request-box.js`）。
那段話已經把流程列成步驟了，照著做就是下面這一套；**使用者只給名字時，先查出處，找到多個同名的要先讓使用者確認，不要自己挑**。

你的工作就是把它變成 registry 資料、重新 build、然後（使用者同意時）推上 GitHub。

---

## 收錄一個 skill 的標準流程

### 1. 判斷來源類型

| 使用者給的東西 | `source.kind` | 你要做的事 |
|---|---|---|
| GitHub repo 網址 | `github` | 讀取該 repo 的 SKILL.md 取得資訊，**不複製檔案** |
| GitHub repo 內某個子資料夾 | `github` + `subdir` | 同上，記得填 `subdir` |
| 本機資料夾／貼上的 SKILL.md 內容 | `local` | **把檔案複製進 `skills/<id>/`**，由本 repo 託管 |
| 單一檔案網址 / zip | `url` | 記錄網址，必要時下載到 `skills/<id>/` |

判斷原則：**外部維護中的 repo 用 `github` 只做索引**（保持同步、尊重原作者）；**使用者自製或對方已不維護的用 `local` 託管**，確保不會失效。

### 2. 蒐集資訊

盡量從來源自動取得，不要反覆問使用者：

- 用 WebFetch 抓 GitHub repo 的 README 和 `SKILL.md`（raw 網址：`https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>/SKILL.md`）
- SKILL.md 的 frontmatter 有 `name` 與 `description`，直接拿來用
- 作者、授權、star 數從 repo 頁面取得
- **`summary` 一定要自己寫**，而且要白話（規則見下面）

抓不到就用合理預設，只有真的無法判斷（例如不確定是不是同一個 skill 的不同版本）才問使用者。

#### summary 的寫法（最重要的一條）

`summary` 是卡片上唯一會被看到的說明。標準只有一個：**完全不懂程式的人看一眼就知道這是幹嘛的**。

- 繁體中文，**25 字內**，一句完整的話
- 只講「能幫我做到什麼」，不講「用什麼技術做到」
- 不要出現 API、函式庫、外掛、框架、frontmatter、tween 這種術語
- 不要寫成「名稱：功能一、功能二、功能三」的功能羅列
- 技術細節、涵蓋範圍、專有名詞一律寫進 `description`，那才是詳情面板看的

| | |
|---|---|
| ✅ | 讓網頁上的東西會動起來，淡入、滑動、跟著捲動都行。 |
| ❌ | GreenSock 官方動畫 skill 全套：tween、時間軸、ScrollTrigger、外掛與效能。 |

`parts[].summary` 同一套規則。`npm run validate` 會抓太長、術語、羅列句型並警告。

### 3. 寫 registry 檔案

建立 `registry/skills/<id>.json`，格式見 `registry/schema.json`。

- `id`：kebab-case，全庫唯一。已存在就是**更新**而非新增，不要建立 `xxx-2`
- `category`：直接寫中文顯示字串。**先看 `registry/skills/` 現有的分類，能沿用就沿用**，不要每收一個就發明新分類
- `tags`：3–6 個，小寫英文，同樣優先沿用現有標籤
- `install.dirName`：安裝後的資料夾名，**必須等於 SKILL.md frontmatter 的 `name`**，否則 AI 認不出來
- `install.files`：實際檔案清單，讓安裝的 AI 知道要拿哪些檔案
- `install.command`：有官方一行指令（`npx skills add <repo>`、`/plugin marketplace add <owner>/<repo>`）就填，安裝提示詞會請 AI 優先用它，省掉一個個抓檔案
- `prompt`：留 `null`。自動產生的安裝提示詞已經夠用，除非安裝方式特殊（要跑 script、要裝套件、要設環境變數）才自己寫

#### 一套 skill 被拆成多個資料夾時，收成**一筆**

像 GSAP 官方 repo 把內容拆成 `gsap-core`、`gsap-timeline`、`gsap-scrolltrigger`… 8 個資料夾，但那是同一套 skill，AI 用的時候會互相參照、安裝也應該一起裝。**不要拆成 8 筆 registry**，用 `parts` 收成一筆：

```jsonc
"source": { "kind": "github", "url": "…/gsap-skills", "branch": "main", "subdir": "skills" },
"parts": [
  { "dirName": "gsap-core", "name": "Core", "summary": "to／from、ease、stagger…" },
  { "dirName": "gsap-timeline", "name": "Timeline", "summary": "多步驟編排…" }
  // …其餘同理
],
"install": { "command": "npx skills add …", "files": ["SKILL.md"] }
```

- `parts[].subdir` 通常不用填，會自動組成 `<source.subdir>/<dirName>`
- 有 `parts` 就可以省略 `install.dirName`
- 判斷標準：**同一個 repo、同一個作者、實際使用時會一起載入** → 用 `parts`。功能各自獨立、可以只裝其中一個 → 分開收錄

#### 多個既有 skill 組成一套資產時，用 `includes`

入口 skill 若負責統籌多個不同來源的既有收錄項目，這是「精選組合包」，不是同來源多資料夾，也不是可選相依：

```jsonc
"includes": ["impeccable", "ui-ux-pro-max", "taste", "hue", "gsap"]
```

- `includes` 的值是其他 registry id，必須已存在，不能引用自己或形成循環
- 建置後的 `installIds` 會遞迴展開並去重；`installPrompt` 會把入口與全部內容一起安裝
- `parts` = 同一來源套件的實體資料夾；`includes` = 跨來源產品組合；`install.requires` = 執行期相依，三者不要混用

#### 能自動續跑的入口，用 `runtime` 描述執行工作流

`includes` 只解決安裝：保證入口會用到的 Skill 都裝齊。它不代表 Agent 執行時會自動依序調用。入口若有固定階段、條件路由、全程覆蓋層或最後收尾器，要另外加入 `runtime`：

```jsonc
"runtime": {
  "mode": "pipeline",
  "stateArtifact": ".agent/frontend-workflow.md",
  "continueWithoutUserInput": true,
  "ambiguityPolicy": "ask-only-material",
  "stages": [
    { "id": "contract", "name": "需求契約", "skills": ["define-acceptance-contract"], "gate": "需求完整且可測" },
    { "id": "ui", "name": "UI", "skills": ["impeccable"], "optionalSkills": ["taste"], "gate": "雙尺寸渲染通過" }
  ],
  "overlays": ["delivery-quality-gate"],
  "finalizers": ["delivery-quality-gate"]
}
```

- `runtime` 引用的是 registry id，而且必須已被 `includes` 的遞迴安裝清單涵蓋
- `runtime` 是給網站與 AI 快速理解的結構化 metadata；完整的路由條件、階段 Gate、失敗回退與續跑方式仍寫在入口 `SKILL.md`
- 長任務入口要用 `stateArtifact` 留下目前階段、有效證據與下一步，避免跨回合後重做或漏做
- 安裝時裝齊完整組合；執行時一次只讀目前階段需要的 Skill，不要把所有子 Skill 同時塞進上下文

入口改過資料夾或 frontmatter `name` 時，用 `replaces` 列出舊名稱。產生的安裝提示詞會先比對舊入口是否有自訂修改；新版驗證成功後，才把無自訂的舊 `SKILL.md` 改名為 `SKILL.md.disabled`，保留可恢復備份並避免重複觸發。

### 4. local 託管的話，複製檔案

放到 `skills/<id>/`，保留原本的目錄結構（`SKILL.md` + `references/` + `scripts/` 等）。

### 5. 重新 build

```bash
npm run build
```

這會產生 `docs/api/*`（給 AI 和網站讀的 JSON 接口）、`docs/llms.txt`、`docs/api/skills.md`。
**產出的檔案不要手動改**，改 registry 再 build。

### 6. 驗證

```bash
npm run validate
```

要全綠。有錯就修 registry，不要繞過驗證。

### 7. 回報

告訴使用者收錄了什麼、放在哪個分類、目前總數。**除非使用者說要，否則不要自動 commit / push。**

---

## 更新既有 skill

改 `registry/skills/<id>.json` → `npm run build`。`updatedAt` 要更新成今天。

## 移除 skill

刪掉 `registry/skills/<id>.json`（local 託管的話連 `skills/<id>/` 一起）→ `npm run build`。刪除前先跟使用者確認。

---

## 專案結構

```
registry/skills/*.json   ← 唯一的資料來源，收錄就是改這裡
skills/<id>/             ← local 託管的 skill 實體檔案
scripts/build.mjs        ← 產生 docs/api/*、llms.txt
docs/                    ← GitHub Pages 網站根目錄（build 產物 + 手寫前端）
  index.html             ← 首頁：介紹 + 精選幾個 skill
  skills.html            ← Skills 庫：搜尋、篩選、多選安裝
  api.html               ← AI 接口說明
  design-system.html     ← 元件與動效總覽。**開發用，不掛在導覽列上**，改設計先改這裡
  assets/js/motion.js    ← 所有 GSAP 共用動效，元件動效一律從這裡取用
  assets/css/tokens.css  ← 設計 token，顏色間距圓角動畫曲線都在這
  assets/css/components.css ← 所有元件樣式
site.config.json         ← GitHub 帳號、repo 名、安裝路徑設定
```

## 改網站時的規則

1. **動效一律寫在 `motion.js`**，用 `data-motion="..."` 綁到元素上。不要在頁面裡寫一次性的 `gsap.to()`
2. **樣式一律用 `tokens.css` 的變數**，不要在 components.css 裡寫死色碼或秒數
3. 新增元件：先在 `components.css` + `motion.js` 定義，加進 `design-system.html` 展示，**確認沒問題才用到實際頁面**。`design-system.html` 是開發工具，不要加回導覽列或 footer
4. 三個頁面共用的東西寫成獨立模組，不要在每個 HTML 各複製一份：浮層（詳情、安裝提示詞、多選操作列、toast）在 `assets/js/overlays.js`，收錄請求輸入框在 `assets/js/request-box.js`
5. 所有動效都要通過 `prefers-reduced-motion`（`motion.js` 已用 `gsap.matchMedia()` 統一處理，照現有寫法就會自動支援）
