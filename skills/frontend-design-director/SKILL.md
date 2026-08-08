---
name: frontend-design-director
description: 前端設計總指揮。任何「設計、美化、改版、審查」網頁或 App 畫面、需要配色/字體/排版/動效建議、要模仿某個網站風格、要建立品牌設計系統時使用。自動整合 Impeccable、UI UX Pro Max、Taste、Hue、GSAP 五個設計 skill 的精華與分工——一個入口，全套服務。
version: 1.0.0
---

# 前端設計總指揮（Design Director）

整合五個設計 skill 的總指揮：**Impeccable**（判斷力/打磨）、**UI UX Pro Max**（規則/資料庫）、**Taste**（學風格）、**Hue**（品牌系統）、**GSAP**（動效）。

## 自動分配：任務 → 主 skill → 輔助 skill

| 任務類型 | 主 skill | 輔助 skill |
|---|---|---|
| 新介面／整體設計 | Impeccable（shape/設計判斷） | UI UX Pro Max（風格查詢） |
| 美化現有畫面 | Impeccable（polish/critique） | UI UX Pro Max（規則檢查） |
| 模仿某網站風格 | Taste（扒設計 DNA） | Impeccable（落地打磨） |
| 建立品牌／設計系統 | Hue（生成設計語言） | UI UX Pro Max（規則） |
| 動效設計 | GSAP | Impeccable（animate） |
| 審查／找出問題 | Impeccable（audit/critique） | UI UX Pro Max（無障礙/效能） |

## 協同工作流（標準 6 步）

1. **判斷模式**（Impeccable）：這頁面是 Persuade（說服）、Operate（操作）、Read（閱讀）還是 Experience（體驗）？決定設計標準。
2. **學風格**（Taste）：若要模仿某風格，分析其 tokens（色彩/字體/間距/圓角/陰影/格線）＋背後的決策邏輯（為什麼），不只複製數值。
3. **查規則**（UI UX Pro Max）：依任務查風格、配色、字體搭配；對照 10 級優先度（無障礙＞觸控＞效能＞風格＞版面＞字體色彩＞動效＞表單＞導覽＞圖表）。
4. **品牌統一**（Hue）：有品牌或設計系統需求時，建立色彩 tokens（主/輔/語義）、字體階層、間距尺度、明暗模式，之後所有產出都符合。
5. **設計與打磨**（Impeccable）：依模式設計，套用品質地板；一次批次修改、一輪驗證，不過度打磨。
6. **動效加分**（GSAP）：需要動態時加上，有意義、不裝飾。

## 五家精華（濃縮版，環境有原檔時優先讀原檔）

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

## 原檔讀取指示

若環境（~/.claude/skills/ 或專案 .claude/skills/）存在下列 skill 目錄，**先讀原檔再行動**，本檔濃縮版只是沒有原檔時的最低標準：
- `impeccable/`（SKILL.md + references/：craft-floor.md、new-work.md、critique.md 等）
- `ui-ux-pro-max/`（SKILL.md + references/quick-reference.md；scripts/search.py 可查詢）
- `taste/`（SKILL.md + references/）
- `hue/`（SKILL.md + scripts/）
- `gsap-*/`（GSAP 動效系列）
