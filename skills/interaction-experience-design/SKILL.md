---
name: interaction-experience-design
description: 專業級「使用者交互體驗」設計 skill。以學術理論為基礎（Nielsen 啟發式評估、Shneiderman 黃金法則、Norman 設計心理學、Fitts/Hick 定律、Miller 7±2、Gestalt 原則、認知負荷理論、資訊架構學、WCAG 無障礙、ISO 9241）。當任務涉及登入流程、多功能 App 組織、導覽與資訊架構、按鈕層級、疊頁與返回、可學習性、操作回饋、可用性審查、無障礙時使用。
version: 2.0.0
---

# 互動體驗設計（Interaction Experience Design）

專業版：不只是「好用」的直覺，而是有**學術理論基礎**的互動設計。視覺設計管「美」，這裡管「人怎麼與系統互動」。

## 一、可用性的定義與衡量（ISO 9241-11）

可用性 = 特定使用者在特定情境下，**有效**（達成目標）、**效率**（資源消耗）、**滿意度**（主觀感受）三者的程度。設計時以這三個維度自問：能完成嗎？要幾步？使用者感覺如何？

## 二、Nielsen 十大啟發式（Heuristic Evaluation，NN/g 2024 版）

可用性審查的學術標準，逐條檢查：

1. **系統狀態可見**（Visibility of System Status）：系統永遠在合理時間內回饋使用者在做什麼。→ 載入中、進度、下載百分比、目前所在頁。
2. **系統與真實世界相符**（Match with Real World）：用使用者的語言（不是系統術語），順著真實世界的習慣。→ 「購物車」不是「Session Cart」；日期照當地格式。
3. **使用者控制與自由**（User Control and Freedom）：誤操作要有「緊急出口」——復原、重做、取消、返回。→ 誤刪可恢復、對話框可逃脫。
4. **一致性與標準**（Consistency and Standards）：同樣的東西同樣的表現；遵循平台慣例。→ 返回位置、圖示意義全站一致；別發明新慣例。
5. **錯誤預防**（Error Prevention）：比好的錯誤訊息更好的是「不讓錯誤發生」。→ 刪除要確認、表單即時驗證、禁用無效按鈕。
6. **辨識勝於回憶**（Recognition rather than Recall）：讓使用者「認得」而不是「記得」。→ 選單顯示所有選項，不靠記憶；常用資訊（帳號、歷史）自動帶入。
7. **彈性與使用效率**（Flexibility and Efficiency of Use）：新手與專家的需求都滿足。→ 捷徑、批次操作、個人化、常用功能可釘選。
8. **美觀與極簡設計**（Aesthetic and Minimalist Design）：畫面只放當下需要的資訊，不讓不相干資訊喧賓奪主。→ 每個多餘元素都是認知負擔。
9. **幫助使用者辨識、診斷、恢復錯誤**（Help Users Recognize, Diagnose, Recover from Errors）：錯誤訊息要白話、指出問題、給解法。→ 「密碼太短（至少 8 碼）」不是「Error 400」。
10. **說明文件與幫助**（Help and Documentation）：需要時找得到，不必先讀完才能用。→ onboarding 引導、工具提示、空狀態說明。

## 三、Shneiderman 八條黃金法則（Designing the User Interface）

1. 一致性（一致性貫穿所有互動）
2. 讓常用使用者能用捷徑（專家效率）
3. 提供有意義的回饋（每個動作都有回饋）
4. 設計對話框讓它結束（動作有開始有結束：確認→執行→結果）
5. 預防錯誤並簡單修正（錯誤防範＋容易復原）
6. 讓動作可反轉（盡可能可復原）
7. 支持內控點（使用者感覺自己主導，不是系統主導）
8. 降低短期記憶負擔（別讓使用者記太多）

## 四、互動設計定律（學術基礎）

- **Fitts's Law（費茲定律）**：目標越大、距離越近，越快點到。→ 主要動作做大按鈕、放拇指區；次要動作小且遠離。
- **Hick's Law（希克定律）**：選項越多，決策越慢。→ 一屏選項收斂到 5-7 個；多餘選項收進「更多」。
- **Miller 7±2（魔法數字七）**：短期記憶一次約能處理 7±2 個單位。→ 導覽項目、步驟數、群組數控制在 5-9。
- **Gestalt 原則（格式塔心理學）**：接近性（相近=一組）、相似性（像=同類）、連續性、封閉性、共同命運（一起動=一組）。→ 用間距與樣式讓使用者「自動」看懂分組，不需說明。
- **Jakob's Law（雅各布定律）**：使用者把大部分時間花在別的系統上，他們期望你的系統像那些。→ 遵循慣例（返回在左上、搜尋在右上），別創新。
- **Norman 設計心理學**（The Design of Everyday Things）：可發現性（Affordance：長得像按鈕的才能點）、對應（控制項與效果的空間對應）、約束（限制錯誤輸入）、回饋、概念模型（使用者心中理解的運作方式）。→ 設計要讓使用者「一看就懂怎麼操作、做了會發生什麼」。

## 五、認知負荷理論（Cognitive Load Theory，Sweller）

工作記憶容量有限：內在負荷（任務本身難度）、外在負荷（介面造成的額外負擔）、增益負荷（學習）。設計目標：**最小化外在負荷**。
→ 減少無關資訊、分步引導、視覺群組、把步驟拆小、讓使用者一次專注一件事。

## 六、資訊架構（Information Architecture，Morville & Rosenfeld）

- **組織方案**：功能多先分類——依任務（工作流程）、依對象（使用者）、依主題、依時間。分類要互斥且完整。
- **心智模型**：使用者心中「東西應該放哪」。→ Card Sorting（卡片分類法）可實測使用者的分類直覺。
- **深度 vs 廣度**：導覽深度 ≤3 層；廣度優先（一層多選項勝過多層深挖）。
- **導覽系統**：全域（側欄/Tab）、局部（頁內）、情境（關聯連結）、麵包屑。側邊欄不是唯一解：主功能用 Tab、次功能用側欄、相關功能用頁內連結、長流程用步驟條。
- **疊頁與返回**：下鑽用疊頁（新頁蓋舊頁），返回固定位置＋滑動手勢，前景後景可區分；深層給標題/麵包屑。

## 七、無障礙（WCAG 2.2 對應）

- 對比度 ≥4.5:1（文字）；操作目標 ≥24×24px（WCAG 2.2 AA）
- 鍵盤可操作、焦點可見、ARIA 標籤、不只靠顏色傳達
- 動效尊重 prefers-reduced-motion

## 八、評估方法（設計完要驗證，不是憑感覺）

1. **啟發式評估**：拿 Nielsen 10 條逐條檢查（低成本、發現大部分問題）
2. **任務分析**：列出關鍵任務，走一遍看幾步能完成
3. **可用性測試**：找真實使用者操作，觀察卡在哪（最有效）
4. **A/B 測試**：不確定時兩個版本實測
5. **心智模型測試**：問使用者「你會在哪裡找 XX 功能」

## 九、反模式清單（不要做）

- ❌ 10 個功能 = 10 個側邊欄分頁（違反組織方案＋Hick's Law）
- ❌ 兩個同尺寸主按鈕競爭（違反 Fitts：沒有主目標）
- ❌ 無返回／返回位置亂跳（違反 Heuristic 3）
- ❌ 深層巢狀無標題無麵包屑（違反 Heuristic 1：使用者迷路）
- ❌ 破壞慣例（違反 Jakob's Law）
- ❌ 操作無回饋（違反 Heuristic 1／Shneiderman 3）
- ❌ 只靠 hover（觸控失效，違反 Heuristic 2）
- ❌ 讓使用者記憶大量資訊（違反 Heuristic 6／Miller）
- ❌ 錯誤訊息講術語不講解法（違反 Heuristic 9）

## 十、設計完自檢清單（對應學理）

- [ ] 每個畫面有明確主動作（Fitts：大而近）？次要動作降級？
- [ ] 一屏選項 ≤7（Hick / Miller）？
- [ ] 功能有分組、導覽 ≤3 層、有 Card Sorting 驗證過？
- [ ] 系統狀態可見：我在哪、載入中、完成（Heuristic 1）？
- [ ] 每個操作有回饋、錯誤可恢復（Heuristic 9 / Shneiderman 5）？
- [ ] 一致性：慣例、術語、位置全站一致（Heuristic 4 / Jakob）？
- [ ] 對比度、鍵盤操作、焦點、reduced-motion（WCAG）？
- [ ] 新手 30 秒知道功能在哪（可學習性）、專家有捷徑（Heuristic 7）？

## 協同使用

- 與**前端設計總指揮**搭配：總指揮三階段流程中，本 skill 負責「階段二 UX 互動」
- 與 **Impeccable** 搭配：它管視覺品質與模式判斷，本 skill 管互動架構
- 與 **UI UX Pro Max** 搭配：它的 Navigation Patterns 與 98 條 UX 指引可查具體數值

## 參考來源

- Nielsen, J. (1994/2024). *10 Usability Heuristics for User Interface Design*. Nielsen Norman Group. nngroup.com/articles/ten-usability-heuristics/
- Shneiderman, B. et al. *Designing the User Interface*（八條黃金法則）
- Norman, D. *The Design of Everyday Things*
- Fitts, P. M. (1954). *The information capacity of the human motor system*
- Hick, W. E. (1952). *On the rate of gain of information*
- Miller, G. A. (1956). *The Magical Number Seven, Plus or Minus Two*
- Sweller, J. (1988). *Cognitive load during problem solving*
- Morville, P. & Rosenfeld, L. *Information Architecture: For the Web and Beyond*
- W3C. *Web Content Accessibility Guidelines (WCAG) 2.2*
- ISO 9241-11:2018. *Ergonomics of human-system interaction — Usability*
