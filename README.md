# J16 HKBReader — Harry Knowledge Base Viewer

Mobile-friendly 閱讀器，對應 J12 家庭日記的視覺語言（深色、max-width 760px、底部 Tab）。
本目錄為 **OneDrive Testing 階段的 Prototype**：先在 localhost 驗證，用戶 OK 後才會上 GitHub / 部署。

## 用語對照（介面一律用左邊的叫法）

| 介面用字 | 對應 HKB 結構 |
|---|---|
| 標題1 | 標題1（主題群組） |
| 標題2 | 標題2（單元） |
| **篇章** | HKB「標題3」表 |
| **細節** | HKB「標題4」表 |
| **學科** | DOCX 檔（一個學科 = 一份 DOCX；**只計實際有單元連著的 13 個**，不是 OneDrive 內全部 360 個檔名） |
| **STREAM** | 文件所在的 OneDrive 資料夾（Social Science、Science and Technology…）；介面不出現「OneDrive Folder」字眼 |
| **科普** | 篇章沒有外部來源／作者（`原文SOURCE`／`原文作者` 皆空）＝自寫知識內容（23 篇） |
| **相關文章** | 篇章有外部來源或作者（即新聞／帖文原文被核查）（27 篇） |
| **Fact Check** | 細節（標題4）中已填 FACT 總評的條目（19 個），由 J_001 Fact Checker 產出 |

> 早期版本用「有無細節子條目」分科普／文章，結果 Science and Technology 全部篇章都有細節 → 顯示「0 科普」，明顯不合理。現改為按**有無外部來源／作者**分：S&T 變成 9 科普 + 9 相關文章。判別邏輯在 `build_hkb.py`（`rec["kind"] = "article" if (media or auts) else "knowledge"`）。

## 四個 Tab

| Tab | 內容 |
|---|---|
| 統計 | **三張大卡**（單元 25／篇章 50／細節 63）＋ mini（STREAM 6／學科 13／Links 39／已核查 19 of 63 細節）。**FACT CHECK 統計**區：3 張 KPI 卡（平均 FACT 總評 66.9%／已核查細節 19／有評分筆數 18）＋ **地區圓餅**（中國港台 12、日韓 3、中國大陸 2、英美 2）＋ **謊言類型圓餅**（基本屬實 10、煽動性誇大敘事 4、因果歸因上誤導 3、單一因果強行串聯 2、匿名來源單方面敘事 1），兩個圓餅只用已核查的 19 筆細節；**點圓餅的扇形區域 → 文章 Tab 自動只顯示該地區／該謊言類型的文章**（文章 Tab 也會同步選好對應下拉）；**點圖例（label）只在圓餅內篩選**，其餘扇形淡化到 10%、該項圖例高亮，再點同一項回復全部，不會跳頁。FACT CHECK 區下方不再有長段說明文字。再下方 **STREAM 橫棒圖**：每條棒綠色＝科普數目、紫色＝相關文章數目，按「科普＋相關文章」由多至少排列；右側顯示該 STREAM 的學科數與單元數，棒下顯示 N 科普 / N 相關文章 / N 細節 / **Fact Check N** / 最新更新。**只顯示有單元的 STREAM（6 個），Academics and Workplace 等 0 單元的 4 個不顯示**。點棒 → 套用該 STREAM 並跳去「科普」（若該 STREAM 沒有科普則跳去「文章」）。 |
| 科普 | 只搜標題3 之中的科普條目（23 篇，無外部來源／作者）。sticky 搜尋（標題1／標題2／篇章／內文）、學科篩選（選了 STREAM 後只列該 STREAM 的學科）、更新日期（7/30/90 日）、最新／最舊排序、重置。預設「最新更新 5 個標題1」**圖庫**，可展開全部；點卡片逐層深入：標題1 → 標題2 單元 → 篇章 → 詳情（內文、細節子段、正面／反面證據、表格、Fact 總評、Links）。 |
| 文章 | 只列「相關文章」（27 篇，有外部來源／作者）。facet 下拉：學科、**來源**（17 個品牌）、**作者**（24 位）、**地區**（中國港台／日韓／中國大陸／英美／未標示）、**謊言類型**（5 類）、日期，數字為實際命中條目數。**橫條列表**：每行顯示文章標題、來源 tag、topic（標題1）、作者、**`FACT x%`**（該篇章已核查細節的 FACT 總評平均；**≥80% 綠、≤40% 紅、其餘黃**；無評分則淡化顯示「FACT 未核查」）、**`AI x%`**（AI 看法平均，藍色）、最後更新日期；預設最新 10 篇，可展開全部。詳情頁頭部有 **FACT CHECK 面板**：**圓環進度圖**顯示 FACT CHECK 平均%（顏色同上 80/40 分色，環內有大號 % 與「FACT CHECK」字）＋ AI 看法小圓環（藍，58px）＋ 該篇章所有已核查細節的 FACT 總評原文（多筆時前置細節名）＋ **謊言類型 chip**（紅底圓角，多類時並列）。面板已承接原「Fact 總評／AI 看法／謊言類型」三行，內文不重複顯示。 |
| 新聞 | **多來源**：來源清單來自飛書「News Feed List」中 Job ID → J16 的記錄（現時 2 個：政府新聞 RSS 30 條、博客網頁 15 條）。依日期分組（無日期者歸「日期未標示」）、78px 本地縮圖、摘要、搜尋、來源 chips 篩選與「載入更多」（每 20 條）。**每張卡右側有兩顆一鍵複製按鈕**：`J01`（藍）複製 `J01 ` + 連結 + 空格、`J04`（紫）複製 `J04 ` + 連結 + 空格，方便直接在豆包 HKB 對話貼上執行 JOB；**點卡片會在另一視窗／分頁開啟原文**，若瀏覽器封鎖新視窗會彈出「直接開啟／複製連結／取消」選擇框，不會靜靜取代閱讀器；複製失敗時彈出可手動 Ctrl+C 的文字框。 |

篩選規則：學科清單會隨 STREAM 收窄（選 Social Science 時只列該 STREAM 的學科），避免兩個篩選互斥而出現空結果。若仍空結果，畫面會列出當前生效的篩選（STREAM／學科／來源／作者／日期）並提供「清除全部篩選」按鈕。

來源與作者口徑：`build_hkb.py` 的 `MEDIA_MAP` 把細節條目的來源 URL 依網域歸成品牌（am730、unwire.hk、香港經濟日報、星島頭條、Yahoo 新聞、關鍵評論網、36Kr、法庭線…），截圖／帖文類統一歸「截圖／帖文」；`norm_author()` 去掉作者欄括號內的職銜或任職機構。

## 資料流

```
飛書 HKB Base（單元 / 標題3 / 標題4 / Links）
        │  build_hkb.py（讀 _raw/*.ndjson + docxmap.json）
        ▼
   hkb.json  ──────────────┐
                           ├─► index.html（純前端，fetch 兩個 json）
news-sources.json          │
        │  build_news.py  ▼
        └────────► news-cache.json + news-img/*.jpg
                ▲
飛書 News Feed List ── sync_news_sources.py（只抽 Job ID → J16 的來源）
```

- `hkb.json`：`{counts, folders[], docs[], units[], t3[], t4[], links[]}`，時間統一 `YYYY-MM-DD HH:MM`；`folders[]` 即 STREAM（含 `knowledge`／`articles` 分數）。
- `t3[]` 每筆有 `kind`（`knowledge` 科普 / `article` 相關文章）、`media[]`（來源品牌）、`auts[]`（去職銜作者），前端 facet 與詳情頁靠這三個欄位。
- `news-cache.json`：`{feed, feedUrl, sources[{name,type,url,count,title,updated}], feedUpdated, generated, count, items[{title,link,date,time,summary,img,imgSrc,cat,src}]}`；`src` 是來源名（對應 `sources[].name`）。
- `news-sources.json`：`[{name,type,url}]`，由 `sync_news_sources.py` 從 News Feed List（`tblHXtZC4Dc0RpEQ` / view `vewFb7ZCho`）抽出 **Job ID link 指向 J16（`reczz28WRDTbyYuH`）** 的所有記錄；`type` 為 `RSS`／`Webpage`／`Youtube`（Youtube 會跳過）。**用戶在表裡加新來源後，重跑 `sync_news_sources.py` + `build_news.py` 即生效**，不需改程式。
- Webpage 類來源（例如博客作者頁）先按「文章卡片」切塊解析：標題（`<h3>`）＋作者列的日期（時鐘圖標後的 `YYYY-MM-DD`）＋摘要（`<div class="des">`）＋縮圖（第一張 `<img>`，走 `cache_image()`）。卡片切不出來才回退到純連結掃描（該情況無日期，歸「日期未標示」）。
- 圖片一律本地化：Base 附件圖放 `images/<file_token>.jpg`（17 張，已壓縮），新聞縮圖放 `news-img/<md5>.jpg`（長邊 480、quality 78）。
  **新聞原圖有防外連，直接引用 URL 在瀏覽器會載不出來，所以一定要用本地副本。**

## 線上部（GitHub Pages）

- 網站：<https://hkharrycheng.github.io/hkb-reader/>
- Repo（public）：<https://github.com/hkharrycheng/hkb-reader>
- 部署方式：repo 根目錄就是網站根目錄，`main` 分支一有更新，GitHub Pages 自動重建（約 1 分鐘）。
- 更新做法：改完本機檔案後，把 `index.html`、`hkb.json`、`news-cache.json`、`news-sources.json`（連同新增的 `images/`、`news-img/`）上傳到 repo 根目錄對應位置即可；`build_*.py`、`sync_news_sources.py`、`_raw/` 不需上傳（`_raw` 是本機工作檔，不進 repo）。
- 不用 Cloudflare Pages：此知識庫屬公開內容，不需要私人存取控制。

## 執行（本機測試）

最簡單：雙擊 `start-localhost.bat`（會起 server 並自動開瀏覽器）。

人手起 server：

```powershell
cd "D:\Onedrive\Harry Information System\豆包Agents Program Backup\HKBReader"
python -m http.server 8790 --bind 127.0.0.1
```

開 <http://127.0.0.1:8790/index.html>。
必須經 http 開啟，直接雙擊 index.html（file://）會被 CORS 擋住而讀不到 json。
如果頁面突然打不開，多數是 server 被關掉了，再跑一次上面的指令或雙擊 bat 即可。

重建資料：

```powershell
python build_hkb.py     # 重寫 hkb.json 與 _raw/images.json（來源為 _raw/*.ndjson，含 media/auts 計算）
python sync_news_sources.py   # 讀飛書 News Feed List，抽出 Job ID → J16 的來源寫 news-sources.json
python build_news.py    # 需外網；按 news-sources.json 抓 RSS／網頁來源並補抓缺漏的新聞縮圖
```

改完 `index.html` 建議先驗 JS 語法（抽出 `<script>` 再 `node --check`）。

## 檔案

| 檔案 | 說明 |
|---|---|
| `index.html` | 全部前端（CSS + ES5 JS，無外部依賴，四 Tab） |
| `hkb.json` | 知識庫資料（約 220 KB） |
| `news-cache.json` | 新聞快取（45 條，2 個來源） |
| `news-sources.json` | J16 新聞來源清單（由 News Feed List 同步，現時 2 個） |
| `build_hkb.py` / `build_news.py` / `sync_news_sources.py` | 資料建置腳本 |
| `start-localhost.bat` | 一鍵起 localhost 並開瀏覽器 |
| `images/` | 單元／篇章／細節的附件圖（17 張） |
| `news-img/` | 新聞縮圖本地副本（30 張） |
| `_raw/` | 飛書四表 ndjson 快照、docxmap.json、images.json（建置輸入，可重用） |

## 版本

`v2026.1.06`（前端徽章讀 `hkb.json` 的 `version`；每次改動 +0.01）

本版（2026.1.06）：①「謊言類型」由細節內文搬到文章頭（chip 並列），FACT CHECK 平均% 改用**圓環進度圖**，顏色 ≥80% 綠 / ≤40% 紅 / 其餘黃（文章列表的 `FACT x%` chip 同步分色）；②統計上排由四張大卡改回**三張**（刪掉重複的 19 Fact Check 卡，19 只保留在 FACT CHECK 統計區）；③新聞卡改為「卡片 + 右側 J01／J04 一鍵複製按鈕」，點卡另開新視窗（被封鎖時彈選擇框），新增 `copyText()` / `toast()` / `openAsk()`。

上一版（2026.1.05）：①文章列表加 `FACT x%` / `AI x%` chip；②刪除 FACT CHECK 區下方長段說明；③圓餅圖例改為圓餅內篩選、只有扇形跳文章；④文章詳情頭部加 FACT CHECK 面板（大號 % + FACT 總評原文）；⑤新聞改多來源，來源由 News Feed List 的 J16 記錄同步（新增 `sync_news_sources.py`、`news-sources.json`）。

## 數字口徑（常被問到）

- **學科為何不是 360？** 360 是 `Knowledge Documentary` 資料夾內所有 DOCX 檔名（`docxmap.json` 掃到 369 個檔 / 360 個唯一名），大部分檔從未進入 HKB。介面顯示的「學科」只算**有單元連著**的 DOCX ＝ 13 個（Social Science 2、Science and Technology 3、Human History and Government 4、Philosophy and Anthropology 2、Business and Economics 1、Medic and Health 1）。`hkb.json` 內 `folders[].docx` 仍是全資料夾檔案數（供除錯），畫面不用。
- **Fact Check 19** ＝ 標題4 之中已填 FACT 總評（文字 `Fact總評%` 或有 `FACT總評%` 數值）的細節數；其餘 44 個細節多為 J_004 Extended Research 產出（有 AI 看法% 但無 FACT 總評）。19 個之中 18 個屬 6 個 STREAM，1 個屬「未分類」篇章（不影響統計，圖內口徑已是全部已核查細節）。
- **平均 FACT 總評 66.9%** ＝ 18 筆有 `FACT總評%` 數值的平均（最低 20%、最高 95%）；有 1 筆只有文字評語沒有數值，故只計 18 筆。
- **圓餅合計為何大於 19？** 地區圓餅 19 筆（每筆一個地區，全部有標示）；謊言類型圓餅合計 20，因為 1 個細節同時標了兩種類型（煽動性誇大敘事＋因果歸因上誤導）。
- **科學與科技 0 科普（已修正）** ＝ 舊規則「篇章有細節就算相關文章」，而 S&T 18 個篇章全部有細節；新規則按外部來源／作者分，S&T 現為 9 科普 + 9 相關文章。

## 已知限制

- Prototype 只在 localhost 驗證，未部署。
- 圖片不能加 `loading="lazy"`：此環境下 lazy 圖在切 Tab 後不會載入（曾造成縮圖全空白），所以全部改成即時載入。
- 資料瑕疵：1 個篇章（「蒙古近70%貿易靠中國…」）在 HKB 單元欄為空，前端顯示為「（未連結單元）／（未分類）」，原始資料未改。
- 新聞 RSS 的 pubDate 只有日期，故時間一律顯示 `00:00`；Webpage 類來源解析到作者列日期就以該日期分組（現時博客 15 條全部有日期），解析不到的才歸「日期未標示」。
- 統計只列出有單元的 STREAM；若日後某 STREAM 有 DOCX 但無任何單元，仍不會出現在統計（設計如此）。
- 新聞開新視窗靠 `target="_blank"` + `window.open()`；**在只支援單一檢視的殼（例如豆包的內建瀏覽器）仍可能把閱讀器取代**，那時可按上一頁返回，或在 Safari／Chrome 開啟本頁即可正常另開分頁。`window.open()` 被封鎖時會彈出「直接開啟／複製連結」選擇框。
