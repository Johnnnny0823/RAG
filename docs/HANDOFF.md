# Agent Handoff

## M5 靜態前端部署驗收

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `316f43f`。
- Current milestone and status: M5 IN_PROGRESS。
- Goal of this session: 驗證不依賴 Vite 開發伺服器的 Compose 部署。
- Files changed (with purpose): `apps/web/Dockerfile`、`nginx.conf` 建置及提供靜態前端，`docker-compose.deploy.yml` 啟用部署映像與內部 API，README、SETUP 及 DECISIONS 記錄。
- Database migrations added/applied: 無新增，獨立新資料卷從空狀態遷移至 `0009_session_message_cascade`。
- API/Schema changes: 無。
- Commands actually run and results: Compose 合併、逐服務建置、`up --no-build --wait` 及 `smoke.py` 通過。匯入 25 個真實 TIPO 文件版本（1 筆全文），建立 228 個詞彙片段與 244 個向量。Playwright 驗證靜態檔、本機模型拆解、檢索、引文、保存及私有 PDF 下載。Docker 確認只有 Web 發布到 `127.0.0.1:18123`。
- Tests NOT run and reason: 未部署外部 TLS、反向代理或壓測。人工評估尚未完成。
- Data sources checked (exact URL/date) and license/access notes: 以 [M1 存檔 TIPO 24 卷 19 期索引及公開全文](DATA_SOURCES.md) 匯入新資料卷，無新增下載。
- Known bugs / risks / blockers: 部署只驗證本機回環入口。35 組候選待人工複核。
- Decisions made (ADR links): [靜態前端部署](DECISIONS.md#m5-靜態前端部署)。
- Uncommitted changes / file ownership warnings: 隔離驗收專案 `patentscope-static-proof` 保留；原始物件存在該次驗收的本機暫存資料夾。
- Next 1–3 concrete actions: 按新版目標補 Playwright TypeScript 與 CI 品質關卡，再續做人工複核及公開部署安全控制。新版目標將 M6 定義為整合、安全與部署，與既有 AGENTS.md 的選配延伸不同，里程碑映射待同步。
- Exact reproduction steps: 見 [靜態前端部署](SETUP.md#靜態前端部署)。

## M5 說明書段落引用

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `ce82fe7`。
- Current milestone and status: M5 IN_PROGRESS。
- Goal of this session: 驗證比較可回傳只在說明書出現的真實引文。
- Files changed (with purpose): `evaluate_citations.py` 加入段落專用案例及預期引文種類驗證。
- Database migrations added/applied: 無。
- API/Schema changes: 無。
- Commands actually run and results: 對 `18022` 完成 7 次比對、14 個判定。6 段引文全部核對通過，含 1 段發明內容。另以 `verify_document 202639611` 從唯讀存檔 XML 驗證 19 項請求項及 122 個說明書段落。Ruff、pytest 47 項通過。
- Tests NOT run and reason: 尚無人工複核的語義判定或相關性分數。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 官方樣本](DATA_SOURCES.md) 的存檔，無新增下載。
- Known bugs / risks / blockers: 段落引文實測只涵蓋一個指定發明內容段落。35 組候選仍待人工複核。
- Decisions made (ADR links): [引文核對方式](EVALUATION.md#2026-11-09-引文核對)。
- Uncommitted changes / file ownership warnings: 無。
- Next 1–3 concrete actions: 人工複核候選池及重跑基線，逐項核對部署與品質驗收。
- Exact reproduction steps: 見 [README 檢索評估](../README.md#檢索評估) 和 [M1 官方樣本重現](SETUP.md#m1-官方樣本重現)。

## M5 人工複核候選池

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `d8497b8`。
- Current milestone and status: M5 IN_PROGRESS。
- Goal of this session: 產生可供人員獨立評分的官方專利候選池。
- Files changed (with purpose): `evaluate_search.py` 新增候選匯出與複核欄位驗證，`tipo_seed.json` 增加兩個領域，`tipo_review_pool.json` 保留待複核結果。
- Database migrations added/applied: 無。
- API/Schema changes: 無。
- Commands actually run and results: 對 `18022` 跑三種模式各四次。匯出 35 組候選並核對來源、無重複及評分留空。Ruff 和 pytest 47 項通過，1 則既有警告。
- Tests NOT run and reason: 人工標註與分數複跑待完成。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 TIPO 語料](DATA_SOURCES.md)，候選附查得的官方連結。
- Known bugs / risks / blockers: 尚無人工複核的分數。池由現有模式聯集建立，未檢索到的文件不在評估分母中。
- Decisions made (ADR links): [複核與去重規則](EVALUATION.md#人工複核候選池)。
- Uncommitted changes / file ownership warnings: 無。
- Next 1–3 concrete actions: 人工逐案複核並重跑評估，驗證說明書段落的引文路徑。
- Exact reproduction steps: 見 [人工複核候選池](EVALUATION.md#人工複核候選池)。

## M5 跨領域引文核對

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `06167bc`。
- Current milestone and status: M5 IN_PROGRESS。
- Goal of this session: 對真實文件版本核對技術比對引文及無證據情境。
- Files changed (with purpose): `scripts/evaluate_citations.py` 新增可重跑引文評估，README 及 [EVALUATION.md](EVALUATION.md) 記錄操作與解讀。
- Database migrations added/applied: 無。
- API/Schema changes: 無。
- Commands actually run and results: 使用 `18022` 真實 TIPO API 驗證六個版本、12 個判定、5 段逐字請求項引文及 7 個無引文判定。Ruff 與 pytest 46 項通過，既有警告 1 則。
- Tests NOT run and reason: 人工語義判定、引文召回及更大樣本待評估。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 TIPO 語料](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 精確率的分母是此批實際輸出的引文，無法由此推論整體技術比對品質。
- Decisions made (ADR links): [引文核對方式](EVALUATION.md#2026-11-09-引文核對)。
- Uncommitted changes / file ownership warnings: 無測試資料異動。
- Next 1–3 concrete actions: 產生可供人工複核的合併候選池，核對 M5 剩餘驗收。
- Exact reproduction steps: 見 [README 檢索評估](../README.md#檢索評估)。

## M5 帳號自助刪除

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `b46b52f`。
- Current milestone and status: M5 IN_PROGRESS。
- Goal of this session: 讓帳號擁有者重新驗證密碼後，自助刪除帳號、私人研究資料及所有登入憑證。
- Files changed (with purpose): `identity.py` 負責交易刪除，`accounts.py`、`patents.py` 提供路由及錯誤碼，`research.tsx` 串接畫面，`smoke_private_browser.js` 驗證。
- Database migrations added/applied: 無新增，沿用 `0009_session_message_cascade`。
- API/Schema changes: `DELETE /api/v1/me`，成功 204，密碼不符 403。
- Commands actually run and results: Ruff lint、pytest 46 項（1 則既有警告）、TypeScript 與 Vite 建置通過。
- Playwright 完整工作台回歸通過。錯誤密碼回傳 403 且保留資料，正確密碼刪除後兩個登入均失效，也無法重新登入。直接查 PostgreSQL 確認該帳號、憑證、專案、搜尋、候選、收藏、Session 與訊息均為 0 筆，公開專利文件仍為 143 筆。
- Tests NOT run and reason: 未測量大量帳號資料的刪除延遲、併發壓力及備份清除。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 TIPO 資料](DATA_SOURCES.md)，沒有新增擷取。
- Known bugs / risks / blockers: 已下載 PDF 與備份由各自位置管理。人工複核及擴大引用評估仍待完成。
- Decisions made (ADR links): [M5 帳號自助刪除](DECISIONS.md#m5-帳號自助刪除)。
- Uncommitted changes / file ownership warnings: 驗收 Web 在 `18122`，API 在 `18022`，僅刪除新建測試帳號。
- Next 1–3 concrete actions: 擴充人工複核候選池及引文測試，核對整體目標的剩餘驗收。
- Exact reproduction steps: 依 [瀏覽器驗收](SETUP.md#m4-瀏覽器驗收) 重跑。帳號驗收會刪除本次新建的擁有者測試帳號。

## M5 AI Session 自助刪除

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `d9e5196`。
- Current milestone and status: M5 IN_PROGRESS。
- Goal of this session: 讓擁有者從專案刪除個別 Session 與訊息。
- Files changed (with purpose): `sessions.py` 加入所有權限定刪除，`research-sessions.tsx` 串接確認與清除，`smoke_private_browser.js` 擴充驗收。
- Database migrations added/applied: `0009_session_message_cascade` 將訊息外鍵改為級聯刪除，保留既有訊息。
- API/Schema changes: `DELETE /api/v1/sessions/{session_id}`。
- Commands actually run and results: Ruff、pytest 46 項（1 則既有警告）、TypeScript 與 Vite 建置通過。
- 已有語料及全新資料卷都遷移至 `0009_session_message_cascade`。Playwright 工作台回歸通過，涵蓋取消、跨帳號 404、擁有者刪除、後續訊息讀寫 404 及專案保留。PostgreSQL 查得目標 Session 與訊息均為 0 筆。
- Tests NOT run and reason: 未做併發負載與外部備份清除。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 TIPO 資料](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 本機下載及獨立保存的搜尋由各自位置管理。帳號整體刪除與擴大引用評估待完成。
- Decisions made (ADR links): [M5 AI Session 刪除](DECISIONS.md#m5-ai-session-刪除)。
- Uncommitted changes / file ownership warnings: 驗收 Web 在 `18121`，API 在 `18021`，只刪除驗收腳本新建的 Session。
- Next 1–3 concrete actions: 補上帳號整體刪除，擴充人工複核與引用評估。
- Exact reproduction steps: 先遷移到 `0009_session_message_cascade`，再跑 [瀏覽器驗收](SETUP.md#m4-瀏覽器驗收)。

## M5 已保存搜尋自助刪除

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `7936e83`。
- Current milestone and status: M5 IN_PROGRESS。
- Goal of this session: 讓擁有者在瀏覽器確認刪除已保存的搜尋、候選與比對。
- Files changed (with purpose): `search_runs.py` 新增所有權限定刪除及快照讀取，`research.tsx` 串接二次確認及狀態清除，API 與瀏覽器腳本擴充回歸。
- Database migrations added/applied: 無新增，沿用既有搜尋候選及比對外鍵的級聯刪除。
- API/Schema changes: 新增 `DELETE /api/v1/search-runs/{run_id}`。
- Commands actually run and results: Ruff lint、pytest 46 項（1 則既有警告）、TypeScript 與 Vite 建置通過。
- Playwright 與 API 回歸通過，核對取消刪除、擁有者刪除、跨帳號拒絕、歷史清空、舊報告及比對回傳 404，且 AI Session 仍可讀取。直接查 PostgreSQL 確認該筆搜尋、候選及比對皆為 0 筆。
- Tests NOT run and reason: 未測外部備份清理或競爭壓力。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 TIPO 資料](DATA_SOURCES.md)，驗收只刪除自建測試搜尋。
- Known bugs / risks / blockers: 已下載 PDF 和備份由各自位置管理。AI Session 與帳號刪除待完成。
- Decisions made (ADR links): [M5 已保存搜尋刪除](DECISIONS.md#m5-已保存搜尋刪除)。
- Uncommitted changes / file ownership warnings: 驗收 Web 在 `18120`，API 在 `18020`。
- Next 1–3 concrete actions: 完成 AI Session 與帳號資料刪除，再擴大人工複核及引用驗收。
- Exact reproduction steps: 使用隔離語料在新 API 跑 `scripts/smoke_search_runs.py` 與 [瀏覽器驗收](SETUP.md#m4-瀏覽器驗收)。

## M5 登出憑證撤銷

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `e017083`。
- Current milestone and status: M5 IN_PROGRESS。
- Goal of this session: 撤銷當前登入憑證並驗證私人資源的存取。
- Files changed (with purpose): `identity.py`、`accounts.py` 加入登出，`research.tsx` 串接，API 與瀏覽器冒煙腳本核對撤銷。
- Database migrations added/applied: 無新增，沿用 `auth_sessions`。
- API/Schema changes: `POST /api/v1/auth/logout` 回傳 204，撤銷本次 Bearer token。
- Commands actually run and results: Ruff lint、pytest 46 項（1 則既有警告）、前端型別及 Vite 建置通過。使用同帳號兩個 token 核對單一憑證撤銷，另一個仍可讀取 `/me`。
- Playwright 工作台回歸通過，確認登出後舊憑證下載 PDF 回傳 401。全新空資料卷以 Compose 啟動，Alembic head 為 `0008_research_sessions`，Web 代理、API 與 pgvector 通過 HTTP 冒煙測試。首次多服務建置遇到 BuildKit gRPC header 錯誤，改為逐服務建置後通過，操作記於 [SETUP.md](SETUP.md)。
- Tests NOT run and reason: 尚未驗證外部部署反向代理或長時間高併發。
- Data sources checked (exact URL/date) and license/access notes: 沿用既有 TIPO 驗收資料，無新增擷取。
- Known bugs / risks / blockers: 登出處理單一憑證。自助研究資料刪除與定期清理仍待實作，部署者須管理模型主機存取及備份。
- Decisions made (ADR links): [登出與資料保留](DECISIONS.md#m5-登出與資料保留)。
- Uncommitted changes / file ownership warnings: 瀏覽器與 API 驗收用測試帳號及公開資料。
- Next 1–3 concrete actions: 完成研究資料刪除及隱私驗收，擴大人工複核候選池與引用測試。
- Exact reproduction steps: 使用含 TIPO 樣本的隔離 API 執行 `scripts/smoke_search_runs.py` 及 [M4 瀏覽器驗收](SETUP.md#m4-瀏覽器驗收)。

## M5 檢索種子基線

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `e80c728`。
- Current milestone and status: M5 IN_PROGRESS。
- Goal of this session: 用同一標註池重跑詞彙、向量與混合重排。
- Files changed (with purpose): `evaluation/tipo_seed.json` 保存種子標註，`scripts/evaluate_search.py` 輸出排名、分數、延遲及模型資訊，`tests/test_evaluate_search.py` 測試未標註與版本重複計分。
- Database migrations added/applied: 無。
- API/Schema changes: 無。
- Commands actually run and results: Ruff 與 pytest 46 項通過。對 `18017` 各模式跑四次，分數與延遲見 [EVALUATION.md](EVALUATION.md)。`smoke_comparison.py` 驗證引文逐字、版本及缺少證據。
- Tests NOT run and reason: 尚無人工複核的完整標註池、跨領域引用準確率、每次查詢硬體成本或負載測試。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 官方語料](DATA_SOURCES.md)，核對 TIPO 公開 `202640162`、`202639611` 與公告 `I941082`。
- Known bugs / risks / blockers: 種子標註由 Codex 查核，兩筆查詢不能支持普遍成效結論。
- Decisions made (ADR links): [評估計分約定](EVALUATION.md)。
- Uncommitted changes / file ownership warnings: 無。個別執行輸出留於本機暫存。
- Next 1–3 concrete actions: 擴充可人工複核的候選池，完成隱私收尾及重現部署驗收。
- Exact reproduction steps: 見 [README 檢索評估](../README.md#檢索評估)。

## M5 私人繁中 PDF 匯出

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `827bffa`。
- Current milestone and status: M5 IN_PROGRESS。
- Goal of this session: 讓搜尋紀錄擁有者能匯出有原文與來源的繁中報告。
- Files changed (with purpose): `reports.py` 產生 PDF，`patents.py` 批次讀取來源，`main.py` 掛載路由，`requirements.txt` 與 API Dockerfile 加入 PDF／字型依賴，`research.tsx` 提供下載，冒煙腳本驗證流程。
- Database migrations added/applied: 無，沿用 `0008_research_sessions`。
- API/Schema changes: 增加 `GET /api/v1/search-runs/{run_id}/report.pdf`。
- Commands actually run and results: pytest 44 項、Ruff 與 Docker 前端建置通過。使用 `smoke_search_runs.py --pdf-output` 在 `18017` 驗證擁有者下載、訪客 401、其他帳號 404。以 pypdf 與 Poppler 檢查 2 頁 A4、繁中、臺灣字型、真實專利與來源連結及原文定位。
- Playwright 在 `18116` 驗證瀏覽器下載及私人工作台回歸。首跑的本機模型等待超過 Playwright 預設 30 秒，腳本改用 120 秒等待後通過。
- Tests NOT run and reason: 未驗證大量候選匯出負載、遠端 CI 及多種 PDF 閱讀器。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 TIPO 資料](DATA_SOURCES.md)，未新增下載。PDF 技術參考見 [DECISIONS.md](DECISIONS.md)。
- Known bugs / risks / blockers: 同步下載，沒有報告佇列或伺服器端報告存檔。報告以已保存候選為準，匯出時讀取候選的現有來源；完整歷史語料快照與檢索品質仍待驗證。
- Decisions made (ADR links): 見 [DECISIONS.md](DECISIONS.md) 的 M5 私人報告輸出。
- Uncommitted changes / file ownership warnings: 驗收報告是公開測試樣本，僅存在本機暫存目錄。
- Next 1–3 concrete actions: 建立人工作標準與相關性測試集，實作三種檢索的品質與延遲評估，再完成 M5 隱私驗收。
- Exact reproduction steps: 見 [M5 私人 PDF 驗收](SETUP.md#m5-私人-pdf-驗收)。

## M4 文件篩選與里程碑驗收

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `be133e0`。
- Current milestone and status: M4 DONE，M5 待開始。
- Goal of this session: 完成日期、文件階段及申請人篩選並驗收研究工作台。
- Files changed (with purpose): `patents.py` 共用檢索篩選，`research.tsx` 串接表單及回顯，`smoke_hybrid.py`、`smoke_private_browser.js` 擴充回歸。
- Database migrations added/applied: 本次無新增或重跑，沿用前次已驗證的 `0008_research_sessions`。
- API/Schema changes: 三種排序檢索接受日期、文件階段及申請人，混合搜尋紀錄也保存條件。
- Commands actually run and results: Ruff 格式及 lint、pytest 44 項（1 則既有警告）、Docker TypeScript／Vite 建置均通過。`smoke_hybrid.py` 通過三種檢索模式及 RRF 回歸，`smoke.py` 通過。Playwright 完整工作台回歸驗證公開篩選、申請人、日期錯誤及歷史還原，另以實際檢索驗證載入及空結果。使用資料庫內的無寫入 `VALUES` 測試核對日期含起迄日與未知值排除。
- Tests NOT run and reason: 未驗證遠端 CI、大量語料下的篩選效能或跨瀏覽器。正式測試資料庫沒有已匯入的公開／公告日期，無法驗證帶日期的真實結果。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 TIPO 資料](DATA_SOURCES.md)，本次無新增下載或補寫日期。
- Known bugs / risks / blockers: 日期篩選會排除未知日期，現有樣本使用日期條件會得到空結果。前端矩陣仍須逐份比對。
- Decisions made (ADR links): 見 [DECISIONS.md](DECISIONS.md) 的 M4 文件篩選。
- Uncommitted changes / file ownership warnings: 驗收 Web 在 `18115`，API 在 `18015`，測試僅使用公開語料。
- Next 1–3 concrete actions: 實作 M5 的私人 PDF 匯出、可重現的相關性與延遲評估及隱私驗收。後續匯入可補入有來源證據的正式日期。
- Exact reproduction steps: 見 [M4 瀏覽器驗收](SETUP.md#m4-瀏覽器驗收)。本次使用 Web `18115`、API `18015`。

## M4 跨文件比對矩陣

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `77257de`。
- Current milestone and status: M4 IN_PROGRESS。
- Goal of this session: 並排比對同一次搜尋中不同文件版本的判定與引文。
- Files changed (with purpose): `comparison-matrix.tsx` 呈現技術特徵、判定及原文定位，`research.tsx` 整合同一搜尋的比對，`smoke_private_browser.js` 增加真實文件並排及重讀驗收。
- Database migrations added/applied: 無新增，沿用 `0008_research_sessions`。
- API/Schema changes: 無，沿用單版本預覽與已保存搜尋的比對 API。
- Commands actually run and results: Docker 內 TypeScript 與 Vite 建置、`smoke.py`、Playwright 私人工作台回歸均通過。Playwright 核對公開 `202640162` 與公告 `I941082` 分欄、技術特徵列、引文與來源雜湊，以及重新登入後從歷史還原兩欄。
- Tests NOT run and reason: 無後端修改，沿用上一提交的 44 項 pytest。未單獨測試預覽跨頁或多瀏覽器。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 TIPO 資料](DATA_SOURCES.md)，無新增下載。
- Known bugs / risks / blockers: 矩陣由使用者逐一比對候選後建立，沒有批次比對。日期、文件種類與申請人篩選仍缺。
- Decisions made (ADR links): 見 [DECISIONS.md](DECISIONS.md) 的 M4 跨文件比對矩陣。
- Uncommitted changes / file ownership warnings: 驗收 Web 在 `18114`，API 在 `18014`，使用公開測試構想。
- Next 1–3 concrete actions: 將日期、文件種類與申請人篩選套用至檢索分支，再驗收空結果、錯誤及完整 M4 流程。
- Exact reproduction steps: 見 [M4 瀏覽器驗收](SETUP.md#m4-瀏覽器驗收)。

## M4 研究專案管理

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `f3207d0`。
- Current milestone and status: M4 IN_PROGRESS。
- Goal of this session: 補齊私人研究專案詳情、改名、說明編輯與安全刪除。
- Files changed (with purpose): `projects.py` 補齊專案操作，`patents.py` 新增衝突代碼，`research.tsx` 串接管理介面，`smoke_private_browser.js` 擴充流程。
- Database migrations added/applied: 無新增，沿用 `0008_research_sessions`，用既有外鍵阻擋有相依資料的專案刪除。
- API/Schema changes: 新增專案詳情 GET、PATCH、DELETE，見 [API.md](API.md)。
- Commands actually run and results: Ruff 格式及 lint、Docker 內 TypeScript 與 Vite 建置、`smoke.py` 通過。pytest 44 項通過（1 則既有警告）。Playwright 完整回歸通過，驗證改名、更新說明、空白專案刪除、含 Session 專案拒絕刪除並保留資料，以及其他帳號查詢、修改與刪除皆回傳 404。
- Tests NOT run and reason: 未做遠端 CI 與並發刪除壓力測試。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 TIPO 資料](DATA_SOURCES.md)，無新增下載。
- Known bugs / risks / blockers: 有資料的專案無法刪除。跨文件比較仍缺矩陣，結果目前僅能按 IPC 篩選，M4 尚未結案。
- Decisions made (ADR links): 見 [DECISIONS.md](DECISIONS.md) 的 M4 研究專案刪除。
- Uncommitted changes / file ownership warnings: 驗收 Web 在 `18114`，API 在 `18014`，驗收僅刪除自行建立的空白測試專案。
- Next 1–3 concrete actions: 加入跨文件特徵比對矩陣及日期、文件種類、申請人篩選，再重跑 M4 完整驗收。
- Exact reproduction steps: 見 [M4 瀏覽器驗收](SETUP.md#m4-瀏覽器驗收)，本次使用 Web `18114`、API `18014`。

## M4 私人 AI Session

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `6eb4a32`。
- Current milestone and status: M4 IN_PROGRESS。
- Goal of this session: 在研究專案中保存及回顧本機 AI 拆解，並將草稿帶回檢索表單。
- Files changed (with purpose): `0008_research_sessions.py` 建立 Session 與訊息，`sessions.py` 實作所有權與分析保存，`main.py`、`patents.py` 掛載路由與錯誤碼，`research-sessions.tsx` 和 `research.tsx` 串接介面，`smoke_private_browser.js` 驗收。
- Database migrations added/applied: `0008_research_sessions` 已套用至含 TIPO 語料的隔離資料庫，亦在 `patentscope-m4-session-clean` 新資料卷驗證遷移與 head。
- API/Schema changes: Session 建立、列表、訊息歷史及本機拆解，見 [API.md](API.md)。
- Commands actually run and results: Ruff 格式與 lint、pytest 44 項、Docker 內 TypeScript 與 Vite 建置通過。Playwright 在 `18113` 驗證本機 Qwen 草稿保存、帶入表單、重新登入後讀回、訊息游標順序與另一帳號的列表、讀取及提交均 404。同一流程也通過真實 TIPO 搜尋、證據、專案歸檔及收藏筆記回歸。
- Tests NOT run and reason: 未做遠端 CI、模型停機模擬或多瀏覽器並發。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 TIPO 資料](DATA_SOURCES.md) 與本機模型，未新增下載。
- Known bugs / risks / blockers: 各輪拆解目前獨立。Session 列表介面顯示最近 100 筆。專案改名與刪除、PDF 和品質評估待實作。
- Decisions made (ADR links): 見 [DECISIONS.md](DECISIONS.md) 的 M4 AI Session。
- Uncommitted changes / file ownership warnings: 驗收 Web 在 `18113`，API 在 `18013`，測試僅用公開構想。
- Next 1–3 concrete actions: 加入專案改名及安全刪除，驗收 M4 後依序開始 M5 報告與評估。
- Exact reproduction steps: 見 [M4 瀏覽器驗收](SETUP.md#m4-瀏覽器驗收)。本次使用 Web `18113`、API `18013`。

## M4 專利收藏與筆記

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `c3ca88f`。
- Current milestone and status: M4 IN_PROGRESS。
- Goal of this session: 在私人研究專案內收藏官方文件版本、編輯筆記及重新開啟全文。
- Files changed (with purpose): `0007_saved_patents.py` 定義收藏表，`bookmarks.py` 提供所有權隔離 API，`main.py` 掛載路由，`patents.py` 加入錯誤碼，`research.tsx` 串接收藏與筆記，`smoke_private_browser.js` 增補驗收。
- Database migrations added/applied: `0007_saved_patents` 已套用至含真實語料的 `patentscope-m1-proof`，亦在 `patentscope-m4-bookmark-clean` 新資料卷上遷移並核對 head。
- API/Schema changes: 專案收藏列表、新增、筆記更新及移除，見 [API.md](API.md)。
- Commands actually run and results: Ruff 格式及 lint 通過。pytest 44 項通過，1 則既有 Starlette 警告。Docker 內 `npm run build` 通過。Playwright `smoke_private_browser.js` 驗證收藏、筆記重讀、重複收藏保留筆記、從收藏開啟同一文件版本、其他帳號讀寫及刪除均回傳 404、移除收藏後既有證據仍可讀取。
- Tests NOT run and reason: 未執行遠端 CI、跨瀏覽器或大量收藏測試。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 TIPO 資料](DATA_SOURCES.md)，使用公開文件 `202640162`，未新增下載。
- Known bugs / risks / blockers: 收藏依目前選定專案顯示。移除收藏也會刪除該筆筆記。AI Session、專案改名與刪除、PDF 及品質評估待實作。
- Decisions made (ADR links): 見 [DECISIONS.md](DECISIONS.md) 的 M4 專案收藏。
- Uncommitted changes / file ownership warnings: 驗收 Web 在 `18112`，API 在 `18012`，測試帳號只使用公開資料。
- Next 1–3 concrete actions: 完成具帳號隔離的 AI Session 與專案管理，再驗收 M4 工作台。
- Exact reproduction steps: 見 [M4 瀏覽器驗收](SETUP.md#m4-瀏覽器驗收)，本次改用 Web `18112`、API `18012`。

## M4 研究專案與搜尋歸檔

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `a229b07`。
- Current milestone and status: M4 IN_PROGRESS。
- Goal of this session: 建立私人研究專案，整理並篩選已保存搜尋。
- Files changed (with purpose): `0006_projects.py` 定義資料表與外鍵，`projects.py`、`search_runs.py` 提供 API，`main.py` 掛載路由，`patents.py` 補錯誤代碼，`research.tsx` 與 `style.css` 接上介面，`smoke_private_browser.js` 擴充驗收。
- Database migrations added/applied: `0006_projects` 已套用到 `patentscope-m1-proof`，獨立空資料卷 `patentscope-m4-clean` 也成功遷移並查得 head。
- API/Schema changes: 專案建立與列表、搜尋歸檔 PATCH、專案篩選，詳見 [API.md](API.md)。
- Commands actually run and results: Ruff 格式與 lint 通過。pytest 44 通過，1 則既有 Starlette 警告。本機 `npm run build` 通過。以 Playwright CLI 在 `18111` 驗證真實 TIPO 搜尋、建立專案、歸檔、依專案重讀引文、解除歸檔，並核對跨帳號查詢及移動回傳 404。
- 另跑 `python scripts/smoke_search_runs.py --api http://127.0.0.1:18011` 與 Docker 內 `npm run build`，兩者均通過。
- Tests NOT run and reason: 未驗證大量專案或並發操作，亦未做遠端 CI。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 TIPO 資料](DATA_SOURCES.md)，無新增擷取。
- Known bugs / risks / blockers: 目前介面載入最近 100 個專案，尚未提供專案改名、刪除、收藏、逐篇筆記或 AI Session。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄同帳號複合外鍵與可空關聯。
- Uncommitted changes / file ownership warnings: 驗收 Web 在 `18111`，API 在 `18011`，只用隔離資料庫中的公開語料。
- Next 1–3 concrete actions: 加入專案內的專利收藏與筆記，接上 AI Session，再驗收完整工作台。
- Exact reproduction steps: 見 [M4 瀏覽器驗收](SETUP.md#m4-瀏覽器驗收)。本次使用 API `18011`、Web `18111`。

## M4 瀏覽器登入與私人搜尋歷史

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `c355bae`。
- Current milestone and status: M4 IN_PROGRESS。
- Goal of this session: 由瀏覽器主動保存搜尋及引文，並以原帳號回顧。
- Files changed (with purpose): `apps/web/src/research.tsx` 串接登入、歷史、候選快照及比對保存。`scripts/smoke_private_browser.js` 驗證跨帳號及重讀流程。
- Database migrations added/applied: 本次無新增或重跑，使用已遷移至 `0005_search_runs` 的隔離 API。
- API/Schema changes: 無。沿用 M3 帳號與搜尋紀錄 API。
- Commands actually run and results: `docker compose -p patentscope-m1-proof build web` 及 `docker compose -p patentscope-m1-proof run --rm --no-deps web npm run build` 通過。Playwright CLI `run-code --filename scripts/smoke_private_browser.js` 通過，核對預覽不保存、明確保存、登出清除、第二帳號歷史為空、原帳號再次登入取回相同原文引文。
- Tests NOT run and reason: 本次無後端修改，沿用 M3 的 pytest 與跨帳號 API 驗收。未實測 token 自然到期及多頁歷史。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 已匯入 TIPO 資料](DATA_SOURCES.md)，比對公開文件 `202640162`，無新增下載。
- Known bugs / risks / blockers: 登出只清除頁面，已發的伺服器 token 仍依 24 小時效期。搜尋保存會執行一次新的檢索。頁面仍有 favicon 404。研究專案、收藏、筆記、AI Session 與 PDF 尚待實作。
- Decisions made (ADR links): 見 [DECISIONS.md](DECISIONS.md) 的 M4 私人搜尋歷史。
- Uncommitted changes / file ownership warnings: 隔離資料庫有瀏覽器測試帳號及公開測試紀錄。
- Next 1–3 concrete actions: 加入具帳號隔離的研究專案與搜尋關聯，接上收藏、筆記及 AI Session，驗收工作台。
- Exact reproduction steps: 見 [M4 瀏覽器驗收](SETUP.md#m4-瀏覽器驗收)。

## M4 查詢、詳情與比對介面

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `cfb56d7`。
- Current milestone and status: M4 IN_PROGRESS。
- Goal of this session: 從 Web 輸入構想、編輯技術特徵，使用實際專利 API 檢索及查證。
- Files changed (with purpose): `apps/web/src/research.tsx` 實作查詢、特徵、排名、文件及證據。 `main.tsx` 整合頁面並保留服務狀態。 `style.css` 加入響應式表單與版面。
- Database migrations added/applied: 本次無新增或重跑遷移，沿用 M3 已驗證的 `0005_search_runs`。
- API/Schema changes: 無。前端串接查詢拆解、混合檢索、文件詳情、請求項與版本比對預覽。
- Commands actually run and results: `npm run build` 型別檢查與編譯通過。`docker compose -p patentscope-m1-proof build web` 通過。`python scripts/smoke.py --api http://127.0.0.1:18010 --web http://127.0.0.1:18110` 通過。以 Playwright CLI 操作瀏覽器，取得中英文檢索詞，修改特徵，以 G01R 找到公開 202640162 與公告 I941082，展開詳情及證據定位並讀取原文、偏移和雜湊。A01B 顯示空結果，無效 IPC 顯示 HTTP 422 錯誤訊息。390 px 檢查無水平溢出。
- 另以 `docker compose -p patentscope-m1-proof run --rm --no-deps web npm run build` 驗證鎖定依賴下的型別及 Vite 7.3.7 建置，通過。
- Tests NOT run and reason: 本次只改前端，沿用上次後端 pytest。尚未做完整鍵盤、跨瀏覽器、重排分頁及研究保存的瀏覽器驗收。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 TIPO 資料](DATA_SOURCES.md)，無新擷取。瀏覽器確認詳情呈現已保存的來源連結，未另行下載原始檔。
- Known bugs / risks / blockers: 頁面尚無 favicon，瀏覽器會產生 404。預覽每次翻頁會重新呼叫檢索；使用重排時跨請求的順序可能變動。登入、歷史、研究專案與 PDF 尚未接入。
- Decisions made (ADR links): 見 [DECISIONS.md](DECISIONS.md) 的 M4 瀏覽器檢索預覽。
- Uncommitted changes / file ownership warnings: Web 驗收綁定 `127.0.0.1:18110`，代理到獨立 TIPO 測試 API。
- Next 1–3 concrete actions: 串接登入與保存歷史。新增研究專案、收藏與筆記，再驗收跨帳號及瀏覽器流程。
- Exact reproduction steps: 見 [M4 瀏覽器驗收](SETUP.md#m4-瀏覽器驗收)。

## M3 私人搜尋紀錄驗收

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `a5e98c7`。
- Current milestone and status: M3 DONE。M4 研究介面待開始。
- Goal of this session: 讓使用者主動保存混合搜尋、候選順位及可回溯證據，驗證帳號隔離。
- Files changed (with purpose): `accounts.py`、`identity.py` 建立本機帳號及驗證，`search_runs.py` 保存及讀取結果，`main.py` 掛載路由，`patents.py` 重用混合查詢與錯誤處理，`scripts/smoke_search_runs.py` 驗證隔離與保存。
- Database migrations added/applied: `0005_search_runs` 已在含 TIPO 樣本的 `patentscope-m1-proof` 套用，亦在新建的 `patentscope-m3-check` 空資料卷遷移並查得 head。
- API/Schema changes: 帳號、Bearer 驗證、搜尋歷史與候選比對保存，見 [API.md](API.md)。
- Commands actually run and results: Ruff 格式及 lint 通過。預設 pytest 暫存目錄遇到 WinError 5（41 通過、3 個 setup error），改用 `pytest -q --basetemp <新建的獨立路徑>` 後 44 通過，1 則既有 Starlette 警告。以 `--api http://127.0.0.1:18010` 執行 `smoke_search_runs.py`、`smoke_hybrid.py`、`smoke_comparison.py` 均通過，涵蓋兩帳號隔離、排名快照、真實文件引文及缺少證據的結果。
- Tests NOT run and reason: 遠端 CI 未觸發。本次無 UI 變更，瀏覽器工作流程留待 M4，檢索品質評估留待 M5。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 已記錄官方樣本](DATA_SOURCES.md)，本次無新增擷取。
- Known bugs / risks / blockers: 搜尋與比對同步執行。紀錄屬於帳號，研究專案、登出、刪除流程、正式部署限流及完整語料重跑尚待後續實作。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄保存與帳號隔離的設計。
- Uncommitted changes / file ownership warnings: 本機驗收 API 綁定 `127.0.0.1:18010`，驗收資料庫含測試帳號及公開查詢。
- Next 1–3 concrete actions: 串接 M4 查詢輸入與特徵編輯、候選詳情及證據顯示，再接研究專案、收藏及筆記並跑瀏覽器驗收。
- Exact reproduction steps: 見 [M3 私人搜尋紀錄驗收](SETUP.md#m3-私人搜尋紀錄驗收)。

## M3 候選重排

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `c786db2`。
- Current milestone and status: M3 IN_PROGRESS。
- Goal of this session: 接上本機模型重排並保留原始融合順位。
- Files changed (with purpose): `patents.py` 接入重排，`rerank.py` 驗證候選排列，新增重排測試及真實語料驗收。
- Database migrations added/applied: 無。
- API/Schema changes: 混合查詢新增 `rerank` 選項與排序來源欄位，見 [API.md](API.md)。
- Commands actually run and results: Ruff 格式、lint 與 pytest 44 項通過。真實語料三筆的融合順位由 `[1,2,3]` 重排為 `[2,1,3]`，保留版本及原分數。
- Tests NOT run and reason: 遠端 CI 與相關性改善評估未執行。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 官方樣本](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 重排最多讀取八筆標題及摘要，模型排序仍需人工評估。此端點不保存執行紀錄。
- Decisions made (ADR links): 見 [DECISIONS.md](DECISIONS.md)。
- Uncommitted changes / file ownership warnings: 驗收 API 綁定 `127.0.0.1:18009`。
- Next 1–3 concrete actions: 建立有存取隔離的搜尋執行紀錄，保存候選順位、模型版本及已驗證證據。
- Exact reproduction steps: 沿用本機嵌入及分析模型設定，重建 API 並映射到 18009，執行 `python scripts/smoke_rerank.py`。

## M3 文件版本比對預覽

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `7cb46b0`。
- Current milestone and status: M3 IN_PROGRESS。
- Goal of this session: 用本機模型判定已確認技術特徵，逐字核對版本內的原文證據。
- Files changed (with purpose): `comparisons.py` 提供比對 API，`evidence.py` 負責片段選取及模型結果驗證，新增單元和真實語料冒煙測試。
- Database migrations added/applied: 無。沿用 `0004_semantic`。
- API/Schema changes: `POST /api/v1/patents/{document_id}/compare`，詳見 [API.md](API.md)。
- Commands actually run and results: Ruff 格式與 lint、pytest 39 項通過（既有警告一則）。`python scripts/smoke_comparison.py` 用真實文件 `202640162` 得到 supported，核對引文、偏移、XPath、雜湊、書目版無證據及無詞命中。精確查詢冒煙測試通過。
- Tests NOT run and reason: 遠端 CI、整體比對品質及召回率未驗。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 官方樣本](DATA_SOURCES.md)，本次無新增擷取。
- Known bugs / risks / blockers: 只選一段字詞命中的片段。原文依資料庫中已保存的版本與檔案雜湊追溯，請求時未重新讀取 XML。結果暫未持久化。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄版本與選段限制。
- Uncommitted changes / file ownership warnings: 隔離 API 為 `127.0.0.1:18008`，只使用公開樣本與測試特徵。
- Next 1–3 concrete actions: 加入候選重排和可重現搜尋紀錄，再串接已驗證證據。
- Exact reproduction steps: 沿用上一節模型設定與資料庫，重新建置 API 並映射到 `127.0.0.1:18008`，執行 `python scripts/smoke_comparison.py`。

## M3 技術特徵與查詢展開

- Date/time (timezone): 2026-11-09（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `05647fb`。
- Current milestone and status: M3 IN_PROGRESS。M2 DONE。
- Goal of this session: 以本機模型拆解技術特徵，驗證經使用者編輯的中英文檢索詞實際改變混合檢索。
- Files changed (with purpose): `services/api/queries.py` 提供拆解 API；`query_features.py` 驗證模型草稿與展開；`ollama.py` 共用本機模型傳輸；混合 API 接受已確認的特徵；Compose 範例加入可選分析模型設定。
- Database migrations added/applied: 無新遷移。沿用 `0004_semantic` 與隔離語料。
- API/Schema changes: 新增 `POST /api/v1/queries/analyze`，混合端點新增可選 `features` 及回傳 `applied_feature_ids`。見 [API.md](API.md)。
- Commands actually run and results:
  - `python scripts/smoke_query_features.py` 通過，Qwen2.5 1.5B 提取一項有效雙語特徵。編輯後，原本詞彙分支未命中的公開案 `202637274` 同時出現在詞彙與向量分支。
  - Ruff 格式、lint、`pytest -q --basetemp=<new-directory>` 38 項通過，1 則既有 Starlette 棄用警告。混合、語意、精確、詞彙與 M0 冒煙測試已通過。
- Tests NOT run and reason: 遠端 CI 及廣泛模型品質評估未執行。重排、持久化搜尋與引文比對仍待實作。
- Data sources checked (exact URL/date) and license/access notes: 重用 [M1 官方語料](DATA_SOURCES.md)，未新增擷取。核對 [Ollama 結構化輸出](https://docs.ollama.com/capabilities/structured-outputs)。
- Known bugs / risks / blockers: Ollama 0.13.5 的 schema-to-grammar 轉換在 7B 與 1.5B 測試中曾引發程序重啟。改用 JSON 模式、格式範例及 Pydantic 驗證。1.5B 模型可能省略次要特徵或加入多餘欄位，故結果保留草稿性質，多餘欄位不回傳。只用公開測試查詢驗收。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄 JSON 模式、展開及 IPC 候選的處理。
- Uncommitted changes / file ownership warnings: 驗收 API 綁定 `127.0.0.1:18007`。預設開發環境未配置分析模型。
- Next 1–3 concrete actions:
  1. 實作按文件版本的證據選取、逐字引用驗證與技術特徵判定。
  2. 加入重排與搜尋執行紀錄，保存模型、候選排名及已驗證證據。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「M3 本機技術特徵驗收」。

## M3 混合檢索檢查點

- Date/time (timezone): 2026-11-09 02:23（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點為 `1beaef0`。
- Current milestone and status: M3 IN_PROGRESS。M2 DONE。
- Goal of this session: 以真實詞彙與向量結果驗證 RRF 融合、可查核的分支排名和版本去重。
- Files changed (with purpose): `services/retrieval/fusion.py` 負責融合與去重，`services/api/patents.py` 共用候選查詢並提供混合端點。`tests/test_fusion.py` 和 `scripts/smoke_hybrid.py` 驗證單分支、分數與真實語料。
- Database migrations added/applied: 無新遷移。沿用 `0004_semantic` 與既有索引。
- API/Schema changes: 新增 `POST /api/v1/patents/search/hybrid`。見 [API.md](API.md)。
- Commands actually run and results:
  - Ruff 格式和 lint 通過，`pytest -q --basetemp=<new-directory>` 34 項通過，1 則既有 Starlette 棄用警告。
  - `python scripts/smoke_hybrid.py` 使用 18006 埠、真實 TIPO 語料與 Ollama，核對單分支排名、RRF 數值、IPC、分頁及同案公開與公告各自保留。語意、詞彙、精確查詢及 M0 冒煙測試均通過。
- Tests NOT run and reason: 未執行遠端 CI 或相關性評估。未測功能包括模型重排、特徵拆解及證據驗證。
- Data sources checked (exact URL/date) and license/access notes: 本次重用 [M1 官方資料](DATA_SOURCES.md)，無新增擷取。融合公式參考 [RRF 原論文](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)。
- Known bugs / risks / blockers: 每分支限前 100 筆，低排名候選可能被截斷。混合查詢尚未持久化，也未提供模型重排、查詢特徵與證據驗證。現有模型設定僅使用公開資料驗收。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄 RRF、快照與去重規則。
- Uncommitted changes / file ownership warnings: 真實語料保留在原隔離資料庫，驗收 API 綁定 `127.0.0.1:18006`。
- Next 1–3 concrete actions:
  1. 接入本機模型輸出的可編輯中英文檢索特徵，並將特徵接到混合候選。
  2. 加入重排、結果與模型版本的搜尋紀錄，以及按文件版本與原文位置的證據驗證。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「M3 混合檢索驗收」。

## M2 語意檢索驗收

- Date/time (timezone): 2026-11-09 02:18（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點為 `d266abb`。
- Current milestone and status: M2 DONE。M3 NOT_STARTED。
- Goal of this session: 用本機嵌入模型與 PostgreSQL pgvector 驗證真實 TIPO 語料的語意查詢。
- Files changed (with purpose): `services/retrieval/embeddings.py` 驗證本機模型，`index_semantic.py` 產生分段向量。API 加入語意路由與 IPC 共用條件。Compose／環境範本加入可選模型設定。新增測試與語意冒煙驗收。
- Database migrations added/applied: `0004_semantic` 建立模型版本及片段向量表。驗收資料庫由 `0003_lexical` 升級，另從全新資料卷遷移至 head 成功。
- API/Schema changes: `POST /api/v1/patents/search/semantic` 提供模型識別、IPC、排序及分頁。見 [API.md](API.md)。
- Commands actually run and results:
  - 本機 Ollama 0.13.5 搭配已安裝的 `qwen3-embedding:0.6b`，實測 1,024 維。 `python -m services.retrieval.index_semantic` 產生 143 個文件版本的 1,724 筆向量，重跑新增零筆。
  - `python scripts/smoke_semantic.py` 兩個已知目標中英文改寫皆第一名，IPC、分頁和模型欄位通過。精確、詞彙與 M0 冒煙測試通過。
  - 最終 SQL `EXPLAIN (ANALYZE, BUFFERS)` 英文加 IPC 案例使用向量複合主鍵定位候選。一次本機執行 1.316 ms，未含模型推論。
  - Ruff 格式、lint、`pytest -q --basetemp=<new-directory>` 通過，31 項測試及 1 則既有 Starlette 棄用警告。
- Tests NOT run and reason: 遠端 CI 未執行。語意驗收屬小規模已知目標冒煙，ANN 和人工相關性評估尚未執行。
- Data sources checked (exact URL/date) and license/access notes: 重用 [M1 官方語料](DATA_SOURCES.md)，無新增擷取。2026-11-09 核對 [Qwen 模型卡](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) 與 [Ollama 嵌入 API](https://docs.ollama.com/api/embed)。
- Known bugs / risks / blockers: 向量維度固定為 1,024。模型與向量索引須同 digest 和 pipeline。共享 Ollama 僅用公開資料驗收；敏感查詢需私有模型服務。現採精確距離搜尋，未上 ANN。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄版本、分段與排序。
- Uncommitted changes / file ownership warnings: 驗收 API 綁定 `127.0.0.1:18005`，資料在隔離資料卷。預設開發環境未設定嵌入模型。
- Next 1–3 concrete actions:
  1. M3 將詞彙與向量候選以 RRF 合併，區分版本並保存可重現的排序資訊。
  2. 實作可編輯的查詢特徵、重排及按文件版本與原文位置驗證的證據。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「M2 本機語意索引」。

## M2 詞彙檢索檢查點

- Date/time (timezone): 2026-11-09 02:12（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點為 `a9b446d`。
- Current milestone and status: M2 IN_PROGRESS。M1 DONE。
- Goal of this session: 用真實語料驗證繁中／英文詞彙檢索、IPC 篩選和增量索引。
- Files changed (with purpose): `services/retrieval/` 提供分詞和增量索引，`services/api/patents.py` 提供詞彙端點。`tests/test_lexical.py` 和 `scripts/smoke_lexical.py` 驗收分詞、錯誤與真實語料。
- Database migrations added/applied: `0003_lexical` 建立衍生詞彙片段和 GIN 索引。已從 M1 資料庫升級及從空資料庫遷移，預設開發資料庫未套用。
- API/Schema changes: `POST /api/v1/patents/search` 接受詞彙查詢、IPC 與分頁。見 [API.md](API.md)。
- Commands actually run and results:
  - `python -m services.retrieval.index_lexical` 建立 143 個真實文件版本的 1,654 個片段，重跑新增零筆。乾淨隔離庫依次匯入兩期各 5 筆後，索引分別新增 5 筆和 5 筆，第三次新增零筆。
  - `python scripts/smoke_lexical.py`、`python scripts/smoke_patents.py --api http://127.0.0.1:18004` 和 `python scripts/smoke.py` 通過。四個已知目標的詞彙案例均第 1 名，IPC 排除與分頁通過。
  - `EXPLAIN (ANALYZE, BUFFERS)` 確認英詞加 IPC 案例使用 GIN，單次 SQL 執行 0.555 ms。
  - Ruff 格式和 lint 通過，`pytest -q --basetemp=<new-directory>` 27 項通過，1 則既有 Starlette 棄用警告。
- Tests NOT run and reason: 遠端 CI 未執行。詞彙驗收屬已知目標冒煙，尚無人工相關性標註與向量驗收。
- Data sources checked (exact URL/date) and license/access notes: 重用 [M1 的 TIPO 正式語料](DATA_SOURCES.md)，無新增擷取。
- Known bugs / risks / blockers: 漢字雙字基線需同一片段出現全部查詢詞，不處理同義詞、簡繁轉換或跨段比對。詞彙索引在匯入後需明確執行更新命令。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄分詞、排序與實測查詢計畫。
- Uncommitted changes / file ownership warnings: 真實資料留在隔離資料庫及配對原始檔。驗收 API 綁定 `127.0.0.1:18004`。
- Next 1–3 concrete actions:
  1. 加入可替換嵌入模型、模型版本記錄和 pgvector 索引，實測真實語料的語意端點。
  2. 完成 M2 驗收後，M3 接查詢特徵、混合檢索、重排及證據驗證。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「M2 詞彙索引與驗收」。

## M2 精確號碼與詳情 API 檢查點

- Date/time (timezone): 2026-11-09 02:07（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點為 `a8ae20f`。
- Current milestone and status: M2 IN_PROGRESS。M1 DONE。
- Goal of this session: 用真實臺灣專利語料驗證精確申請、公開、公告號查詢及版本隔離。
- Files changed (with purpose): `services/api/patents.py` 提供查詢、詳情、請求項與來源契約，`main.py` 掛載路由。測試覆蓋輸入、錯誤和 URL 篩選，`scripts/smoke_patents.py` 驗收真實語料。
- Database migrations added/applied: 無新遷移。使用既有 `0002_ingestion` 的隔離資料庫。
- API/Schema changes: 新增 `GET /api/v1/patents`、`GET /api/v1/patents/{document_id}` 及 `GET /api/v1/patents/{document_id}/claims`。詳見 [API.md](API.md)。
- Commands actually run and results:
  - Ruff 格式及 lint、`pytest -q --basetemp=<new-directory>` 通過，25 項通過及 1 則既有 Starlette 棄用警告。
  - 建置隔離 API 並在 18003 埠以 `python scripts/smoke_patents.py` 驗證真實查詢。驗收涵蓋分頁、空結果、404、同案公告與公開版本各 13 項請求項、書目版本空請求項及原檔雜湊定位。第二期資料的 FTPS URL 正常回傳。
  - 三種精確查詢皆執行 `EXPLAIN (ANALYZE, BUFFERS)`，結果見 [DECISIONS.md](DECISIONS.md)。`python scripts/smoke.py` 通過。
- Tests NOT run and reason: 未在遠端執行 CI。尚無詞彙及向量檢索可驗收。
- Data sources checked (exact URL/date) and license/access notes: 本次重用 [M1 已驗證的官方資料](DATA_SOURCES.md)，無新增擷取。
- Known bugs / risks / blockers: 詳情只回傳語料實際保存的欄位。請求項依賴、附件、法律狀態、詞彙及向量搜尋待接入。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄指定號碼類型、可見來源及版本選擇。
- Uncommitted changes / file ownership warnings: 真實語料留在隔離資料庫及配對的原始檔目錄。隔離 API 綁定 `127.0.0.1:18003`。
- Next 1–3 concrete actions:
  1. 實作可評估的繁中詞彙檢索、IPC 篩選和索引更新，記錄實際查詢計畫。
  2. 增加可替換的嵌入模型、模型版本紀錄與 pgvector 語意檢索。用真實語料驗收 M2 後再進 M3。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「M2 精確專利號查詢驗收」。

## M1 跨期增量驗收

- Date/time (timezone): 2026-11-09 02:02（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `c498b07`。
- Current milestone and status: M1 DONE，M2 NOT_STARTED。
- Goal of this session: 驗證第二個官方公開卷期的增量匯入，確認先前文件版本與證據仍可追溯。
- Files changed (with purpose): `services/ingestion/import_issue.py` 驗證並保存索引的官方 URL，`verify_document.py` 以文件定位查找公告來源；新增來源 URL 回歸測試並更新開發文件。
- Database migrations added/applied: 無新遷移。沿用隔離驗收資料庫 `patentscope-m1-proof` 的 `0002_ingestion`。
- API/Schema changes: REST 與 Schema 無變更。匯入 CLI 新增可選的 `--index-source-url`。
- Commands actually run and results:
  - `python -m services.ingestion.download` 從官方 FTPS 取得第 24 卷第 18 期索引；XML 宣告與實際皆為 1,984 筆。
  - `import_issue --verified-tipo --batch 024018 --limit 25 --index-source-url <official-url>` 第一次新增 25 個書目版本，第二次 `reused: true`。比較 SQL 快照確認原有 118 個文件 ID 和內容雜湊全數保留，既有 256 項請求項數量相同，批次只增加一筆。資料庫可查到第二期官方 URL 和相符的 SHA-256。
  - `verify_document` 再次逐項核對同一申請案的公開與公告版本，各 13 項請求項；公開版另核對 41 段說明書。
  - Ruff 格式及 lint、`pytest -q --basetemp=<new-directory>` 的 18 項測試、本機冒煙測試皆通過。保留一則既有 Starlette 棄用警告。
- Tests NOT run and reason: 未在遠端執行 CI。此次完成的是已驗證來源的匯入 PoC，尚未測量生產資料庫索引、全量下載或檢索品質。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-09 核對 [政府目錄 15996](https://data.gov.tw/dataset/15996)，並從 [官方 FTPS 第二期索引](ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024018/index.xml) 取得樣本。完整雜湊與授權見 [DATA_SOURCES.md](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 125 個公開號中有 17 份公開全文；另有 1 份公告請求項，未取得該公告的說明書全文。3 份原始公開 XML 缺請求項編號而隔離。尚未整合更廣的資料來源、法律狀態或排程更新。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄來源 URL 與卷期約束。
- Uncommitted changes / file ownership warnings: 真實 XML 保存在本機暫存路徑，驗收資料卷保留。樣本未併入預設開發資料卷。
- Next 1–3 concrete actions:
  1. M2 建立精確申請號、公開號、公告號查詢及文件詳情 API。證據和本文以文件版本 ID 查詢。
  2. 為繁體中文設計可測的詞彙檢索基線，記錄查詢計畫並加上 pgvector 索引與可替換的嵌入模型。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「第二期增量匯入」。

## M1 批次全文與公告版本檢查點

- Date/time (timezone): 2026-11-09 01:58（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點為 `adb612c`。
- Current milestone and status: M1 IN_PROGRESS。M0 DONE。
- Goal of this session: 由 TIPO 清單下載批次全文，並以同一申請案核對公開與公告版本。
- Files changed (with purpose): `services/ingestion/` 增加清單核對、主機快取、公告索引解析及來源回溯。 `tests/` 新增清單、離線快取、重試及公告驗證。更新來源、決策、設定與進度文件。
- Database migrations added/applied: 沿用隔離資料庫 `patentscope-m1-proof` 的 `0002_ingestion`。無新遷移。
- API/Schema changes: REST 無變更。公告文件以 `grant` 階段及 `claims_only` 範圍保存。
- Commands actually run and results:
  - Windows 主機 `import_issue --fetch-only --limit 20` 成功取得 20 份官方 XML。容器預設信任存放區未通過官方 FTPS 憑證鏈驗證，已確認下載失敗會記錄原因。透過 `--cache-only` 匯入 17 份全文，另 3 份因來源缺少請求項編號隔離，重跑回傳 `reused: true`。
  - 匯入 S01 公告 `I941082` 並重跑，第二次回傳 `reused: true`。SQL 確認同一申請號 `114106690` 保留公告、公開全文及公開書目三筆版本。逐項核對兩版各 13 項請求項與公開版 41 段說明書。
  - Ruff 格式、lint、`pytest -q --basetemp=<new-directory>` 的 17 項測試及 `python scripts/smoke.py` 通過。仍有 1 則既有 Starlette 棄用警告。
- Tests NOT run and reason: 同一來源跨卷期增量尚缺第二期公開樣本。遠端 CI 尚未執行。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-09 核對並實取 [官方 S01 公告索引](https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S01)，由 [目錄 15987](https://data.gov.tw/dataset/15987) 連結，適用政府資料開放授權第 1 版。公開卷期與 FTPS 證據見 [DATA_SOURCES.md](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 3 份公開 XML 缺請求項編號，需比對官方公報再決定映射。容器直接 FTPS 需另有可信憑證鏈，現可由主機驗證後快取。尚未驗證跨期發現、更新和公告全文。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄逐筆限速、來源配對及缺號隔離。
- Uncommitted changes / file ownership warnings: 真實 XML 不進 Git。隔離資料卷與 `%TEMP%/patentscope-m1-run/objects` 保留配對。
- Next 1–3 concrete actions:
  1. 取得第二個公開卷期的官方索引，驗證只新增該期的資料及同一期重跑去重。
  2. 核對缺號來源是否有可驗證的正式編號，以及公告全文來源。記錄涵蓋率後完成 M1 驗收。
  3. M1 驗收後進入 M2，從專利編號精確查找及文件詳情 API 開始。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「以官方清單補入全文」及「公告版本比對」。

## M1 初次官方資料匯入紀錄

- Date/time (timezone): 2026-11-09 01:50（Asia/Taipei，UTC+8）。
- Agent: Codex，官方來源研究代理負責 [DATA_SOURCES.md](DATA_SOURCES.md)。
- Branch / commit SHA: `main`，本文件所在的 M1 檢查點提交，起點為 `cb55380`。
- Current milestone and status: M1 IN_PROGRESS。M0 DONE。
- Goal of this session: 取得真正的 TIPO XML 並驗證從原始檔、PostgreSQL 到原文定位的匯入流程。
- Files changed (with purpose): `services/ingestion/` 提供下載、原檔雜湊保存、解析、匯入及回溯驗證。Dockerfile 包含匯入模組。測試涵蓋原始物件校驗、錯誤 XML 隔離、文件定位與卷期檢查。SETUP、PROGRESS、DECISIONS 與 DATA_SOURCES 記錄操作、證據與決策。
- Database migrations added/applied: `0002_ingestion` 建立來源、批次、原始物件關聯、申請案、文件版本、IPC、說明書段落和請求項。新建隔離資料卷從 base 遷移到 `0002_ingestion`，降版在會丟失資料的情況下拒絕。預設開發資料卷未套用本次遷移。
- API/Schema changes: REST 契約無變更。資料表以文件階段及來源雜湊保留版本；此次只驗證發明公開文件。
- Commands actually run and results:
  - `python -m services.ingestion.download` 成功取得官方 HTTPS 卷期索引、相同卷期的 FTPS 索引及個案 XML。兩份索引的 SHA-256 一致，個案雜湊符合來源紀錄。
  - `docker compose -p patentscope-m1-proof run --rm --build migrate` 在新資料卷成功。以 `import_issue --verified-tipo --batch 024019 --limit 100` 匯入 99 筆書目與 1 筆全文，0 筆無效紀錄，0 筆個案隔離。再次匯入回傳 `reused: true`，SQL 確認共 100 筆申請案、100 筆文件、1 個批次。
  - `python -m services.ingestion.verify_document 202639611` 核對原始 SHA-256、19 項請求項與 122 段說明書文字和 XPath。
  - `python -m ruff format --check .` 與 `python -m ruff check .` 通過。`python -m pytest -q --basetemp=<new-directory>` 14 項通過，1 則既有 Starlette 棄用警告。首次使用既有 Windows pytest 暫存路徑時有 2 個測試設定權限錯誤，改用新路徑後通過。`python scripts/smoke.py` 通過。
- Tests NOT run and reason: GitHub Actions 遠端工作未執行。跨卷期增量、公告樣本與批次全文尚未接入。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-09 核對 [政府目錄 15996](https://data.gov.tw/dataset/15996) 與 [政府資料開放授權](https://data.gov.tw/license)，測試 HTTPS 及 FTPS。FTPS 期別 `index_all.xml` 含 2,384 個不需 API 金鑰的個案路徑；實際批次成功率與請求頻率限制待確認。完整路徑、雜湊和限制見 [DATA_SOURCES.md](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 匯入全文暫由操作者以公開號指定個案檔，程式檢查 XML 申請號一致；仍需從官方清單自動綁定每個來源 URL 與公開號。說明書資料限已驗證的 A103.1.0 格式。來源索引不提供日期或 kind code 時保留空值。尚無真實公告樣本及目前法律狀態。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄 M1 的原始檔與文件版本策略。
- Uncommitted changes / file ownership warnings: 真實 XML 不進 Git。隔離驗收資料卷 `patentscope-m1-proof_postgres-data` 保留，容器已停止，原始物件位於本機 `%TEMP%/patentscope-m1-run/objects`。重新啟動前保留資料卷與物件目錄的配對。
- Next 1–3 concrete actions:
  1. 接上已驗證的 FTPS `index_all.xml`，以清單綁定來源 URL 和公開號，限速分批取得全文並保存實際下載狀態及可重試錯誤。
  2. 取得並驗證官方公告樣本，確認申請案、公開及公告版本可共存，並測試同一文件的新版本不覆寫既有原文。
  3. 實測跨卷期增量匯入，記錄全文覆蓋率與失敗原因，完成 M1 驗收後再進 M2。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的 M1 官方樣本指令；如要重用已驗證資料庫，先執行 `docker compose -p patentscope-m1-proof up -d --wait db`，以保留的物件目錄執行回溯驗證。

## M0 歷史交接

- Date/time (timezone): 2026-11-09 01:30（Asia/Taipei，UTC+8）
- Agent: Codex
- Branch / commit SHA: `main`，M0 實作提交為 `199419b`。
- Current milestone and status: M0 DONE。M1 NOT_STARTED。
- Goal of this session: 從僅有 AGENTS.md／CLAUDE.md 的目錄建立並驗收本機開發堆疊。
- Files changed (with purpose): `apps/web/` 繁中 React 狀態頁、Tailwind 與同源代理。 `services/api/` FastAPI 探測端點。 `database/migrations/` 與 `alembic.ini` 管理 DB 修訂。根目錄 Compose、Dockerfile、環境範本、依賴及忽略設定供重現。 `tests/`、`scripts/smoke.py`、`.github/workflows/ci.yml` 提供測試和 CI。README、API、SETUP、DECISIONS、PROGRESS 與本文件記錄契約和交接。
- Database migrations added/applied: 由全新資料卷驗證 `0001_enable_vector`，PostgreSQL 16.14、pgvector 0.8.2。遷移服務以代碼 0 結束，資料庫的 `alembic_version` 記錄正確。重啟同一資料卷也通過；降版刻意保留向量擴充功能。
- API/Schema changes: `GET /api/v1/health` 回應存活。 `GET /api/v1/ready` 實際執行向量距離查詢，DB 無法使用時回傳帶 UUID 的 503 錯誤。OpenAPI 由 FastAPI 產生，見 [API.md](API.md)。
- Commands actually run and results:
  - `python -m ruff format --check .` 與 `python -m ruff check .` 通過。6 個 Python 檔案格式符合。
  - `python -m pytest -q` 有 4 項通過，另有 1 則 Starlette TestClient 使用 httpx 的棄用警告。 `python -m alembic heads` 顯示 `0001_enable_vector (head)`。
  - `docker compose config --quiet` 通過。原目錄的預設 Bake 回傳代碼 100，設 `COMPOSE_BAKE=false` 後 `docker compose up -d --build --wait --wait-timeout 180` 成功。另以 `git checkout-index --all --prefix=<temp>/` 建立純 ASCII 路徑的乾淨副本，用不同 Compose 專案名稱、連接埠和全新資料卷，採預設 Bake 重跑完整建置、遷移和冒煙測試，全部通過。
  - `python scripts/smoke.py` 通過 API 存活、Web 代理的 pgvector 就緒及繁中 HTML 首頁檢查。 `docker compose exec -T web npm run build` 內含 TypeScript 型別檢查，通過。 `docker compose exec -T web npm audit` 回報 0 項漏洞。映像建置中的 `npm ci` 成功。
  - `docker compose stop db` 後，API 存活為 200、Web 代理就緒為 503 `DATABASE_UNAVAILABLE`。在瀏覽器確認載入中與離線文案。執行 `docker compose up -d --wait db` 並按「重新檢查」後，頁面恢復就緒，冒煙測試再次通過。
- Tests NOT run and reason: GitHub Actions 遠端執行待有遠端及推送後確認。M0 無專利資料、模型或檢索流程可測。瀏覽器已手動驗收上述狀態。
- Data sources checked (exact URL/date) and license/access notes: 本階段未檢查 TIPO 資料集，也未匯入任何資料。M1 從官方目錄 https://cloud.tipo.gov.tw/S220/opdata 開始，授權、配額、下載能力待查。
- Known bugs / risks / blockers: Windows 目前目錄的 Bake 建置問題與 Git 擁有權排查方式見 [SETUP.md](SETUP.md)。Starlette 發出測試用戶端棄用警告。TIPO 的實際資料授權、存取條件及公開／公告版本欄位仍待驗證。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄 M0 選擇，沿用 AGENTS.md 的既定技術架構。
- Uncommitted changes / file ownership warnings: M0 交付包含初始 Git 提交。 `.env`、依賴目錄與編譯輸出由 Git 忽略。原本的 AGENTS.md 與 CLAUDE.md 內容保留。
- Next 1–3 concrete actions:
  1. 核對一個官方 TIPO 資料集的入口、授權、涵蓋、更新頻率、下載限制與樣本，記入 `docs/DATA_SOURCES.md`。
  2. 用實際樣本確認申請號、公開／公告號、kind code 與請求項定位，再加入保留原檔雜湊和文件版本的資料表、解析器及冪等批次匯入。
  3. 存取許可時匯入 100–500 筆，抽查原檔到 DB 的回溯，重跑同批驗證去重。存取受阻則記錄阻礙並用 DEMO fixture 驗證解析，保持真實匯入未完成。
- Exact reproduction steps: 在根目錄依 [README](../README.md) 建立 `.env`，執行 `docker compose up -d --build --wait --wait-timeout 180`、`python scripts/smoke.py`，再執行 README 的本機檢查。若 Windows Bake 出現代碼 100，依 [SETUP.md](SETUP.md) 暫時停用 Bake 或改用 ASCII 路徑的工作副本。

## 2026-11-09 產品規格補充（Asia/Taipei）

- Codex 在 [PROGRESS.md](PROGRESS.md) 記錄適用於不同技術領域的 M1–M5 驗收條件。智慧冰箱是可替換的例子。使用者指定的 PDF 報告、公開／公告版本、證據定位及發明構想隱私已列入。
- 本次修改 PROGRESS 與 HANDOFF。API、資料庫遷移、程式碼與里程碑狀態無異動。
- 本次重新執行 `python scripts/smoke.py`，通過存活、Web 代理的 pgvector 就緒與繁中首頁檢查。其餘測試結果沿用上方 M0 驗收紀錄。

- 本次釐清驗收輸入可替換，只修改上述兩份文件。執行 `git diff --check`，通過。程式測試沿用前述紀錄。


- 本次 Codex 負責 M3 混合候選與驗收。

## M6 Playwright 品質關卡

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `fd9b75e`。
- Current milestone and status: M6 IN_PROGRESS（目標檔定義）。本次補齊 M0 瀏覽器冒煙測試。
- Goal of this session: 對隔離的前端、FastAPI 與 PostgreSQL 建立可重跑的 TypeScript E2E，接入 GitHub Actions。
- Files changed (with purpose): `apps/web` 套件設定、Playwright 設定與案例、Docker 建置排除產物、`.github/workflows/ci.yml` 及三份進度／測試／交接文件。
- Database migrations added/applied: 無新增。Compose 專案 `patentscope-e2e-1124` 使用新卷執行既有 Alembic 遷移。
- API/Schema changes: 無。
- Commands actually run and results: Compose 啟動及 `scripts/smoke.py` 通過。Chromium `npm run test:e2e --prefix apps/web` 2 通過。Ruff 格式 66 檔與 lint 通過。Pytest 47 通過，1 項既有 Starlette 棄用警告。
- Tests NOT run and reason: 未執行遠端 Actions。此次使用空白測試卷，未執行 TIPO 檢索／PDF 回歸及其他瀏覽器。
- Data sources checked (exact URL/date) and license/access notes: 本次未存取 TIPO；只使用合成帳號和專案。
- Known bugs / risks / blockers: 首次桌面案例定位錯誤已修正；平行重跑會共用產物目錄。Windows 預設 pytest 暫存目錄存取被拒，改用獨立 `--basetemp` 後全部通過。首次失敗留下合成帳號於獨立卷。
- Decisions made (ADR links): 沿用既有架構，使用 Chromium 同時驗證桌面及手機 viewport。
- Uncommitted changes / file ownership warnings: 測試產物已由 Git 忽略，獨立測試卷保留。
- Next 1–3 concrete actions: 將既有真實專利瀏覽器腳本轉為有固定資料種子的 TypeScript 案例，補上 PDF 與來源證據斷言，再查核遠端 Actions 結果。
- Exact reproduction steps: 依 [TESTING](TESTING.md#playwright-typescript-冒煙測試) 的隔離 Compose 和瀏覽器指令。

## M6 真實 TIPO Playwright 回歸

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `d181eb0`。
- Current milestone and status: M6 IN_PROGRESS（目標檔定義）。
- Goal of this session: 將已核對的真實 TIPO 全文、混合檢索、請求項引文及 PDF 下載納入 TypeScript E2E。
- Files changed (with purpose): `apps/web/e2e/tipo-research.spec.ts`、Playwright 設定及測試交接文件。
- Database migrations added/applied: 無。沿用隔離的靜態部署 `patentscope-static-proof` 及已建立的語料索引。
- API/Schema changes: 無。
- Commands actually run and results: `Get-FileHash` 確認既有卷期索引和原始全文 XML 的 SHA-256。設定 `PATENTSCOPE_E2E_TIPO=1` 後執行 `npm run test:e2e --prefix apps/web`，桌面及手機共 2 通過。未設定旗標時原有冒煙測試 2 通過，前端型別檢查及建置通過。
- Tests NOT run and reason: 遠端 Actions 未準備官方樣本與本機模型。PDF 繁中內容及版面尚未由此案例驗證。未變更 Python。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-10 重新核對既有快取雜湊及 API 文件版本，來源為 `ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/2419202639611/113133932-A0304.xml`。授權與取得紀錄見 [DATA_SOURCES](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 首輪誤以為該部署含 `202640162` 全文，API 證實只有書目及摘要。切換至已核對的 `202639611`，並將重複 XPath 定位限定在專利詳情後通過。真實資料案例使用本機模型，執行時間可能隨硬體而變。
- Decisions made (ADR links): 本機真實資料案例以 `@tipo` 獨立執行，沿用預設無模型的 CI 冒煙案例。
- Uncommitted changes / file ownership warnings: 瀏覽器除錯產物已由 Git 忽略。案例以合成帳號執行並清理。
- Next 1–3 concrete actions: 為 CI 準備隔離且可重建的固定來源與模型，擴充 PDF 內容和研究歷史斷言，驗證遠端品質關卡。
- Exact reproduction steps: 見 [TESTING](TESTING.md#真實-tipo-資料的-typescript-回歸)。

## M6 繁中 PDF 驗收

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `cf963f7`。
- Current milestone and status: M6 IN_PROGRESS。
- Goal of this session: 驗證瀏覽器實際下載的繁中 PDF 內容、來源與版面。
- Files changed (with purpose): Playwright TIPO 案例加入報告語意斷言，`scripts/inspect_test_report.py` 解析 PDF 文字與連結，`requirements-dev.txt` 固定 pypdf，更新測試及交接文件。
- Database migrations added/applied: 無。沿用隔離部署及原有官方索引。
- API/Schema changes: 無。
- Commands actually run and results: 本機模型與官方案 `202639611` 驗證桌面及手機 Chromium 各 1 項。用 Poppler `pdftoppm` 渲染桌面 PDF 共兩頁並目視核對。前端建置與型別檢查通過，Ruff 格式與 lint 通過，Pytest 47 通過、1 項既有警告。
- Tests NOT run and reason: 真實資料仍未接遠端 Actions。僅目視檢查一份實際下載檔，未建立視覺快照基準。
- Data sources checked (exact URL/date) and license/access notes: 沿用 2026-11-10 核對的 [官方案來源](DATA_SOURCES.md)，無新增下載。
- Known bugs / risks / blockers: 初次斷言通過後 Windows HTML reporter 遇到 EPERM，改用獨立可寫目錄。樣本長雜湊換行，原文引用跨到第二頁，渲染可讀。
- Decisions made (ADR links): pypdf 僅作開發測試依賴，報告生成程式無變更。
- Uncommitted changes / file ownership warnings: PDF 與 PNG 都位於忽略的測試產物目錄。
- Next 1–3 concrete actions: 將固定官方樣本與模型供應加入隔離 CI，補足研究歷史及跨版本回歸。
- Exact reproduction steps: 見 [TESTING](TESTING.md#真實-tipo-資料的-typescript-回歸)。

## M6 固定官方樣本與遠端驗收工作

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `297f5d2`。
- Current milestone and status: M6 IN_PROGRESS。
- Goal of this session: 讓真實資料的 Playwright 案例能從新資料卷重建，準備 GitHub Actions 手動驗收。
- Files changed (with purpose): `scripts/seed_tipo_e2e.py` 固定來源、雜湊與匯入順序，`tests/test_tipo_e2e_seed.py` 驗證快取雜湊不符時拒絕且保留原檔，`.github/workflows/tipo-e2e.yml` 設定隔離的 CPU 模型與瀏覽器工作，更新驗收及來源文件。
- Database migrations added/applied: 無新增。新建 Compose 專案 `patentscope-tipo-e2e` 已套用既有 migrations。
- API/Schema changes: 無。
- Commands actually run and results: `python -m scripts.seed_tipo_e2e <cache>` 重新下載兩份官方 XML，匯入 1 份全文、0 筆隔離，核對 19 項請求項與 122 段說明書，索引 145 詞彙片段與 157 向量。加 `--offline` 重跑重用批次，新增 0 片段、0 向量。Playwright 對新卷通過桌面與手機 2 項，Ruff 格式／lint 通過，Pytest 48 通過、1 項既有警告。
- Tests NOT run and reason: 本機 Git 沒有設定 remote，無法執行 GitHub Actions。遠端 FTPS 及該工作容器的 CPU 推論待驗。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-10 重抓 FTPS 固定期別與全文，兩份雜湊符合。目錄與授權見 [DATA_SOURCES](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 固定來源若無法取得，或 Ollama 標籤日後改指不同摘要，工作會失敗；應保留錯誤並重新查核。
- Decisions made (ADR links): 遠端真實資料驗收用手動觸發；既有 push／PR 冒煙流程沿用。
- Uncommitted changes / file ownership warnings: 新的隔離專案已停止，測試資料卷與官方快取保留供重現。
- Next 1–3 concrete actions: 有遠端時執行 `Official patent E2E`；補充歷史、跨版本及瀏覽器相容性驗證。
- Exact reproduction steps: 見 [TESTING](TESTING.md#自動建立固定官方樣本)。

## M6 研究歷史與平板回歸

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `a29412b`。
- Current milestone and status: M6 IN_PROGRESS。
- Goal of this session: 驗證研究歷史經登出及重載後仍能讀取保存的引文和 PDF，加入平板瀏覽器覆蓋。
- Files changed (with purpose): `apps/web/e2e/tipo-research.spec.ts` 驗證重開搜尋，`apps/web/playwright.config.ts` 加入平板，以及測試、進度與交接文件。
- Database migrations added/applied: 無。沿用隔離的資料庫。
- API/Schema changes: 無。
- Commands actually run and results: `npm run typecheck --prefix apps/web` 通過。官方樣本及本機模型 E2E 在 `18123` 跑桌面、平板及手機三項均通過。冒煙套件在 `18124` 重跑，桌面、平板及手機三項均通過。
- Tests NOT run and reason: 僅變更前端測試及文件，未重跑 Python。尚無 Git 遠端，未執行遠端 CI。其他瀏覽器引擎與實體裝置尚未驗證。
- Data sources checked (exact URL/date) and license/access notes: 沿用已核對的公開案 `202639611` 與 [來源紀錄](DATA_SOURCES.md)，本次未重新下載。
- Known bugs / risks / blockers: iPad 使用 Chromium 模擬，Safari 相容性需單獨驗證。
- Decisions made (ADR links): 在現有 Chromium 套件加入平板配置。
- Uncommitted changes / file ownership warnings: 無。瀏覽器測試產物由 Git 忽略。
- Next 1–3 concrete actions: 補跨版本回歸、Firefox／WebKit 驗收，並於遠端可用時執行官方 E2E 工作。
- Exact reproduction steps: 見 [TESTING](TESTING.md#研究歷史與平板)。

## M6 Firefox 與 WebKit 相容性

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `e0f20c8`。
- Current milestone and status: M6 IN_PROGRESS。
- Goal of this session: 對現有的帳號與真實研究流程補 Firefox 與 WebKit 驗收。
- Files changed (with purpose): Playwright 配置、手動官方 E2E 工作、測試及交接文件。
- Database migrations added/applied: 無。
- API/Schema changes: 無。
- Commands actually run and results: 安裝 Firefox 與 WebKit 後，分別執行兩種引擎的帳號／專案冒煙與官方專利回歸，共 4 項通過。前端建置和型別檢查通過。
- Tests NOT run and reason: 未變更 Python。未設定 Git 遠端，GitHub runner 的三引擎工作尚未執行。未測 Safari 和實體裝置。
- Data sources checked (exact URL/date) and license/access notes: 沿用公開案 `202639611`，無新增下載。見 [資料來源](DATA_SOURCES.md)。
- Known bugs / risks / blockers: Windows Playwright WebKit 的結果只適用已測引擎環境。
- Decisions made (ADR links): 平日 CI 使用 Chromium，手動官方工作啟用三種引擎。
- Uncommitted changes / file ownership warnings: 測試產物由 Git 忽略。
- Next 1–3 concrete actions: 擴充真實跨版本回歸、補剩餘 CI 關卡與在遠端可用時執行官方工作。
- Exact reproduction steps: 見 [TESTING](TESTING.md#firefox-與-webkit-相容性)。

## M6 跨版本證據回歸

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `8a68d5c`。
- Current milestone and status: M6 IN_PROGRESS。
- Goal of this session: 在同一檢索確認公開、公告兩版的請求項與來源分開。
- Files changed (with purpose): `apps/web/e2e/patent-versions.spec.ts`、Playwright 選擇設定及三份驗收／交接文件。
- Database migrations added/applied: 無。沿用隔離的既有真實語料庫，案例只讀。
- API/Schema changes: 無。
- Commands actually run and results: 前端型別檢查通過，兩份封存 XML 的 `Get-FileHash` 符合固定雜湊。由 Vite `18126` 同源代理至驗收 API `18022`，桌面、平板及手機 Chromium 重跑共 3 通過。另以 `--list --reporter=list` 驗證既有兩套測試選擇各自維持三個案例。
- Tests NOT run and reason: 本次未重跑 Python；新案例尚未移入遠端 CI。遠端仍未設定，公告歷史期別須使用封存副本。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-10 核對既有公開 `202640162` 全文、S01 第 53 卷第 28 期的 `I941082`。未重新下載。精確來源見 [資料來源](DATA_SOURCES.md)及 [評估來源清單](../evaluation/tipo_review_pool.json)。
- Known bugs / risks / blockers: 以 HTML reporter 預設路徑執行列舉時曾遇 Windows EPERM，正式回歸使用專用輸出目錄。初次手機案例等待比對回應超過 60 秒，改為有上限的 110 秒並循序重跑後三項通過，單次逾時根因未確認。
- Decisions made (ADR links): `PATENTSCOPE_E2E_TIPO=versions` 將雙版本語料案例獨立選出。
- Uncommitted changes / file ownership warnings: 瀏覽器產物由 Git 忽略。
- Next 1–3 concrete actions: 準備可安全重取的公告期別快取，再把版本案例接進遠端；接續補前端 lint 及其 CI 關卡。
- Exact reproduction steps: 見 [TESTING](TESTING.md#同案公開與公告版本)。

## M6 前端 lint 關卡

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `a72ca60`。
- Current milestone and status: M6 IN_PROGRESS。
- Goal of this session: 補前端 lint 指令及 push／PR CI 關卡。
- Files changed (with purpose): `apps/web/package.json` 與 lockfile 固定 Oxlint，`.github/workflows/ci.yml` 加入 lint，並更新測試與交接文件。
- Database migrations added/applied: 無。
- API/Schema changes: 無。
- Commands actually run and results: 在全新暫存副本以 Node 22.12 執行 `npm ci`、`npm run lint`、`npm run build` 均通過。刻意讓 useEffect 條件式呼叫時，lint 如預期以代碼 1 失敗。Windows 與 Linux Node 22 容器的乾淨安裝、lint 及建置均通過，npm 安裝摘要均為零漏洞。
- Tests NOT run and reason: 只變更靜態檢查工具及 CI，未重跑 Python 或瀏覽器。尚無遠端，GitHub runner 結果待驗證。
- Data sources checked (exact URL/date) and license/access notes: 無專利資料變更。
- Known bugs / risks / blockers: 工作區的 `npm ci` 遇到 Windows 原生模組檔案鎖定，改在全新暫存副本驗證，原工作區亦已用 npm install 恢復並通過 lint。
- Decisions made (ADR links): ESLint 試裝出現 Node 引擎相容性及 audit 告警，最終選用支援 Node 22.12 並包含 React Hooks 規則的 Oxlint。
- Uncommitted changes / file ownership warnings: 暫存副本與負向測試檔在工作區外。
- Next 1–3 concrete actions: 補專用 PostgreSQL 整合關卡與錯誤流程 E2E，待有遠端再驗證工作。
- Exact reproduction steps: 見 [TESTING](TESTING.md#前端靜態檢查)。

## M6 PostgreSQL 與 API 整合關卡

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `7de576e`。
- Current milestone and status: M6 IN_PROGRESS。
- Goal of this session: 建立可在獨立資料卷重跑的 PostgreSQL 與 API 整合測試。
- Files changed (with purpose): `tests/integration/test_postgresql.py`、`docker-compose.test.yml`、一般 CI 工作及進度、測試和交接文件。
- Database migrations added/applied: 無新增。從空白的 `patentscope-pg-integration` 卷執行 Alembic upgrade head。
- API/Schema changes: 無。
- Commands actually run and results: PostgreSQL 整合測試 2 通過，合併執行共 50 通過，Ruff 格式及 lint 通過。測試直接連 PostgreSQL 驗證 Alembic head、pgvector 與搜尋紀錄跨帳號外鍵，並以 FastAPI TestClient 驗證真實 DB readiness 及 API 專案權限。
- Tests NOT run and reason: 未修改前端或 API 實作，未重跑瀏覽器。未設定 Git 遠端，GitHub runner 尚未執行。
- Data sources checked (exact URL/date) and license/access notes: 無專利資料變更。
- Known bugs / risks / blockers: Pytest 仍有既有 Starlette TestClient 棄用警告。
- Decisions made (ADR links): CI 使用獨立 `patentscope_test` 資料庫，僅在回環位址開放測試連接埠。
- Uncommitted changes / file ownership warnings: 專用測試資料卷保留，合成測試帳號透過 API 清理。
- Next 1–3 concrete actions: 補搜尋錯誤和服務不可用的瀏覽器回歸，並於遠端可用時驗證 CI。
- Exact reproduction steps: 見 [TESTING](TESTING.md#postgresql-與-api-整合)。

## M6 搜尋錯誤及空結果回歸

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `2c96353`。
- Current milestone and status: M6 IN_PROGRESS。
- Goal of this session: 分開驗證錯誤輸入、服務失敗、空結果、用戶端逾時與重試。
- Files changed (with purpose): 新增 `apps/web/e2e/search-errors.spec.ts`，擴充官方 E2E 案例，修正 `research.tsx` 的逾時分類，更新驗收文件。
- Database migrations added/applied: 無。沿用無模型與單筆官方語料的獨立資料庫。
- API/Schema changes: 無。
- Commands actually run and results: 前端 lint、型別檢查與建置通過。修正後在 Chromium 三個裝置配置、Firefox 和 WebKit 重跑工作台與錯誤流程共 15 項通過，官方空結果、引文、歷史與 PDF 共 5 項通過。
- Tests NOT run and reason: 未修改後端，未重跑 Python。尚無 Git 遠端，未執行遠端工作。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [固定官方資料](DATA_SOURCES.md) 的公開案 `202639611`，無新增下載。
- Known bugs / risks / blockers: WebKit 原先把計時中止回報為 Fetch is aborted。前端改依逾時訊號的原因分類，保留 180 秒設定。逾時案例在測試瀏覽器內縮短單次計時並暫停傳輸，驗證用戶端行為；未量測完整 180 秒等待或正式環境的服務恢復時間。
- Decisions made (ADR links): 無效日期及模型不可用使用真實 HTTP 422／503；空結果使用真實 200 和空清單；逾時不偽造 API 回應。
- Uncommitted changes / file ownership warnings: 測試產物由 Git 忽略。
- Next 1–3 concrete actions: 補檢索排序及分頁回歸，並在有遠端後執行 CI。
- Exact reproduction steps: 見 [TESTING](TESTING.md#搜尋失敗空結果與逾時)。

## M6 真實語料排序與分頁

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `c1c157d`。
- Current milestone and status: M6 IN_PROGRESS。
- Goal of this session: 用多筆官方語料確認預覽搜尋的融合排序與分頁。
- Files changed (with purpose): `apps/web/e2e/search-pagination.spec.ts` 及驗收文件。
- Database migrations added/applied: 無。使用既有隔離語料庫，案例只讀。
- API/Schema changes: 無。
- Commands actually run and results: `npm run lint` 和 `npm run typecheck` 通過。以 `PATENTSCOPE_E2E_TIPO=versions` 執行版本及分頁案例，桌面、平板、手機共 6 項通過。使用 Vite `18126` 同源代理至 `18022`。
- Tests NOT run and reason: 只改瀏覽器測試及文件，未重跑 Python。未驗證保存後分頁、模型重排或遠端工作。
- Data sources checked (exact URL/date) and license/access notes: 沿用隔離的 TIPO 官方樣本及索引，未重新下載。見 [DATA_SOURCES](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 單筆官方種子無法測試分頁。遠端仍需要足夠的固定官方樣本。
- Decisions made (ADR links): 在現有多文件驗收配置執行，驗證關閉重排時的融合排名。
- Uncommitted changes / file ownership warnings: 測試產物位於暫存目錄，Vite 驗收服務已停止。
- Next 1–3 concrete actions: 補已保存搜尋分頁及排序選項的回歸；繼續準備遠端多文件語料。
- Exact reproduction steps: 見 [TESTING](TESTING.md#檢索排序與分頁)。

## M6 已保存搜尋分頁

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `3d44d64`。
- Current milestone and status: M6 IN_PROGRESS。
- Goal of this session: 驗證保存搜尋從歷史重開後保留原候選快照及分頁。
- Files changed (with purpose): `apps/web/e2e/search-pagination.spec.ts` 與驗收文件。
- Database migrations added/applied: 無，使用既有隔離語料。
- API/Schema changes: 無。
- Commands actually run and results: `npm run lint` 與 `npm run typecheck` 通過。於 Vite `18126` 代理至官方樣本 API `18022`，執行 `PATENTSCOPE_E2E_TIPO=versions` 的分頁測試。桌面、平板與手機的預覽及已保存分頁共 6 通過。
- Tests NOT run and reason: 未修改後端，未重跑 Pytest。未執行遠端、多文件模型重排與其他瀏覽器引擎。
- Data sources checked (exact URL/date) and license/access notes: 沿用既有 TIPO 語料，無新增下載。見 [DATA_SOURCES](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 單筆官方種子不具備分頁條件。遠端仍未設定。
- Decisions made (ADR links): 案例驗證快照分頁，不觸發新一輪模型檢索。
- Uncommitted changes / file ownership warnings: 測試產物寫在專用暫存目錄，合成帳號由 API 清理。
- Next 1–3 concrete actions: 補模型重排驗收及可重建的遠端多文件樣本。
- Exact reproduction steps: 見 [TESTING](TESTING.md#檢索排序與分頁)。

## M6 模型重排序驗收

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `fe7bb60`。
- Current milestone and status: M6 IN_PROGRESS。
- Goal of this session: 修正真實候選的重排失敗並驗證 API 與畫面排序。
- Files changed (with purpose): `services/retrieval/rerank.py` 改為候選限定的結構化輸出，更新單元與瀏覽器測試及 API、驗收與交接文件。
- Database migrations added/applied: 無。沿用隔離的官方樣本。
- API/Schema changes: 重排模型流程版本升為 `ollama-listwise-v2`，API 欄位與錯誤格式維持。
- Commands actually run and results: 舊版隔離 API 對已驗證的公開與公告候選回傳 503。新 API 容器以相同查詢回傳完整兩筆；未篩選的 API 查詢成功重排八筆。兩候選的 Playwright 桌面、平板與手機共 3 通過，Pytest 單元 48 通過，Ruff、前端 lint 與型別檢查通過。
- Tests NOT run and reason: 未重跑 PostgreSQL 整合測試。尚未執行遠端多文件工作或人工排序品質複核。
- Data sources checked (exact URL/date) and license/access notes: 沿用真實 `202640162` 與 `I941082` 等已匯入的 [TIPO 樣本](DATA_SOURCES.md)，未重新下載。
- Known bugs / risks / blockers: 模型仍可能輸出無效排列，後端會拒絕。首輪瀏覽器斷言誤用僅保存檢索可見的說明，改核對預覽的勾選狀態及逐列 API 名次後通過。
- Decisions made (ADR links): 使用 Ollama JSON Schema 約束編號與長度，候選唯一性由後端驗證。
- Uncommitted changes / file ownership warnings: 測試產物在專用暫存目錄。臨時 API 與 Vite 已停止。
- Next 1–3 concrete actions: 準備可重建的遠端多文件樣本，補人工相關性標註及重排品質評估。
- Exact reproduction steps: 見 [TESTING](TESTING.md#本機模型重排序)。

## 2026-11-10 交由 Claude Code 接續

- 接手起點為 `main` 的 `9d7a82e`，當時工作區乾淨。Codex 目標由使用者暫停，M6 仍在進行。接手交接只更新本文件。
- 原始目標檔為 `C:\Users\xnikz\.codex\attachments\38124b2a-5177-4f61-835c-8117b7ec1c76\goal-objective.md`。先完整閱讀該檔、`CLAUDE.md`、`AGENTS.md`，再核對 Git、[進度](PROGRESS.md)、[測試](TESTING.md)與本文件最近一節。原始目標的 M6 是整合、安全與部署，與 AGENTS 的 M6 選配延伸命名不同，驗收範圍以原始目標為準。
- 最近一次實測是重排修正後的 48 項單元測試、Ruff、前端 lint／型別檢查及三種 Chromium 裝置的重排回歸。未篩選的真實語料也成功重排前八筆。先前的 PostgreSQL 整合測試、瀏覽器相容性及繁中 PDF 有各自的實測紀錄，接手後依變更範圍重新驗證。
- **下一步**：檢查 `scripts/seed_tipo_e2e.py` 與 `.github/workflows/tipo-e2e.yml`。現有種子只有一份全文；先用已核對雜湊的官方封存期別建立足夠分頁的隔離語料，驗證空白卷遷移、重跑不重複及保存後分頁，再接 CI。跨版本測試另需公開 `202640162` 全文及公告 `I941082` 的固定期別；移動中的最新期 S01 不能當作歷史封存檔替代。來源見 [DATA_SOURCES](DATA_SOURCES.md)。
- **外部依賴**：Git 未設定遠端，GitHub Actions 未實跑。由使用者指定遠端後再驗證。重排的品質評估仍缺人工相關性標註，見 [EVALUATION](EVALUATION.md)；已通過的流程測試只證明候選及排名資料完整。
- 不要重做已驗收工作，也不要將既有文件的成功紀錄擴大解讀為整體完成。每輪執行適用測試並更新 PROGRESS 和 HANDOFF，保留未驗證及外部阻礙。正式資料、設定及憑證依專案規範處理。

## M6 可重建的官方多文件語料

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Claude Code。
- Branch / commit SHA: `main`，本文件所在提交及其前一個排序修正提交，起點 `5d13594`。
- Current milestone and status: M6 IN_PROGRESS（原始目標檔定義）。
- Goal of this session: 讓分頁、跨版本與重排案例使用可由官方來源重建的隔離語料，並接入手動 CI 工作。
- Files changed (with purpose): `scripts/seed_tipo_e2e.py` 改為多文件種子，固定 24 個檔案雜湊並核對匯入筆數。`services/ingestion/download.py`、`import_issue.py` 接受公告期別封存目錄 `PatentIsuRegSpecXMLA`。`services/api/patents.py` 修正同分版本排序。`apps/web/e2e/patent-versions.spec.ts` 的公告來源雜湊改為封存檔。`.github/workflows/tipo-e2e.yml` 加入 `versions` 套件，逾時改為 90 分鐘。`tests/test_index_source.py`、`tests/test_tipo_e2e_seed.py` 補測試。更新 DATA_SOURCES、DECISIONS、TESTING、PROGRESS。
- Database migrations added/applied: 無新增。新卷 `patentscope-tipo-multi` 從空白遷移到 `0009_session_message_cascade`，匯入前文件數為 0。
- API/Schema changes: 無欄位變更。詞彙、向量與混合檢索在同分時先排內容較完整的版本。
- Commands actually run and results:
  - `python -m scripts.seed_tipo_e2e <cache>` 從 FTPS 下載 24 個檔案，雜湊全部相符。匯入結果為 99 書目加 1 全文、17 全文加 3 隔離、1 筆公告。`verify_document` 核對 `202639611`（19 項請求項、122 段）、`202640162`（13 項、41 段）及 `I941082`（13 項）。索引 117 個版本、1,677 個詞彙片段、1,624 個向量。
  - 加 `--offline` 重跑，三個批次皆 `reused: true`，新增 0 片段 0 向量，文件、請求項、段落、批次、原始物件與索引筆數前後相同。
  - `PATENTSCOPE_E2E_TIPO=versions` 首輪 9 通過 3 失敗，三項都是跨版本案例找不到 `202640162` 全文版。修正排序並重建 API 後 12 項通過。`PATENTSCOPE_E2E_TIPO=1` 兩輪各 3 項通過。皆為 Chromium 桌面、平板、手機。
  - Ruff 格式與 lint 通過。Pytest 含 PostgreSQL 整合共 51 通過，1 則既有 Starlette 警告。前端 Oxlint 與 `tsc --noEmit` 通過。
- Tests NOT run and reason: 未設定 Git 遠端，GitHub Actions 未執行。Firefox、WebKit 未對新語料重跑。未重跑無模型的冒煙與錯誤流程套件，前端程式無變更。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-10 匿名 FTPS 列出 `/PatentIsuRegSpecXMLA/115/`，下載第 53 卷第 28 期 `index.xml`（15,597,462 bytes，SHA-256 `60936a7a…`）。它與 S01 端點副本不同檔，`I941082` 的 13 項請求項文字逐字相同。詳見 [DATA_SOURCES](DATA_SOURCES.md#公告期別的固定封存檔)。
- Known bugs / risks / blockers:
  - 跨版本案例的公告雜湊已改為封存檔，舊驗收庫 `patentscope-m1-proof`（API `18022`）保存的是 S01 副本，該案例對舊庫會失敗。分頁與重排案例不受影響。
  - 這台機器的 Docker Desktop 無法掛載 D: 槽路徑，錯誤為 `mkdir /run/desktop/mnt/host/d: file exists`。快取改放 C: 槽後成功，根因未查。
  - 本機 GPU Ollama 建立向量約 100 秒。GitHub runner 的 CPU 推論時間未量測，90 分鐘上限是估計。
  - 官方若替換任一封存檔，種子會在匯入前以雜湊不符失敗，需要重新查核來源。
- Decisions made (ADR links): [同分文件版本排序](DECISIONS.md#m6-同分文件版本排序)。
- Uncommitted changes / file ownership warnings: Compose 專案 `patentscope-tipo-multi` 已停止，資料卷保留。官方快取在 `%TEMP%\patentscope-tipo-multi`，約 97 MB。
- Next 1–3 concrete actions: 使用者指定 Git 遠端後手動執行 `Official patent E2E` 並依實測調整逾時。對新語料補跑 Firefox 與 WebKit。人工複核 35 組候選後重跑檢索與重排評估。
- Exact reproduction steps: 見 [TESTING](TESTING.md#自動建立固定官方樣本)。
## M6 首次遠端 CI

- Date/time (timezone): 2026-11-10（Asia/Taipei）。
- Agent: Claude Code。
- Branch / commit SHA: `main`，本文件所在提交，起點 `12340ce`。
- Current milestone and status: M6 IN_PROGRESS。
- Goal of this session: 依使用者指定設定 Git 遠端並驗證一般 CI。
- Files changed (with purpose): PROGRESS 與本文件記錄遠端結果。
- Database migrations added/applied: 無。
- API/Schema changes: 無。
- Commands actually run and results: `git remote add origin https://github.com/Johnnnny0823/RAG.git` 後 `git push -u origin main`，遠端原為空。推送觸發的 [執行 42833320981](https://github.com/Johnnnny0823/RAG/actions/runs/42833320981) 全部步驟通過，以 `gh run watch --exit-status` 確認。
- Tests NOT run and reason: 手動 `Official patent E2E` 未觸發，等待使用者決定。本次只改文件，未重跑本機測試。
- Data sources checked (exact URL/date) and license/access notes: 無新增。
- Known bugs / risks / blockers: CI 回報 Node.js 20 動作棄用與 `ubuntu-latest` 遷移兩則警告。本機 git 的背景 repack 在 D: 槽遇到權限錯誤，`git fsck` 通過。
- Decisions made (ADR links): 無。
- Uncommitted changes / file ownership warnings: 無。
- Next 1–3 concrete actions: 手動執行 `Official patent E2E` 並依實測調整逾時。處理 CI 的兩則警告。人工複核 35 組候選後重跑評估。
- Exact reproduction steps: `gh run list --repo Johnnnny0823/RAG`。
## 2026-11-25 CPU 向量索引逾時修復工作範圍

- Codex 負責 embeddings.py、index_semantic.py、seed_tipo_e2e.py、對應測試、官方 E2E 工作與驗收文件。目標為讓離線建索引可指定較小批量及有上限的推論等待，並保留逐文件群組的交易一致性。

## M6 CPU 離線索引可設定批量與等待上限

- Date/time (timezone): 2026-11-25 12:58（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `28a8c0c`；本紀錄隨修復提交。
- Current milestone and status: M6 IN_PROGRESS（完整目標檔定義）；M0–M5 稽核估計 22/30，整體 Goal 尚未完成。
- Goal of this session: 承接稽核確認的遠端 CPU embedding 逾時，提供受限批量／等待設定與失敗一致性測試。
- Files changed (with purpose): `services/retrieval/embeddings.py` 傳遞離線等待；`index_semantic.py` 提供受限參數與 CLI；`scripts/seed_tipo_e2e.py` 傳遞設定；`.github/workflows/tipo-e2e.yml` 指定 2／180；`tests/test_embeddings.py`、`tests/test_semantic_index.py` 驗證傳輸、範圍與部分失敗；`docs/AUDIT-2026-11-25.md` 保存修復前唯讀稽核；PROGRESS、TESTING、本文件更新實際狀態。
- Database migrations added/applied: 無新增／變更。使用既有隔離 `patentscope_test`，head `0010_login_failures`；沒有修改真實研究資料。
- API/Schema changes: 無。線上預設等待 90 秒未變；模型 digest、pipeline、向量維度不變。
- Commands actually run and results:
  - 修復前 `pytest -q tests/test_semantic_index.py`：2 failed，尚不支援批量參數；修復後目標套件 6 passed，之後補參數及傳輸案例。
  - `pytest -q --basetemp <unique-temp>`：57 passed、3 skipped、1 既有 Starlette 警告。首次未指定暫存目錄為 48 passed、3 skipped、4 errors，原因 WinError 5，並非通過。
  - 設定隔離 PG 環境後 `pytest -q tests/integration --basetemp <unique-temp>`：3 passed，驗證 migration head、pgvector、API readiness、帳號／專案隔離與節流。
  - `ruff format --check .`：73 files already formatted；`ruff check .`：All checks passed。CLI `--batch-size 0` 在啟動模型前拒絕。
  - 隔離 `patentscope-cpu-index-proof`：2 CPU、4 GiB、DeviceRequests=null，使用唯讀既有模型卷；長 DEMO 兩段 21.45 秒；已核對官方原文兩段 2.01 秒，均 2 個 1024 維向量。這不是全量 CPU 索引或 GitHub runner 驗收。
- Tests NOT run and reason: 本修復尚未重跑 GitHub 官方 E2E，需推送修復分支後觸發。未重跑 Playwright／前端建置，本輪只改離線索引與設定；修復前稽核已有 37 項瀏覽器測試通過，完整結果見 AUDIT。未執行 1624 向量 CPU 全量重建／模型品質人工評估。
- Data sources checked (exact URL/date) and license/access notes: 本輪使用稽核重新取得的 `ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/2419202639611/113133932-A0304.xml`（2026-11-25 取得），核對 SHA-256 `0537aedd633f9c63e7fe06790732cb0bf06e240e0bebf360c725abf9bc98d70a`。未新增資料集或改變既有授權判斷。
- Known bugs / risks / blockers: 遠端官方工作 42837679581 已失敗，尚無修復後成功證據；CPU 小批量成功不可證明全量能在 90 分鐘完成。人工標註、持久 raw store／復原、DB 最小權限、高成本端點資源上限仍未完成。既有煙霧腳本與種子期別不符。見 AUDIT 詳細分類。
- Decisions made (ADR links): 無架構變更，不新增依賴；離線選項維持既有預設，官方 CI 明確選擇 CPU 設定。
- Uncommitted changes / file ownership warnings: 修復檔案由 Codex 單獨修改；本機 `main` 起點較 origin/main 超前 1 個既有文件提交，未重寫歷史。測試容器完成後停止，資料卷保留。
- Next 1–3 concrete actions: 1. 推送修復分支並觸發官方 E2E，按 runner 全量時間調整並記錄。2. 統一煙霧腳本語料契約、持久保存官方原始物件並驗證備份復原。3. 優先處理資源上限與 DB 最小權限，再由人員標註候選並執行品質評估。
- Exact reproduction steps: 見 [TESTING CPU 離線向量索引](TESTING.md#cpu-離線向量索引)。一般單元測試用唯一 `--basetemp`；PG 使用專用 `patentscope_test`、回環連線與 `PATENTSCOPE_PG_INTEGRATION=1`，切勿改成真實資料庫。

## 2026-11-25 關機前接續點

- 修復提交 `8cea2f1` 已推送至 `origin/fix/cpu-embedding-index`。目前未合併 main。
- 已手動觸發 [Official patent E2E 45550486217](https://github.com/Johnnnny0823/RAG/actions/runs/45550486217)，最後查核狀態 `in_progress`，不是通過；GitHub 雲端 runner 可在本機關機後繼續執行。下次先用 `gh run view 45550486217 --repo Johnnnny0823/RAG` 查詢，若失敗收集 `--log-failed`，不要未查狀態就重啟同一工作。
- 已開始調查原始檔持久保存：Compose 目前只有 PostgreSQL named volume；匯入與驗證要求明確 `--objects`，常用文件指向暫存快取。尚未修改保存機制，也未建立備份還原功能。
- 本機沒有新啟動的開發服務或新程式碼修改。下一步先確認遠端完整 CPU 索引與瀏覽器結果，再補持久 raw store 與實測備份／還原。整體 Goal 保持未完成。

## 原始 XML 保存工作範圍

- Codex 負責 Compose 的原始物件卷、匯入與驗證 CLI、校驗複製指令、測試及操作文件。

## 官方 E2E 結果與原始 XML 復原

- Date/time (timezone): 2026-11-25 20:51（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `d806ca9`，本節隨持久保存提交。
- Current milestone and status: M1 原始物件保存切片已實測，完整 Goal 的 M6 仍 IN_PROGRESS。
- Goal of this session: 驗收遠端 CPU 修復，並補足開發環境的 XML 備份還原。
- Files changed (with purpose): `docker-compose.yml` 配置遷移服務的物件卷。匯入與驗證 CLI 共用目錄設定。新增 `services/ingestion/sync_objects.py`，依資料庫校驗或複製原始物件。測試驗證損毀來源會保留已有備份。SETUP、PROGRESS、HANDOFF 記錄操作與結果。
- Database migrations added/applied: 無新增。在隔離專案套用到 `0010_login_failures`，以 `pg_dump -Fc`／`pg_restore --exit-on-error` 復原至第二套隔離資料庫。
- API/Schema changes: 無。實測復原後 readiness 與專利請求項端點。
- Commands actually run and results:
  - `gh run view 45550486217 --log`（對應工作 `138990245525`）：提交 `8cea2f1` 成功，CPU 117 個版本、1,624 個向量；Playwright 兩套分別 5／12 通過。
  - `pytest -q --basetemp <unique-temp>`：58 passed、3 skipped、1 則既有 Starlette 警告。Ruff 74 檔格式通過且 lint 通過。
  - `docker compose --env-file .env.example config --quiet` 通過。隔離專案匯入 19 筆書目、1 份全文。不同一次性容器讀回資料卷並核對 19 項請求項和 122 段。複製 2 份原始物件，復原 PostgreSQL 後再複製到第二個新資料卷，原文再校驗通過。復原後 API readiness 正常，公開號 `202639611` 回傳 19 項請求項。
- Tests NOT run and reason: 此提交未重跑完整官方 Playwright 或所有歷史語料的復原。本機使用第 024019 期前 20 筆及一份全文驗證備份流程，遠端 17 項屬上一項 CPU 修復的結果。三項預設停用的 PostgreSQL 套件本輪未另執行。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-25 從 `ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/index.xml` 及 `ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/2419202639611/113133932-A0304.xml` 重新下載，分別符合既有固定雜湊 `7befed78…`、`0537aedd…`。沿用 [DATA_SOURCES](DATA_SOURCES.md) 的既有來源紀錄。
- Known bugs / risks / blockers: 備份會在遇到首個遺失或損毀物件時退出，既有語料需用其成對的檔案和 DB 備份核對。最小權限、資源配額與人工品質評估仍待完成。
- Decisions made (ADR links): 沿用現有雜湊物件儲存。開發環境以 Compose 專案資料卷持久保存，顯式傳入 `--objects` 的呼叫保留自訂路徑。
- Uncommitted changes / file ownership warnings: 獨立測試專案停止，保留資料卷。無正式資料變更。
- Next 1–3 concrete actions: 統一舊冒煙測試所需的期別語料，補上資源配額及資料庫最小權限，準備人工標註與檢索量測。
- Exact reproduction steps: 見 [SETUP 原始 XML 備份操作](SETUP.md#原始-xml-持久保存備份及還原)，使用空白還原專案。

## 官方語料 API 驗收工作範圍

- Codex 負責三支既有 API 冒煙腳本、官方 E2E workflow 與驗收文件。保留雙期樣本的驗收，另接入可由 CI 重建的官方語料。

- Date/time (timezone): 2026-11-25（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `914f8ef`。
- Current milestone and status: M2 API 測試語料驗收，完整 Goal 仍 IN_PROGRESS。
- Goal of this session: 讓同一套官方 CI 種子可執行 API 及瀏覽器驗收，保留舊雙期語料的測試方式。
- Files changed (with purpose): `scripts/smoke_{patents,lexical,semantic}.py` 新增語料選項，`.github/workflows/tipo-e2e.yml` 在種子後執行三支腳本，更新 TESTING、PROGRESS、HANDOFF。
- Database migrations added/applied: 無。在既有隔離庫讀取 117 個版本。
- API/Schema changes: 無。
- Commands actually run and results: 三支腳本以 `--official-e2e --api http://127.0.0.1:18035` 均通過。詞彙 4 組、語意 2 組已知案均排第 1，API 同時驗證全文來源與版本、分頁及錯誤。修改前的舊腳本在該庫缺 024018 期而失敗。Ruff 格式 74 檔、lint 通過。
- Tests NOT run and reason: 沒有 API 或前端程式變更，未另跑單元套件、舊雙期樣本及 Playwright。新增 workflow 步驟待遠端驗收。
- Data sources checked (exact URL/date) and license/access notes: 沿用 2026-11-25 驗證的第 024019 期 FTPS 與封存公告；這輪未重新下載。精確 URL 及授權備註見 DATA_SOURCES。
- Known bugs / risks / blockers: 已知案排名只測固定小語料。人工相關性及正式檢索效能仍未驗收。
- Decisions made (ADR links): 舊腳本預設保留雙期前置條件；CI 明確選擇官方 E2E 語料。
- Uncommitted changes / file ownership warnings: 專用本機 API 及隔離資料庫於驗收後停止。
- Next 1–3 concrete actions: 查核新增的遠端 API 步驟，然後處理 DB 角色與高成本端點資源限額。
- Exact reproduction steps: 依 TESTING 的官方語料章節重建並執行三支腳本。

## 模型併發限制工作範圍

- Codex 負責模型呼叫的 API 共用限制、錯誤回應、相關設定及測試。範圍含直接搜尋、分析、重排、比對及研究工作台的相同操作。

- Date/time (timezone): 2026-11-25（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `073c076`。
- Current milestone and status: 完整目標 M6 安全性 IN_PROGRESS。
- Goal of this session: 限制線上推論的併發並提供可重試的 API 回應。
- Files changed (with purpose): `services/api/model_limits.py`、模型呼叫所在 API 路由、Compose、環境範例，及 `tests/test_model_limits.py`。API、SETUP、PROGRESS 與本文件更新。
- Database migrations added/applied: 無。
- API/Schema changes: `429 MODEL_BUSY`，含 `Retry-After: 5` 及禁止快取。預設每程序兩個推論名額。
- Commands actually run and results: 首輪 pytest 58 pass、3 skip、1 fail，指出缺少快取標頭。修正後啟用 `PATENTSCOPE_PG_INTEGRATION=1` 並指定隔離 PostgreSQL 與獨立 `--basetemp`，62 項全部通過，保留既有 Starlette 警告。Ruff 格式及 lint、`docker compose --env-file .env.example config --quiet` 通過。
- Tests NOT run and reason: 本輪未在本機重跑瀏覽器測試。上一提交的官方 [45618424111](https://github.com/Johnnnny0823/RAG/actions/runs/45618424111) 查核時執行中，並不涵蓋這次的併發修復。
- Data sources checked (exact URL/date) and license/access notes: 無新來源。
- Known bugs / risks / blockers: 限制以程序為單位，跨程序／逐使用者配額、直接模型端點隔離及 DB 最小權限仍待完成。離線索引不占 API 名額。
- Decisions made (ADR links): 採每程序非阻塞名額，沿用現有 FastAPI 錯誤格式，未新增基礎設施。
- Uncommitted changes / file ownership warnings: 隔離資料庫於測試後停止。
- Next 1–3 concrete actions: 確認遠端官方驗收，實作 API 與遷移帳號的資料庫權限分離，補足逐客戶與多程序的資源限制。
- Exact reproduction steps: `python -m pytest -q tests/test_model_limits.py`。含 DB 的重跑環境見 TESTING 的 PostgreSQL 與 API 整合章節。

## PostgreSQL 帳號分離工作範圍

- Codex 負責 API 資料庫角色、Compose 啟動流程、隔離整合測試、CI 及操作文件。所有測試使用獨立資料庫。

- Date/time (timezone): 2026-11-25（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `5bf5fa7`。
- Current milestone and status: 完整目標 M6 安全性 IN_PROGRESS。
- Goal of this session: 限制線上 API 的 PostgreSQL 權限。
- Files changed (with purpose): `services/api/provision_db_role.py` 設定專用登入與明確授權，Compose 與環境範例分離帳密，CI、整合測試與操作文件更新。
- Database migrations added/applied: 無新增。空白測試環境套用既有遷移到 `0010_login_failures`，接著建立角色。另實測對同一測試庫重跑配置。
- API/Schema changes: 無，資料庫執行角色改為 `patentscope_api`。
- Commands actually run and results: 隔離 Compose 新卷啟動成功。開啟 PostgreSQL 整合後 `pytest -q --basetemp <unique-temp>` 共 63 pass，既有 Starlette 警告 1 則。Ruff lint 與格式通過。專用 Playwright 設定的 Chromium 三種螢幕各 4 項，共 12 pass。初次透過 Windows npm 傳 `--output` 時參數被誤作過濾器，改用本機 Playwright CLI 後正常執行。重跑角色配置後，以管理帳號匯入已驗證官方 XML 並建立詞彙索引，透過受限 API 查到 `202639611` 及 19 項請求項。
- Tests NOT run and reason: 本修訂尚未跑完官方全文／向量瀏覽器 suite 或正式部署。前一提交的 [45618424111](https://github.com/Johnnnny0823/RAG/actions/runs/45618424111) 仍在建置語料。
- Data sources checked (exact URL/date) and license/access notes: 本輪沿用先前核對雜湊的 024019 期索引與個案原文，未重新下載。見 DATA_SOURCES。
- Known bugs / risks / blockers: 既有 `.env` 需補設定。API 角色提供跨研究資料的功能性權限，應用所有權檢查仍須維持。多程序及逐客戶配額尚未完成。
- Decisions made (ADR links): 權限清單置於角色配置程式，遷移及匯入保留管理帳號。資料庫還原後重跑角色配置以套用授權。
- Uncommitted changes / file ownership warnings: 專用測試容器停止，保留隔離資料卷。
- Next 1–3 concrete actions: 確認官方 CI 及當前分支回歸，補跨程序與逐客戶配額，進行人工檢索評估。
- Exact reproduction steps: 用 `docker-compose.test.yml` 啟動隔離環境，再依 TESTING 的 PostgreSQL 整合章節執行。Playwright 使用獨立 Web origin。

## 請求項原文援引工作範圍

- Codex 負責原文援引擷取、關聯遷移與匯入、請求項 API／畫面及驗收。維持來源標記與文本援引的不同語義。

- Date/time (timezone): 2026-11-25（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `433c02d`。
- Current milestone and status: M1／M3 請求項結構與定位的增量，完整 Goal IN_PROGRESS。
- Goal of this session: 保存同版本請求項正文的明確援引，並提供詳情頁跳轉。
- Files changed (with purpose): `0011_claim_dependencies.py` 建表與回填，`claim_references_v1.py` 解析，匯入與 API 讀權限更新，請求項 JSON 和詳情頁互動加欄位。新增解析測試及擴增官方 Playwright 案例。
- Database migrations added/applied: 空白隔離庫升至 `0011_claim_dependencies`；原有小語料庫從 `0010` 回填。以隔離 DB 降版確認原文仍有 19 項，再升版回填 128 筆。
- API/Schema changes: `GET /api/v1/patents/{document_id}/claims` 新增 `referenced_claim_numbers`。每個外鍵只允許目標在同一文件版本內，父項須先於子項。
- Commands actually run and results: pytest 啟用 PostgreSQL 整合後 65 passed、1 則既有 Starlette 警告。Ruff 格式及 lint、前端 lint 和 TypeScript 通過。固定官方全文的初次匯入與回填各得到 128 筆，API 第 2／3／4 項分別回傳 `[1]`、`[1,2]`、`[1,2,3]`。用隔離 PostgreSQL 實測拒絕自我援引與不存在的子項。
- Commands actually run and results（續）: 本機以隔離小語料 20 個版本、230 個向量與真實模型執行 `PATENTSCOPE_E2E_TIPO=1` 的 `desktop-chromium`，1 passed。新增援引跳轉斷言及既有引文、歷史、PDF 斷言均通過。
- Tests NOT run and reason: 本輪尚未以此提交重跑遠端全文、公告版本與全瀏覽器套件。本機 E2E 範圍限新增 UI 所在的官方文件案例。
- Data sources checked (exact URL/date) and license/access notes: 本輪重用已驗證的 `ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/2419202639611/113133932-A0304.xml`，固定 SHA-256 為 `0537aedd…`。來源 XML 第 2–4 項標為 `independent-claim`，正文仍有援引。
- Known bugs / risks / blockers: 規則只涵蓋已支援的明確正文形式，結果不等同法律上的依附性判定；未覆蓋含糊或其他語言的表述。
- Decisions made (ADR links): 獨立項來源標記保持原值。使用兩個指向同版本複合鍵的 FK，衍生關係可重建。
- Uncommitted changes / file ownership warnings: 隔離 Compose 服務驗收後停止，保留測試卷，沒有改動正式語料。
- Next 1–3 concrete actions: 以封存公告交叉驗證，繼續改進證據語義與完整工作流程。
- Exact reproduction steps: 用測試 Compose 匯入固定官方 XML 或對現有隔離庫升版，再查 `202639611` 請求項。依 TESTING 執行 `PATENTSCOPE_E2E_TIPO=1` 的官方流程。

## 比對證據的語意候選工作範圍

- Codex 負責比對候選檢索、API 及保存相容性、測試和技術文件。

- Date/time (timezone): 2026-11-25（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `a10678a`。
- Current milestone and status: M3 語意證據候選增量，完整 Goal IN_PROGRESS。
- Goal of this session: 對字詞未命中的特徵補充同版本語意證據，保留引用的精確可追溯性。
- Files changed (with purpose): `comparisons.py` 檢索及保存兼容欄位，`evidence.py` 驗證原文位置，`embeddings.py` 批量查詢向量，更新證據單元測試、官方 Playwright、舊字詞基準腳本及 API 文件。
- Database migrations added/applied: 無。沿用 `0011` 測試庫的 20 版本與 230 向量。
- API/Schema changes: 比對預設補語意候選，直接比較可傳 `semantic_evidence: false` 回到字詞行為。每特徵回傳 `evidence_method`，比對回傳 `evidence_embedding_digest`，舊保存結果欄位預設空值。
- Commands actually run and results: 啟用 PostgreSQL 整合執行 pytest 共 66 passed、1 則既有 Starlette 警告。Ruff 格式與 lint、前端 lint 與型別查核通過。使用真實模型，官方 `202639611` 對「Polymer composition curable by light above 500 nanometers」字詞結果無片段，語意結果回傳第 9 項 [0,53) 與模型判定 `supported`，用 GET claims 驗證原文逐字相符，查詢耗時 3.77 秒。Chromium 官方案例 1 passed，涵蓋新增語意引文與原有保存／歷史／PDF。
- Tests NOT run and reason: 尚未以新提交重跑遠端完整官方 suite，也未做人工作業以驗證語意判定品質。首次 Ruff 因測試 import 位置及空白未通過，整理後通過。
- Data sources checked (exact URL/date) and license/access notes: 沿用先前核對的官方 `202639611` XML（FTPS 來源與雜湊見上節）。未取得新資料。
- Known bugs / risks / blockers: 每特徵最多給模型一段原文，未做多段綜合。嵌入或分析判定可能出錯，尚無真人相關性覆核與大量語料效能驗收。
- Decisions made (ADR links): 原文字詞命中保有優先順序，語意候選只使用同模型、同文件版本及通過來源篩選的請求項或說明書。
- Uncommitted changes / file ownership warnings: 測試環境驗收後停止，保留資料卷。無正式資料變更。
- Next 1–3 concrete actions: 接續人工證據品質評估及多段候選驗證，補完整遠端瀏覽器回歸。
- Exact reproduction steps: 用 TESTING 的官方語料及模型設定執行桌面 `PATENTSCOPE_E2E_TIPO=1`；案例會比對純字詞與語意的可核對引文差異。

## 長篇發明構想工作範圍

- Codex 負責前端構想欄位、分析與搜尋需求驗證、查詢展開、測試及文件。

- Date/time (timezone): 2026-11-25（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `f8323e4`。
- Current milestone and status: M2／M3 長篇構想流程已實測，整體 Goal IN_PROGRESS。
- Goal of this session: 長描述可直接拆解、送入混合搜尋、保存並重開研究結果。
- Files changed (with purpose): 分析、混合搜尋 Schema，查詢展開、模型上下文、前端兩個構想欄位、pytest／Playwright 與文件。短篇專用詞彙及語意端點保留原上限。
- Database migrations added/applied: 無新增。使用既有隔離庫 `0011`、20 版本／230 向量。
- API/Schema changes: 混合搜尋、獨立分析、Session 共用 1,200 字元限制。混合回應與已保存設定加入 `query_expansion_version`。
- Commands actually run and results: 70 項 pytest 通過，含 PostgreSQL 整合及超限 422；Ruff、前端 lint、TypeScript 通過。第一次官方 Chromium 案例到達歷史重開，但仍以短句檢查畫面而失敗。改為核對完整長文，瀏覽器案例驗證真實模型、已保存查詢、引文和 PDF 中的各句。1,200 字真實模型實測最初回傳 `503 ANALYSIS_UNAVAILABLE`，完整輸出結構曾導致本機模型中斷連線，外層結構仍允許不符規則的巢狀 IPC 值。用 Ollama 可接受的欄位型別與陣列上限約束，並保留 Pydantic 驗證後，1,200 字的 Session 成功生成 1 項特徵、重讀的原文逐字相符，混合檢索命中 `202639611`。
- Tests NOT run and reason: 未於本輪重跑新版完整遠端官方與跨瀏覽器 suite；桌面使用本機模型及小語料。前一筆 `f8323e4` 的一般遠端 CI `45621413069` 通過。
- Data sources checked (exact URL/date) and license/access notes: 沿用既有官方封存第 024019 期，未重新下載。來源與授權見 DATA_SOURCES。
- Known bugs / risks / blockers: 長描述的相對檢索品質尚待人工評估；仍缺非同步搜尋、進度及取消。報告只證明已驗收樣本的呈現。
- Decisions made (ADR links): 長描述先按句段做詞彙查詢，語意檢索保留完整構想與確認的特徵描述。特徵詞另外參與詞彙查詢。
- Uncommitted changes / file ownership warnings: 本機測試專案驗收後停止，原服務及資料卷保留。
- Next 1–3 concrete actions: 驗收新版遠端官方流程，優先補任務狀態及人工相關性評估。
- Exact reproduction steps: 依 TESTING 的官方語料步驟啟動隔離環境並執行 `PATENTSCOPE_E2E_TIPO=1` 桌面 Chromium。

## 背景搜尋工作範圍

- Codex 負責工作表遷移、背景搜尋 API 與工作程序、研究介面、測試及文件。本輪在隔離資料庫驗收。

- Date/time (timezone): 2026-11-25（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `0949898`。
- Current milestone and status: M3／M4 背景搜尋與狀態，完整 Goal IN_PROGRESS。
- Goal of this session: 登入後可將混合搜尋排入背景、查看進度、取消，以及完成後取得一般研究快照。
- Files changed (with purpose): `0012_search_jobs.py` 遷移、工作 API 與工作程序、搜尋快照共用寫入、受限角色授權、Compose／CI、前端輪詢與取消、整合和 Playwright 驗收及對應文件。
- Database migrations added/applied: 在既有隔離資料庫與新空白隔離庫驗證 `0012_search_jobs`。活動工作按帳號限制一筆；取消或終止後清除暫存的構想。研究快照在成功交易中一次保存。
- API/Schema changes: `/api/v1/search-jobs` 增加 HTTP 202 接收、狀態、目前工作與取消。前端「搜尋並保存」走新流程，已保存搜尋讀取 API 維持原來的路徑。
- Commands actually run and results: 啟用 PostgreSQL 整合的 pytest 71 passed、1 則既有 Starlette 警告。Ruff、前端 lint 與 TypeScript 通過。測試使用真實資料庫與替身檢索，核對跨帳號 404、重複送出 409、工作完成保存，以及執行中取消不留快照。
- Commands actually run and results（續）: 隔離 Compose 啟動工作程序後，真實模型及官方 `202639611` 的 Chromium 桌面案例 1 passed。瀏覽器收到 202，輪詢成功後開啟已保存的快照，並完成引文、歷史與 PDF 驗收。
- Tests NOT run and reason: 這版尚無遠端官方及其他瀏覽器的結果。取消路徑由 PostgreSQL 整合測試執行，瀏覽器官方流程驗收成功保存。
- Data sources checked (exact URL/date) and license/access notes: 沿用已核對雜湊的第 024019 期與小語料索引，沒有新增來源。
- Known bugs / risks / blockers: 取消屬盡力取消，已送出的模型請求仍可能執行到回應或逾時。Worker 漏失的工作會由後續工作程序標為逾時，不自動重試。報告、向量索引及匯入的任務狀態尚未整合。
- Decisions made (ADR links): 使用 PostgreSQL 佇列與單獨 Compose 工作程序。匿名預覽仍使用現有同步搜尋；已登入保存流程使用背景工作。
- Uncommitted changes / file ownership warnings: 隔離工作程序、Web、API 與 DB 驗證後停止，保留測試卷。
- Next 1–3 concrete actions: 驗收遠端官方流程；補報告及匯入任務狀態；進行相關性評估。
- Exact reproduction steps: 在 worker 停止時跑 PostgreSQL 整合 pytest。以 `docker compose up -d --build search-worker` 啟動後，依 TESTING 執行官方 Playwright。

## 私人 PDF 背景匯出工作範圍

- Codex 負責 PDF 工作狀態、暫存及授權，整合既有資料庫工作程序、研究介面及端到端驗收。

- Date/time (timezone): 2026-11-25（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `f8b6f47`。
- Current milestone and status: M5 私人報告背景生成；完整 Goal IN_PROGRESS。
- Goal of this session: 讓 PDF 生成脫離 HTTP 請求，並維持授權與原文驗證。
- Files changed (with purpose): `0013_generated_reports.py`、`report_jobs.py` 提供工作與暫存；現有工作程序取件，PDF 共用原產生器與授權查詢。研究介面改為排隊、輪詢、下載；新增 PostgreSQL 測試，擴充官方 E2E。
- Database migrations added/applied: `0013_generated_reports`，已在空白與既有隔離庫驗證。報告與搜尋紀錄級聯刪除，下載有效期一小時。
- API/Schema changes: `/api/v1/search-runs/{run_id}/reports` 為 HTTP 202 入口，另有狀態與 PDF 端點；同步端點保留。
- Commands actually run and results: PostgreSQL 整合開啟後 pytest 72 passed、1 則既有 Starlette 警告。Ruff 格式與 lint、前端 lint 與 TypeScript 通過。隔離 DB 測試涵蓋重複送出、未完成回傳 409、跨帳號 404、PDF 欄位與禁止快取、過期遮蔽和級聯刪除。
- Commands actually run and results（續）: 真實官方資料的 Chromium 桌面案例 1 passed，驗證排入報告工作回傳 HTTP 202，工作完成後下載私人 PDF，核對繁中構想、原文引證、雜湊及官方連結。上一提交 `f8b6f47` 的一般遠端 CI [45624748266](https://github.com/Johnnnny0823/RAG/actions/runs/45624748266) 通過。
- Tests NOT run and reason: 本提交尚未完成遠端官方與其他瀏覽器套件；本機以小語料和桌面 Chromium 驗收報告流程。
- Data sources checked (exact URL/date) and license/access notes: 沿用早前已校驗的第 024019 期官方小語料，未下載新資料。
- Known bugs / risks / blockers: 報告和搜尋共用單工作程序，長搜尋可能推遲報告。尚未完成匯入與嵌入的任務管控、人工品質評估及正式部署。
- Decisions made (ADR links): 暫存 PDF 以 PostgreSQL 保存，每份上限 8 MiB。直接在來源搜尋紀錄上檢查所有權及刪除關係。
- Uncommitted changes / file ownership warnings: 專用 Compose 專案驗收後停止，測試資料卷保留。
- Next 1–3 concrete actions: 補匯入任務的管理及狀態；查核最新版遠端官方驗收；執行 RAG 人工評估。
- Exact reproduction steps: 依 TESTING 在 worker 停止時執行 PostgreSQL 整合測試；啟動 worker 後執行 `PATENTSCOPE_E2E_TIPO=1` 的官方案例。

## 官方匯入與索引監控工作範圍

- Codex 負責既有匯入／索引的操作員背景指令、狀態紀錄、管理員唯讀 API 與工作台查詢。

- Date/time (timezone): 2026-11-25（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `5db035c`。
- Current milestone and status: M1／M5 官方匯入及索引狀態，完整 Goal IN_PROGRESS。
- Goal of this session: 以既有官方流程執行可追蹤的背景匯入，並供授權帳號查看。
- Files changed (with purpose): 遷移 `0014_ingestion_jobs`、`run_pipeline.py`、唯讀管理路由、帳號授權能力標記、Compose 環境設定、研究工作台及 PostgreSQL 測試。
- Database migrations added/applied: `0014_ingestion_jobs` 已在既有與空白隔離庫成功套用。API 角色可讀工作紀錄，實測不可更新。
- API/Schema changes: `GET /api/v1/admin/ingestion/jobs`，及 `GET /api/v1/me` 新增 `can_monitor_ingestion`。以 UUID 白名單授權。
- Commands actually run and results: PostgreSQL 整合啟用後 pytest 73 passed、1 則既有 Starlette 警告，Ruff 格式與 lint、前端 lint、TypeScript 皆通過。隔離空白庫實際用 detached Docker job 匯入 1 份固定官方全文、建 145 個詞彙片段與 157 個向量，容器退出 0，狀態為 `succeeded`。另一隔離庫重跑既有批次為 `partial`；不存在的輸入退出 1 並標記 `failed`。以真實 Chromium 登入隔離版管理帳號並核對兩種狀態。測試帳號於完成後刪除。
- Tests NOT run and reason: 未重跑完整遠端官方瀏覽器套件。此輪本機 Chromium 驗收範圍為管理頁，既有瀏覽器主要研究流程的紀錄見前節。
- Data sources checked (exact URL/date) and license/access notes: 沿用 2026-11-25 核對的官方 `ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/index.xml` 及 `ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/2419202639611/113133932-A0304.xml`，未重新下載。
- Known bugs / risks / blockers: 監控按階段更新，沒有逐向量進度。背景容器異常終止後由下一次受監控操作標記舊工作中斷。尚缺自動排程與人工相關性評估。
- Decisions made (ADR links): 管理介面唯讀，匯入由操作員在部署環境啟動，沿用官方來源與既有入庫程序。
- Uncommitted changes / file ownership warnings: 測試專案停止，保留隔離資料卷及已結束的驗收容器紀錄。
- Next 1–3 concrete actions: 查核遠端官方流程，完成評估基準與人工標註，補作較大規模規劃分析。
- Exact reproduction steps: 依 SETUP 官方匯入監控段落設定輸入與管理者 UUID，執行 detached 流程後以管理帳號查看。

## PostgreSQL 檢索計畫驗收範圍

- Codex 負責檢索 SQL 的重現指令、隔離語料量測、測試與效能證據文件。

- Date/time (timezone): 2026-11-26 01:51（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `fbe109e`。
- Current milestone and status: M2／M6 PostgreSQL 小語料基線完成，完整 Goal IN_PROGRESS。
- Goal of this session: 量測真實 SQL，避免精確 IPC 案例仍掃描全部向量。
- Files changed (with purpose): `patents.py` 新增精確 IPC 的候選向量查詢，`scripts/explain_search.py` 以生產 SQL 重現量測，`test_explain_search.py` 驗證計畫只輸出所需欄位，更新評估、資料庫與交接文件。
- Database migrations added/applied: 無新增。將已核對的公開資料備份還原至新建隔離庫，從空白遷移到 `0014`，對隔離語料執行 `ANALYZE`。
- API/Schema changes: 無。精確 IPC 向量分支改用先篩文件的查詢；無 IPC 或四碼子類使用原查詢。兩個精確 IPC 案例的結果、順序及分數逐筆一致。
- Commands actually run and results: PostgreSQL 整合開啟後 pytest 74 passed、1 則既有 Starlette 警告。Ruff 格式及 lint 通過。隔離真實 API 的三支 `--official-e2e` 冒煙通過。117 版本／1,560 詞彙片段／1,624 向量，用唯讀快照及 7 次量測比對兩個精確 IPC 案例。完整本機輸出在 `%TEMP%/patentscope-sql-plans-520c713b-a4ea-43dd-a28a-fa04c1d6fd46.json`，數字見 EVALUATION。
- Tests NOT run and reason: 本機未重跑全瀏覽器套件，此輪沒有前端修改。更早提交 `073c076` 的遠端官方 E2E 45618424111 通過，含三支冒煙及 17 項 Playwright。本次變更另需自己的遠端結果。
- Data sources checked (exact URL/date) and license/access notes: 沿用已驗證的 TIPO 第 024019／053028 期封存檔形成的公開資料備份，未重新下載。來源及授權見 DATA_SOURCES。
- Known bugs / risks / blockers: 小語料、預熱查詢、未加併發負載。未量測大規模資料及向量索引的速度／召回取捨。人工相關性標註仍待完成。
- Decisions made (ADR links): 目前保留精確向量排序，不加入近似索引。候選查詢優化限精確 IPC，保留較寬查詢的行為。
- Uncommitted changes / file ownership warnings: 隔離 API 與 DB 停止，保留測試卷。
- Next 1–3 concrete actions: 核對新版官方工作；準備人工標註並量測代表性負載；檢查尚未完成的產品與部署驗收。
- Exact reproduction steps: 依 [EVALUATION SQL 計畫](EVALUATION.md#2026-11-26-postgresql-查詢計畫基線) 執行。

## 搜尋涵蓋範圍工作範圍

- Codex 負責混合搜尋索引涵蓋範圍、既有快照設定、研究介面、PDF、測試及對應文件。
- Codex 同步處理官方 E2E 的 TIPO FTPS 暫時性 425 錯誤，範圍限既有下載器及測試。

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `4154d66`。
- Current milestone and status: M4／M5 搜尋涵蓋範圍通過本機官方案例，M6 官方遠端驗收 IN_PROGRESS。
- Goal of this session: 讓使用者在當次搜尋、歷史及 PDF 查到相同的索引涵蓋範圍，處理官方 CI 下載暫時失敗。
- Files changed (with purpose): `patents.py` 同快照計數，`reports.py` 與 `research.tsx` 顯示範圍，`tipo-research.spec.ts` 跨 API、畫面及 PDF 核對；`download.py` 和 `test_download.py` 覆蓋 425 重試、耗盡及非暫時故障。
- Database migrations added/applied: 無新增遷移。重用 `0014` 的隔離資料庫。舊公開資料備份未含 `claim_dependencies`，用既有遷移的解析方式從真實原文補建 334 筆後重跑瀏覽器驗收。未改動日常資料庫。
- API/Schema changes: 混合 API 增 `corpus_coverage`，保存於既有 `settings` JSONB。舊紀錄缺欄位時明示未記錄。觀察時間、詞彙及向量版本數及最新文件日期於排名相同讀取交易取得。
- Commands actually run and results: 含 PostgreSQL 的 pytest 78 通過、1 則既有 Starlette 警告。Ruff、前端 lint、TypeScript、Vite build 通過。隔離官方語料三支 API 冒煙通過。桌面 Chromium 官方全文、歷史與 PDF 案例 1 通過（48.6 秒）。首次廣域測試遇到模型分析等待，切回文件指定 1.5B 模型後，先後遇到並行註冊逾時與隔離備份缺依附資料。單獨執行並補回依附資料後通過。
- Tests NOT run and reason: 本機未執行完整多瀏覽器官方套件。前一提交的一般 CI [45669424746](https://github.com/Johnnnny0823/RAG/actions/runs/45669424746) 通過。相同提交的官方工作 [45669425487](https://github.com/Johnnnny0823/RAG/actions/runs/45669425487) 因伺服器回覆 `425 Unable to listen, too many pending PASV/EPSV requests` 中止，三支 API 冒煙及 Playwright 均未開始。
- Data sources checked (exact URL/date) and license/access notes: 本機 E2E 使用固定官方第 024019、053028 期還原語料。2026-11-26 另以新版下載器實際下載 `ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/index.xml`，15,253,438 bytes，SHA-256 `7befed78be2cc6067266f13afd4a34f6feca4730b9a717f3f99890d551da9b69`。實際下載成功，425 復原與耗盡以測試替身分別驗證。授權與來源條件見 DATA_SOURCES。
- Known bugs / risks / blockers: 117 個驗收版本的日期欄全部空白。大語料的計數負載、完整索引重建及人工評估仍待完成。425 重試耗盡時應保留失敗狀態。
- Decisions made (ADR links): 索引計數按本次篩選及實際模型／分詞版本保存。FTPS 僅對已觀察的 425 等待 15、45 秒後重開資料傳輸。
- Uncommitted changes / file ownership warnings: 隔離容器的資料卷保留，供後續驗收。
- Next 1–3 concrete actions: 確認新版官方 CI 通過三個 API 冒煙與瀏覽器；查證可追溯的官方文件日期；完成人工相關性複核及較大語料效能驗收。
- Exact reproduction steps: 依 TESTING 啟動隔離官方語料與 worker，設定 `PATENTSCOPE_E2E_TIPO=1` 後執行桌面 Chromium 官方案例。使用 `python -m pytest tests/test_download.py` 重現 425 測試。

## 官方公報日期工作範圍

- Codex 負責公報書目原檔的日期、識別碼與卷期核對，以及隔離語料的寫入和 API 驗收。

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `658447d`。
- Current milestone and status: M1／M4 日期補齊已通過官方樣本驗收，整體 Goal IN_PROGRESS。
- Goal of this session: 從同卷期官方書目補正申請日和文件日期，讓既有日期篩選可用。
- Files changed (with purpose): `gazette_dates.py` 負責比對與寫入，`download.py`、`artifacts.py` 提供有上限的公報下載及物件保存，`verify_document.py` 仍選原請求項來源。研究詳情同時提供原始檔與資料集連結，新增日期 Playwright 案例。
- Database migrations added/applied: 無新增。公開、公告兩次各寫入後再重跑，保留 117 個文件版本、2 個新增原始檔及 117 筆新增來源連結。資料僅寫入 `patentscope_plan_proof`。
- API/Schema changes: 路徑及欄位維持原契約，既有詳情、候選及索引涵蓋範圍能讀到已補齊的日期。既有私有搜尋紀錄保留原本結果。
- Commands actually run and results: PostgreSQL 整合啟用後 pytest 84 passed、1 則既有 Starlette 警告。Ruff lint 與格式、前端 lint 及 TypeScript 通過。官方公開案 19 項、公告案 13 項請求項仍引用各自原檔。官方 API 精確查詢、來源雜湊與日期包含／排除驗收通過。桌面、平板、手機 Chromium 日期案例 3 passed。首輪案例指出 UI 僅顯示 FTPS 原檔，補上可從瀏覽器開啟的官方目錄連結後同套件通過。
- Tests NOT run and reason: 此次未重跑本機全官方套件。上一提交一般 CI [45671574773](https://github.com/Johnnnny0823/RAG/actions/runs/45671574773) 通過，上一提交官方流程 [45671575813](https://github.com/Johnnnny0823/RAG/actions/runs/45671575813) 截至本輪驗收仍在準備種子語料。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 實際下載公開第 024019 期及公告第 053028 期公報，核對位元組、SHA-256、卷期及日期，見 DATA_SOURCES。公開期另透過正式 CLI 重新下載與重跑。
- Known bugs / risks / blockers: 日期補齊目前由操作員按卷期獨立執行，未接入自動排程。覆蓋限已匯入且可核對的同卷期發明案件。大型公報超過 32 MiB 時會拒絕。代表性負載、完整語料快照及人工評估仍待完成。
- Decisions made (ADR links): 日期只填既有版本的缺值或確認相同值，原文、引用與舊搜尋紀錄仍可追溯。書目日期與請求項原文分別保留來源。
- Uncommitted changes / file ownership warnings: 隔離測試的資料卷與原始檔保留，日常專案資料未動。
- Next 1–3 concrete actions: 追蹤遠端官方驗收，擴充評估用的代表性官方語料與人工標註，量測檢索品質及負載。
- Exact reproduction steps: 依 SETUP 的 `services.ingestion.gazette_dates` 兩條命令補齊隔離資料，再以 `PATENTSCOPE_E2E_TIPO=dates` 執行 Playwright。

## 官方檢索評估工作範圍

- Codex 負責評估器、固定版本的待複核候選、測試及評估文件。

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `70dd57a`。
- Current milestone and status: M2／M6 官方種子重驗通過，人工相關性驗收 IN_PROGRESS。
- Goal of this session: 用可重建的官方語料重跑評估並保留可獨立複核的文件版本。
- Files changed (with purpose): `evaluate_search.py` 按文件號取最完整版本，人工標註集用雜湊及解析版本預檢；`test_evaluate_search.py` 核對版本漂移及未複核拒評；`tipo_official_117_review.json` 為 34 組待複核候選。
- Database migrations added/applied: 無新增。沿用唯讀隔離官方語料驗證。
- API/Schema changes: 無。人工複核資料格式要求 `content_scope`、`document_sha256`、`parser_version`。
- Commands actually run and results: PostgreSQL 整合啟用後 pytest 86 passed、1 則既有 Starlette 警告，Ruff 格式與 lint 通過。四案三模式各兩次共 24 個檢索請求，均找回五項已知文件。34 組候選用 API 重驗指紋，不依資料庫 UUID。引用腳本 7 次比對、14 個判定、6 個引文均逐字驗證成功。細項 JSON 在本機 `%TEMP%/patentscope-official-117-evaluation-20261126.json` 及 `%TEMP%/patentscope-official-117-citations-20261126.json`。
- Tests NOT run and reason: 純評估工具變更，本機未重跑瀏覽器。前一提交一般 CI [45674020726](https://github.com/Johnnnny0823/RAG/actions/runs/45674020726) 通過。前版遠端官方流程 [45671575813](https://github.com/Johnnnny0823/RAG/actions/runs/45671575813) 查核時仍在準備種子語料。
- Data sources checked (exact URL/date) and license/access notes: 沿用 DATA_SOURCES 的 TIPO 第 024019、053028 期，未重新下載。
- Known bugs / risks / blockers: 尚無人工標註，現有分數是種子已知命中基線。書目摘要 19 組，技術相關性可能需另外取得全文。大語料與正式負載仍待驗證。
- Decisions made (ADR links): 依文件階段與編號計排行；人工複核綁定可重建的文件內容。待複核資料不產生分數。
- Uncommitted changes / file ownership warnings: 隔離語料資料卷留供複驗。
- Next 1–3 concrete actions: 人工評估 34 組候選並重跑指標，擴充資料規模與主題，查核官方遠端工作。
- Exact reproduction steps: 依 EVALUATION 執行 `evaluate_search.py --repeats 2 --review-pool <新檔名>` 及 `evaluate_citations.py`，API 指向隔離官方語料。
