# 動效基線

動效只用於引導注意、說明空間關係、確認狀態或維持連續性。沒有明確目的就不新增動畫。

## 決策順序

1. 先沿用專案既有動畫方案；不要為了使用某個動效 skill 而替換技術棧。
2. CSS transition 能清楚完成的微互動不用引入新函式庫。
3. 需要時間軸、可逆序列、捲動驅動或複雜協調時才選 GSAP 等方案。
4. 動畫狀態必須從產品狀態推導，不能成為第二套互相競爭的狀態來源。

載入 GSAP Skill 是為了取得動效規格、生命週期、降級與性能知識，不代表必須把 GSAP 函式庫加入產品；簡單微互動仍應選 CSS。只有宿主確實找不到對應 Skill 時才使用 fallback。

## 品質規則

- 優先使用 `transform` 和 `opacity`，避免每幀觸發 layout。
- 動畫可被重複觸發、中斷、快速切換和元件卸載，不留下 timer、listener 或 timeline。
- `prefers-reduced-motion` 下保留完整功能與必要狀態回饋，移除非必要移動、縮放與視差。
- 動畫不延遲主要操作、不遮擋控件、不讓焦點位置與視覺位置分離。
- duration、ease 和 stagger 來自一致 tokens；不要每個元件自行發明數值。
- 捲動綁定與大型動畫要檢查低階裝置、頁籤切換和 resize。

Motion 規劃 Gate 先記錄每段動效目的、reduced-motion 等價行為與中斷／清理策略。實作完成後，integration Gate 必須在正常與 reduced-motion 兩種模式實測，並快速重複操作確認最終狀態、timer、listener 與 timeline 都正確收斂。
