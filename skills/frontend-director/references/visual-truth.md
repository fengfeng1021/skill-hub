# Signature Visual Truth

Use this reference whenever a task creates or changes visible UI. Its purpose is to enforce the honesty baseline (no faking), not to set a creativity ceiling. Style freedom is governed by [creative-tier.md](creative-tier.md): the higher the tier, the more the creative surface expands — this file only ever narrows what may be *claimed*, never what may be *attempted*.

## 定位：誠信底線 vs 設計標準

- 本檔案只管「誠信」：事實性主張不得造假，視覺不得聲稱自己不存在的細節。
- 「設計好不好看、大不大膽」不是本檔案管的事；那是 impeccable／taste／ui-ux-pro-max 與 creative-tier 的職責。
- 非事實性視覺（藝術、品牌、抽象構成）在 Tier 3 可使用 `intentional-abstraction`／`generated-illustration` 作為主視覺，只需誠實標示（見 §2.6）。
- 自動拒絕模式（§3）只適用於「以假圖冒充真實主張」的情況；抽象藝術或風格化構成不因「不寫實」而被拒絕。

## 1. Name the signature visuals before implementation

A signature visual is any image, rendered object, map, chart, hero scene, product view, artifact, or detail state that carries the page's identity or factual claim. Record each one in the acceptance contract and UI plan. A page normally has one to five; do not classify decorative dividers or minor icons as signature visuals.

For every signature visual record:

- its user-facing claim and whether that claim is factual;
- one truth mode: `sourced`, `procedural-validated`, `generated-illustration`, or `intentional-abstraction`;
- asset or algorithm provenance, license, implementation files, and target desktop/mobile/detail views;
- a task that owns acquisition or generation, implementation, comparison, and repair.

## 2. Truth-mode rules

- `sourced`: use a traceable asset from an authoritative or appropriate source and record its URL/path and license.
- `procedural-validated`: render from a documented model or dataset; cite the model/data and verify scale, domain, units, bounds, and camera coverage.
- `generated-illustration`: AI-generated or artist-created imagery is allowed only when the UI presents it as illustration, not documentary fact.
- `intentional-abstraction`: a deliberately non-realistic representation is allowed only when it is honest, visually coherent, and does not imply factual detail it does not contain.

A factual scientific, medical, geographic, financial, historical, museum, or product-identification visual MUST use `sourced` or `procedural-validated`. A generated image or decorative approximation cannot be labelled or implied to be factual.

## 2.5 Sourced 資產取得程序（讓寫實路徑可落地）

`procedural-validated` 的抽象幾何與 `sourced` 的寫實資產是並存選項，不是二選一。要走向寫實路徑時，依此程序取得資產，任何一步失敗才退回程序化：

1. 優先使用明確授權圖庫（Unsplash License、Pexels License、Pixabay License、Openverse／CC 授權搜尋、維基共享資源）或專案方自有照片。
2. 下載後 **vendored 進專案**（如 `public/assets/photos/`），不得在執行期外連圖庫 URL（離線可用、來源可追）。
3. 每個資產在 `sources.md`（或等價來源文件）記錄：`uri`、`license`、`author`、下載日期、與專案事實主張的相符性說明（例如「衣索比亞高原咖啡園，與耶加雪夫產區地貌相符」）。
4. 資產必須與其聲稱的畫面相符；找不到相符資產時，記錄搜尋失敗與理由，再退回程序化或明確標示的抽象，不允許用「神似但不同」的資產冒充。
5. 照片與程序化資料視覺可以共存：寫實資產擔任氛圍與場景層，程序化 SVG 擔任資料層（剖面、地圖、圖表）。

## 2.6 非事實性場景的創意放寬（依 Creative Tier）

[creative-tier.md](creative-tier.md) 的 Tier 決定真實性規則的鬆緊：

- **Tier 1／2**：維持上述嚴格規則；生成與抽象視覺僅在明確標示時可用。
- **Tier 3（創意機構、作品集、藝術、品牌）**：只對**非事實性**視覺放寬——抽象構成、藝術背景、動態場景、實驗字型可以使用 `intentional-abstraction` 或 `generated-illustration` 作為主視覺，只需「誠實抽象」：視覺不聲稱自己不存在的細節、不冒充紀實。**事實性畫面（科學、地理、金融、歷史、產品辨識、人物照）在任何 Tier 都維持 §2 的嚴格規則**。
- 放寬不清除品質：Tier 3 的創意視覺同樣要過 §3.5 卓越門檻與自動拒絕模式（不得用漸層圓球冒充產品、不得共用貼圖冒充原創）。

## 3.5 卓越門檻（Excellence Bar）— 非劣檢查不夠

所有非劣檢查（可辨識、非佔位、符合主張）只是及格線。每個簽章視覺在 Gate 前必須通過以下**正面 craft 檢查**（在 signature-visual-plan 逐項記錄）：

- EX-1｜視覺深度：場景至少有前景／中景／後景三層，或資料圖表包含不只一層資訊（網格、刻度、標註）。
- EX-2｜資產或技法品質：使用真實授權資產；程序化視覺則至少具備編輯級構成（命名、字級層次、格線、比例設計），不得是單一形狀＋單一漸層。
- EX-3｜資訊排版：圖內有地圖式或雜誌式邊註（名稱、座標、數值、出處），像出版物的一頁，不像程式輸出。
- EX-4｜反複製檢查：同一頁面兩個以上同類簽章視覺必須在形狀、色彩與特徵上可區分，不得共用同一套漸層配方。
- EX-5｜bolder 反向審查：在 UI Gate 前，對每個簽章視覺做一次「如何讓它更大膽」的替代方案書面比較（至少記錄 1 個被否決的更大膽方案與理由）；沒有方案就是該產品的識別力不足，回到設計階段。

任何 EX 檢查為 false 時，簽章視覺不得通過 Gate，也不得用 Lighthouse 分數、build 成功或「符合非劣檢查」抵銷。

## 3. Automatic rejection patterns

Reject the UI and return to the earliest responsible task when a signature visual uses any of these shortcuts:

- a generic CSS gradient circle, flat textureless sphere, emoji, stock placeholder, wireframe, or arbitrary contour line in place of the claimed object;
- one gradient, silhouette, texture, or decorative recipe reused for distinct entities that should be visually distinguishable;
- fake maps, invented data, decorative charts, impossible scale/camera bounds, or labels that claim more truth than the rendering contains;
- a tiny thumbnail that looks acceptable only because defects are hidden, while the modal/detail view has no additional craft;
- a broken or missing asset silently replaced by unrelated decoration;
- “looks premium,” a detector score, Lighthouse, or successful build used as evidence of visual fidelity.

If trustworthy assets or tooling are unavailable, choose and label an honest abstraction or change the visual direction. Never fake realism to preserve the original concept.

## 4. Implementation loop for each signature visual

1. Save a reference/provenance note before coding.
2. Capture or define a failure-first comparison that exposes the placeholder, false claim, repeated identity, incorrect scale, or missing detail.
3. Implement the smallest truthful complete visual, including loading, missing-asset, and narrow-screen behavior.
4. Render the actual page at desktop and mobile sizes and open the largest available detail state.
5. Compare the result with its source/model. Repair until every binary check below passes.
6. Record all evidence in `.agent/evidence/visual-evidence.json` and validate it with:

   ```text
   workflowctl validate-visual-evidence --manifest .agent/evidence/visual-evidence.json
   ```

## 5. Blind review protocol

When the host can delegate or request a human review, give the reviewer only the brief, source/reference material, and actual screenshots—not the implementation report or author's self-assessment. Ask the reviewer to judge each signature visual with these binary checks:

- recognizable without its text label;
- visually distinct from other entities;
- not a placeholder or generic decoration;
- truthful to the claim made by the interface;
- materially matches its cited reference/model;
- remains crafted in the full-size detail view.

Any `false` result fails `visual-fidelity`. Fix the implementation and repeat the review. If independent review is unavailable, use `degraded-self-review`, disclose that limitation in the manifest and final report, and perform a separate adversarial pass after clearing prior implementation commentary from the immediate context.

## 6. Required evidence manifest

Use `schemas/visual-evidence.schema.json`. The manifest must list at least one signature visual when UI work occurred, reference existing implementation files, store every desktop/mobile/detail screenshot as `{ "path": "...", "sha256": "..." }`, contain provenance for every factual visual, have an empty `issues` array, and use `verdict: "pass"`. Screenshots must be real PNG, JPEG, or WebP files; the controller verifies their hashes so an image cannot be replaced after review. The controller also applies the factual truth-mode rule.

Minimal shape:

```json
{
  "schemaVersion": 1,
  "surface": "product home and detail",
  "reviewer": { "mode": "independent-agent", "id": "reviewer-1", "blind": true },
  "signatureVisuals": [
    {
      "id": "hero-object",
      "role": "hero",
      "claim": "The documented object shown in the hero",
      "factual": true,
      "truthMode": "sourced",
      "sources": [
        { "uri": "https://authoritative.example/object", "license": "CC BY 4.0", "note": "identity and appearance reference" }
      ],
      "implementationFiles": ["src/components/Hero.tsx"],
      "screenshots": {
        "desktop": { "path": "reports/hero-desktop.png", "sha256": "<64 lowercase hex characters>" },
        "mobile": { "path": "reports/hero-mobile.png", "sha256": "<64 lowercase hex characters>" },
        "detail": { "path": "reports/hero-detail.png", "sha256": "<64 lowercase hex characters>" }
      },
      "checks": {
        "recognizableWithoutLabel": true,
        "entityDistinct": true,
        "notPlaceholder": true,
        "truthfulToClaim": true,
        "referenceMatch": true,
        "fullSizeCraft": true
      },
      "notes": "Compared against the cited reference at all required sizes."
    }
  ],
  "verdict": "pass",
  "issues": []
}
```

The integration gate records the manifest itself as the `visual-fidelity` evidence. A passed UI phase cannot mark this check manual or not applicable.
