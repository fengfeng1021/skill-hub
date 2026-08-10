---
name: frontend-director
description: 前端總指揮——前端體驗與交付的單一入口。任何「設計、美化、改版、審查」網頁或 App 畫面、需要配色/字體/排版/動效建議、要模仿某網站風格、要建立品牌設計系統、或要規劃使用者互動與導覽時使用；前端程式碼交付前自動觸發品質與安全閘門。整合 Impeccable、UI UX Pro Max、Taste、Hue、GSAP、interaction-experience-design 六個設計 skill 與 delivery-quality-gate（品質閘門＋安全審查），依四階段流程執行（UI → UX → 動效 → 品質閘門），每階段有完成標準、交付前有最終清單——不漏階段、不漏把關。
version: 3.0.0
---

# 前端總指揮（Frontend Director）

> **定位：前端體驗與交付的總指揮。**「設計」在這裡指的是完整前端體驗——視覺（UI）、互動（UX）、動效（Motion），到交付前的品質與安全。本入口整合 7 個收錄項目：六套設計能力 + 交付品質閘門，四階段完成前端交付，一個入口，全套服務。

## 調度總則（怎麼做到不漏）

1. **開場宣告**：接到任務先宣告「本任務將走哪幾個階段、每階段用哪個 skill、產出什麼」，讓使用者可以修正後再開始。
2. **逐階段執行**：一階段一階段做，每階段完成自檢其 DoD（完成標準），**未過 DoD 不進下一階段**。
3. **交付前最終清單**：全部完成後，逐項打勾回報（見文末），缺一項就補做。
4. **誠實回報**：每個階段結束回報「階段 x/y 完成＋驗證結果」，讓使用者監督；不宣稱沒驗證過的事。

## 四階段流程（重要：不是只做 UI）

```
階段一　UI 底子（畫面好看）
　→ Impeccable 判斷模式＋品質地板、UI UX Pro Max 查規則、Taste 學風格、Hue 品牌統一
階段二　UX 互動（好用）
　→ interaction-experience-design：主動作層級、資訊架構與導覽、疊頁返回、可學習性、操作回饋
階段三　動效加分（有生命）
　→ GSAP：有意義的動效（引導、回饋、連續性）
階段四　品質閘門（交付前把關，橫切關卡）
　→ 觸發 delivery-quality-gate：驗證 → 審查 → 安全，三關全過才准交付
```

品質閘門是**橫切關卡**：任務完全不涉及畫面（純功能、修 bug、重構）時，跳過階段一～三，直接進入階段四執行。

## 每階段 DoD（完成標準，未過不進下一階段）

| 階段 | 完成標準（DoD） |
|---|---|
| 一 UI | 文字對比 ≥4.5:1、焦點環可見、8px 間距系統、無反 AI 味（過度陰影／彩虹漸層／假 3D／萬用紫） |
| 二 UX | 一頁一個主動作、導覽深度 ≤3 層、下鑽可返回、所有操作有回饋、30 秒可上手 |
| 三 動效 | 動效有意義（引導／回饋／連續性）、尊重 prefers-reduced-motion、優先 transform/opacity |
| 四 品質閘門 | 驗證指令已跑＋輸出已確認、審查員已看過、安全已查（委派 delivery-quality-gate 執行） |

## 自動分配：任務 → 主 skill → 輔助 skill

| 任務類型 | 主 skill | 輔助 skill |
|---|---|---|
| 新介面／整體設計 | Impeccable（shape/設計判斷） | UI UX Pro Max（風格查詢） |
| 美化現有畫面 | Impeccable（polish/critique） | UI UX Pro Max（規則檢查） |
| 模仿某網站風格 | Taste（扒設計 DNA） | Impeccable（落地打磨） |
| 建立品牌／設計系統 | Hue（生成設計語言） | UI UX Pro Max（規則） |
| 動效設計 | GSAP | Impeccable（animate） |
| **互動／導覽／流程設計** | **interaction-experience-design**（讀其 SKILL.md 決策樹選 references） | Impeccable（Operate 模式） |
| 審查／找出問題 | Impeccable（audit/critique） | interaction-experience-design（互動檢查） |
| **任何程式碼交付** | **delivery-quality-gate**（品質閘門總指揮） | verification-before-completion 等（由它分配） |

## 協同工作流（標準 8 步）

1. **開場宣告**：宣告階段與產出（見調度總則）。
2. **判斷模式**（Impeccable）：Persuade（說服）/ Operate（操作）/ Read（閱讀）/ Experience（體驗）。
3. **學風格**（Taste）：若要模仿某風格，分析其 tokens（色彩/字體/間距/圓角/陰影/格線）＋背後的決策邏輯。
4. **查規則**（UI UX Pro Max）：依任務查風格、配色、字體搭配；對照 10 級優先度（無障礙＞觸控＞效能＞風格＞版面＞字體色彩＞動效＞表單＞導覽＞圖表）。
5. **品牌統一**（Hue）：建立色彩 tokens、字體階層、間距尺度、明暗模式，所有產出符合。
6. **設計底子**（Impeccable）：依模式設計，套用階段一 DoD。
7. **互動與動效**（interaction-experience-design + GSAP）：套用階段二、三 DoD。
8. **品質閘門**（delivery-quality-gate）：委派品質閘門總指揮執行驗證→審查→安全，全過才交付。

## 六家精華（濃縮版，環境有原檔時優先讀原檔）

### Impeccable — 判斷力
- 四模式：Persuade（行銷頁：大膽、抓住注意）/ Operate（App、儀表板：掃讀性、一致性優先）/ Read（文件：結構清楚）/ Experience（作品集：作品先行）
- 品質地板：文字對比 ≥4.5:1、焦點環可見、8px 間距系統、留白節奏
- 反 AI 味：避免過度陰影、彩虹漸層、假 3D、萬用紫色
- 精修保留原樣，重設計才替換；一次批次修完，不要無限打磨

### UI UX Pro Max — 規則
- 關鍵數值：觸控目標 ≥44×44px、正文 ≥16px、行高 ≥1.5、動效 150-300ms、間距 ≥8px
- 反模式：emoji 當圖示、只靠 hover 回饋、灰對灰、placeholder 當欄位標籤、橫向捲動、移除焦點環

### Taste — 學風格
- 分析四層：色彩系統、字體階層、間距與圓角、格線與陰影
- 每層都要問「為什麼這樣做」，理解取捨才能應用到沒看過的頁面

### Hue — 品牌系統
- 完整設計語言：色彩 tokens（主/輔/語義色）、字體、間距、元件規格、明暗模式
- 兩次會話產出的東西視覺必須一致

### GSAP — 動效
- 動效要有意義（引導注意、狀態回饋、空間連續性），不是裝飾
- 尊重 prefers-reduced-motion；優先 transform/opacity（效能）

### interaction-experience-design — 互動體驗（學術理論基礎）
- 一頁一個主動作：主動作大按鈕、次要動作降級（Fitts 費茲定律）
- 資訊架構：功能先分組再導覽、深度 ≤3 層、10 個功能不要 10 個分頁（Hick 希克定律、IA 學）
- 疊頁與返回：下鑽頁蓋在舊頁上、返回固定位置、前景後景可區分（IA 導覽系統、Nielsen 啟發式 3）
- 可學習性：用慣例（Jakob 定律）、30 秒上手、狀態可見（Nielsen 啟發式 1、認知負荷理論）
- 操作回饋：按了要有反應、錯誤提示在欄位旁（Nielsen 啟發式 9）
- 詳細學理（Nielsen 10 啟發式、Shneiderman 8 法則、Gestalt、WCAG 等）見原檔

## 最終交付清單（宣告完成前逐項打勾回報）

- [ ] 開場宣告的每個階段都執行完畢，沒有跳過
- [ ] 每個階段的 DoD 都自檢通過（未過的已補做）
- [ ] 品質閘門三關（驗證／審查／安全）已由 delivery-quality-gate 確認
- [ ] 回報中包含各階段實際驗證結果（貼輸出或截圖），不是「應該可以」

## 常見遺漏警示（歷史漏做模式）

- 只做 UI 就交差 → 沒走 UX／動效／品質閘門
- 跳過品質閘門直接說「完成了」 → 違反調度總則
- 沒宣告就開做 → 使用者無法監督階段完整性
- 說「測過了」但沒證據 → 等於沒測
- 只讀濃縮精華沒讀原檔 → 環境有原檔時必須先讀

## 原檔讀取指示

先依目前 Agent 的官方 skill 機制找出它實際載入的 skill 目錄。若其中存在下列 skill，**先讀原檔再行動**；不要預設品牌或猜測固定路徑。本檔濃縮版只是沒有原檔時的最低標準：
- `impeccable/`（SKILL.md + references/）
- `ui-ux-pro-max/`（SKILL.md + references/quick-reference.md；scripts/search.py 可查詢）
- `taste/`（SKILL.md + references/）
- `hue/`（SKILL.md + scripts/）
- `gsap-*/`（GSAP 動效系列）
- `interaction-experience-design/`（SKILL.md）
- `delivery-quality-gate/`（品質閘門總指揮，品質/安全細節由它指揮；它會讀 superpowers 三件套與 mantis-*/）
