---
name: frontend-design-director
description: 前端設計總指揮。任何「設計、美化、改版、審查」網頁或 App 畫面、需要配色/字體/排版/動效建議、要模仿某個網站風格、要建立品牌設計系統、或要規劃使用者互動與導覽時使用。自動整合 Impeccable、UI UX Pro Max、Taste、Hue、GSAP、interaction-experience-design 六個設計 skill 的精華與分工，並依四階段流程執行（UI → UX → 動效 → 品質閘門）——一個入口，全套服務。交付程式碼前自動套用 verification-before-completion、requesting-code-review、receiving-code-review（obra/superpowers）與 mantis 安全審查。
version: 2.2.0
---

# 前端設計總指揮（Design Director）

整合六個設計 skill 的總指揮：**Impeccable**（判斷力/打磨）、**UI UX Pro Max**（規則/資料庫）、**Taste**（學風格）、**Hue**（品牌系統）、**GSAP**（動效）、**interaction-experience-design**（互動體驗）。

## 四階段流程（重要：不是只做 UI）

使用者說「設計／做一個畫面」時，依序完成四個階段，**每階段完成再進下一階段**，不要只做其中一項：

```
階段一　UI 底子（畫面好看）
　→ Impeccable 判斷模式＋品質地板、UI UX Pro Max 查規則、Taste 學風格、Hue 品牌統一
階段二　UX 互動（好用）
　→ interaction-experience-design：主動作層級、資訊架構與導覽、疊頁返回、可學習性、操作回饋
階段三　動效加分（有生命）
　→ GSAP：有意義的動效（引導、回饋、連續性）
階段四　品質閘門（程式碼乾淨、安全，才叫完成）
　→ verification-before-completion（驗證後才能宣稱完成）、requesting-code-review（派審查員）、mantis 安全審查
```

執行時明確回報「目前在第幾階段」，完成一階段再進行下一階段，讓使用者知道設計是有流程的。

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
| **程式碼品質驗收** | **verification-before-completion**（先驗證再宣稱完成） | requesting-code-review（交付前派審查員） |
| **程式碼安全** | **mantis-threat-model / mantis-review** | mantis-patch（修補漏洞） |

## 協同工作流（標準 8 步）

1. **判斷模式**（Impeccable）：Persuade（說服）/ Operate（操作）/ Read（閱讀）/ Experience（體驗）。
2. **學風格**（Taste）：若要模仿某風格，分析其 tokens（色彩/字體/間距/圓角/陰影/格線）＋背後的決策邏輯。
3. **查規則**（UI UX Pro Max）：依任務查風格、配色、字體搭配；對照 10 級優先度（無障礙＞觸控＞效能＞風格＞版面＞字體色彩＞動效＞表單＞導覽＞圖表）。
4. **品牌統一**（Hue）：建立色彩 tokens、字體階層、間距尺度、明暗模式，所有產出符合。
5. **設計底子**（Impeccable）：依模式設計，套用品質地板。
6. **互動體驗**（interaction-experience-design）：主動作、資訊架構、導覽與疊頁返回、可學習性、操作回饋——讓「好用」。
7. **動效加分**（GSAP）：有意義的動態，不裝飾。
8. **品質閘門**（superpowers + mantis）：先驗證（證據優先）、再審查、後檢查安全，全過才交付。

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

## 品質閘門三件套（obra/superpowers，270k★ 開發方法論）

### verification-before-completion — 完成前驗證（品質門）
- 要宣稱「完成／修好／測試通過」前，**先跑驗證指令並確認輸出**；證據先於斷言
- 沒跑驗證就說完成 = 違反本 skill 的硬規則

### requesting-code-review — 交付前審查（閉環）
- 主要功能完成、合併前，派 code-reviewer 子代理（讀 `code-reviewer.md`）審查
- 給審查員精確的上下文與評估標準，不丟整個 session 歷史；早審、常審

### receiving-code-review — 正確接收意見
- 收到審查意見：先驗證再實作，不懂就問；技術正確性優先於客氣，不盲從也不表演式同意
- 若意見技術上有問題，用證據說明，不要照單全收

## 安全審查（google/mantis，Google 官方 18-skill 流水線）

- 前端交付前對照 `mantis-threat-model`（威脅建模）→ `mantis-review`（審查）→ `mantis-patch`（修補）
- 典型檢查：XSS／注入、敏感資訊外洩、權限過寬、DOM clobbering、第三方套件風險
- ⚠️ mantis 會產生並執行自動化程式碼，**只在隔離環境使用**；所有發現需人工複核後才回報

## 原檔讀取指示

先依目前 Agent 的官方 skill 機制找出它實際載入的 skill 目錄。若其中存在下列 skill，**先讀原檔再行動**；不要預設品牌或猜測固定路徑。本檔濃縮版只是沒有原檔時的最低標準：
- `impeccable/`（SKILL.md + references/）
- `ui-ux-pro-max/`（SKILL.md + references/quick-reference.md；scripts/search.py 可查詢）
- `taste/`（SKILL.md + references/）
- `hue/`（SKILL.md + scripts/）
- `gsap-*/`（GSAP 動效系列）
- `interaction-experience-design/`（SKILL.md）
- `verification-before-completion/`、`requesting-code-review/`（含 code-reviewer.md）、`receiving-code-review/`（superpowers 品質閘門）
- `mantis-*/`（Google 安全審查流水線，18 個 skill）
