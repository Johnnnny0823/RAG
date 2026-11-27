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

## 官方驗收的固定語料重建

- Codex 負責固定語料準備、官方工作流程、相關測試及驗收文件。

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `cba5cde`。
- Current milestone and status: M6 分段重建通過本機官方語料驗收，遠端快取 IN_PROGRESS。
- Goal of this session: 拆開 FTPS 準備、PostgreSQL 匯入和索引階段，讓故障能由步驟與檔案進度定位。
- Files changed (with purpose): `tipo-e2e.yml` 加公開 XML 快取與分段工作，`seed_tipo_e2e.py` 加兩個執行選項及逐檔進度，`test_tipo_e2e_seed.py` 檢查純準備與離線匯入的執行範圍。
- Database migrations added/applied: 無新增。空白隔離庫 `patentscope_ci_replay` 套用至 `0014_ingestion_jobs`。
- API/Schema changes: 無。
- Commands actually run and results: PostgreSQL 整合啟用後 pytest 88 passed、1 則既有 Starlette 警告，Ruff 格式、lint、Git diff 檢查通過。第一次直接跑單檔測試遇 Windows 既有共用暫存目錄權限錯誤，以新 `--basetemp` 跑全套通過。正式 CLI 的準備及離線匯入各核對 24 筆 SHA-256，空白庫完成三批匯入、三項原文校對及獨立建索引。查得 117 版本、1,677 筆詞彙索引（含 117 個標記）、1,624 向量及 334 筆請求項援引。三支官方 API 冒煙通過。
- Commands actually run and results（續）: 同一空白重建語料的官方桌面 Chromium 案例 1 passed（58.3 秒），包含研究保存、引文、歷史重讀及 PDF。
- Tests NOT run and reason: 本機未執行完整多瀏覽器套件，向量索引用 24 筆批量，GitHub CPU 流程維持 2 筆。前一提交一般 CI [45675094328](https://github.com/Johnnnny0823/RAG/actions/runs/45675094328) 通過。既有官方工作 [45671575813](https://github.com/Johnnnny0823/RAG/actions/runs/45671575813) 截至本輪仍在原種子步驟，該步驟涵蓋下載、匯入及索引。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 從 DATA_SOURCES 所列固定 FTPS 路徑取得 22 個原檔，另重用已驗證的同批索引與一份個案檔。原始檔從臨時目錄保存，未提交 Git。
- Known bugs / risks / blockers: 冷快取仍依賴官方 FTPS。遠端快取寫入及後續命中需 GitHub 實跑。全量專利覆蓋及人工標註仍待完成。
- Decisions made (ADR links): 快取只保存公開 XML 與公開下載檔，儲存前與匯入前均校驗固定雜湊。GitHub Actions 快取動作鎖定至已核對的 v5 提交。
- Uncommitted changes / file ownership warnings: 資料卷及臨時公開原檔保留供重現。
- Next 1–3 concrete actions: 驗收新版遠端分段和快取，擴充代表性資料與人工評估，補上測試報告證據。
- Exact reproduction steps: 依 TESTING 先跑 `--prepare-only`，對空白已遷移隔離庫跑 `--offline --skip-semantic`，另執行 `services.retrieval.index_semantic`、官方 API 冒煙及 Playwright。

## 官方語料規模與併發量測

- Codex 負責隔離語料擴充、檢索量測、測試及評估紀錄。

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `fb427f2`。
- Current milestone and status: M2／M6 518 版本負載已量測，完整目標 IN_PROGRESS。
- Goal of this session: 以較多官方書目比較實際 SQL，量測小型本機服務在併發下的有效產出及忙碌回覆。
- Files changed (with purpose): `benchmark_search_load.py` 提供迴圈式併發及有來源的已知案核對；`test_benchmark_search_load.py` 檢查延遲與拒絕各自計數；`smoke_patents.py` 加擴充語料的版本斷言，原固定語料仍採原先預期。
- Database migrations added/applied: 無新增。以既有隔離庫 `patentscope_ci_replay` 增量重建至 518 版本、3,006 詞彙片段、3,164 向量。從官方原 XML 第 401 筆核對 API 公開案 `202640836` 的申請號、文件雜湊、來源及 XPath。
- API/Schema changes: 無。
- Commands actually run and results: pytest 含 PostgreSQL 整合 90 passed、1 則既有 Starlette 警告。Ruff 格式、lint、Git diff 檢查通過。擴充庫三支官方 API 冒煙通過。初次直接套用 117 版本冒煙時，`202639611` 因多一個合法書目版本觸發解包失敗。以明確的擴充語料模式驗證兩個版本後通過。
- Commands actually run and results（續）: SQL 兩組精確 IPC 的候選、順序和分數逐筆與原 SQL 一致。180 個 HTTP 查詢中，150 個成功且均命中已知案，30 個回覆 `429 MODEL_BUSY`。各組成功延遲與吞吐在 EVALUATION。
- Tests NOT run and reason: 本輪僅評估及驗收工具修改，未重跑 Playwright。一般 CI [45677084566](https://github.com/Johnnnny0823/RAG/actions/runs/45677084566) 通過。新版官方流程 [45677086302](https://github.com/Johnnnny0823/RAG/actions/runs/45677086302) 已通過固定 XML 驗證與快取寫入，尚在執行其他步驟。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 沿用已驗證的 `ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/index.xml`，未重新下載。來源授權見 DATA_SOURCES。
- Known bugs / risks / blockers: 語料增加的是書目摘要版本，無法外推完整語料、重排序或多程序生產負載。人工標註與快取命中仍待查核。
- Decisions made (ADR links): 以已知案命中驗證每筆正常回覆，忙碌回覆單列，成功延遲不計入快速拒絕。
- Uncommitted changes / file ownership warnings: 隔離資料卷及原始 JSON 保留。量測檔為 `%TEMP%/patentscope-load-117-*.json`、`patentscope-load-518-*.json`、`patentscope-concurrency-final-518-*.json`。
- Next 1–3 concrete actions: 核對官方遠端流程與後續快取命中，對更多資料來源及全文做規模分析，完成候選人工複核。
- Exact reproduction steps: 依 EVALUATION 擴充官方樣本，執行 `explain_search`、`benchmark_search_load` 及 `--expanded-corpus` API 冒煙。

## 官方異動公報工作範圍

- Codex 負責已核對的公報事件解析、來源關聯、詳情呈現及隔離驗收。

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `e0041d9`。
- Current milestone and status: M1／M4 已核對的公報事件通過隔離驗收，完整 Goal IN_PROGRESS。
- Goal of this session: 將可追溯的異動公報事件呈現在其同一申請案的專利詳情。
- Files changed (with purpose): 新增 `0015_legal_events.py`、`legal_events.py`、解析與 Playwright 測試。既有下載器只新增兩種固定路徑，API 與前端顯示公報來源。
- Database migrations added/applied: 新增 `0015_legal_events`，在已有 518 個官方文件版本的隔離資料庫與空白隔離資料庫套用成功。受限 API 角色有讀權限而無更新權限。
- API/Schema changes: `GET /api/v1/patents/{document_id}` 回傳 `legal_events`，含類別、證書號、官方可取得生效日與原檔定位。公告版本再比對證書號。
- Commands actually run and results: Pytest 含 PostgreSQL 整合 93 passed、1 則既有 Starlette 警告。Ruff、前端 lint、TypeScript 和 Vite build 通過。實際下載兩種 XML 後透過 CLI 匯入，31 筆發明更正中 2 筆配對，新跑同一期新增 0 筆；838 筆消滅公告與目前隔離的案件無交集。API 核對兩筆更正與一筆空清單。桌面、平板、手機 Chromium 三項來源定位案例通過。第一次測試有選擇器語法錯誤，改用核對完整官方 URL，重跑後通過。
- Tests NOT run and reason: 本機未執行完整多瀏覽器套件。目前無同時具消滅公告與匹配專利的驗收樣本，因此消滅日期以官方原檔與解析測試驗證，未宣稱完成對應的瀏覽器流程。一般 CI [45678252779](https://github.com/Johnnnny0823/RAG/actions/runs/45678252779) 在前提交通過，較早官方遠端流程仍在建立向量索引。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 核對 TIPO 第 53 卷第 33 期 `sud08.xml`、`sud24.xml` 及 P10 最新索引、30126 API 目錄。固定路徑、SHA-256、目錄授權及限制見 DATA_SOURCES。
- Known bugs / risks / blockers: 歷史事件僅涵蓋已匯入期別、發明類別與兩種已核對的公告結構。任意案件的最新法律狀態與完整歷程未驗證。
- Decisions made (ADR links): 公報更正不推估日期，只呈現官方提供的卷期及更正欄位。消滅公告保留來源的消滅日及原因。原檔 XML 不直接渲染。
- Uncommitted changes / file ownership warnings: 測試只使用獨立資料庫與公開原檔，資料卷保留。
- Next 1–3 concrete actions: 找到可與消滅公報交叉驗證的既有案例，繼續追查官方遠端驗收，完成人工相關性複核。
- Exact reproduction steps: 依 SETUP 建立擴充官方語料，執行 `legal_events` 的兩種固定卷期匯入，再以 `PATENTSCOPE_E2E_TIPO=events` 跑 Playwright。

## 消滅公告端到端驗收工作範圍

- Codex 負責官方公告原檔交叉核對、公告索引匯入大小限制與瀏覽器驗收。

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `5da633d`。
- Current milestone and status: M1／M4 消滅公告端到端驗收通過，完整 Goal IN_PROGRESS。
- Goal of this session: 用兩份官方原檔確認同一證書的公告、請求項及消滅事件，並通過瀏覽器驗收。
- Files changed (with purpose): 公告下載、讀取與解析的大小上限調整；詳情顯示公報記載消滅日；新增資料上限回歸測試及官方消滅案 E2E。
- Database migrations added/applied: 無新增。隔離現存 `0015_legal_events` 資料庫匯入公告案 1 版本，補建 10 個詞彙片段及 10 個向量。
- API/Schema changes: 無。既有 `legal_events` 回覆可顯示此次驗收的有日期事件。
- Commands actually run and results: 用匿名 FTPS 下載第 52 卷第 6 期公告索引，驗證 1,780 筆、大小與雜湊。CLI 匯入 `I874215` 後 `verify_document` 逐項核對 9 項請求項。重跑第 53 卷第 33 期消滅事件匯入，第一次新增 1 筆，第二次新增 0 筆。API 驗證此案消滅日 2026-02-21、原檔雜湊、XPath 和其他案件無交叉關聯。
- Commands actually run and results（續）: PostgreSQL 整合啟用後 pytest 96 passed、1 則既有 Starlette 警告。Ruff、前端 lint、TypeScript 和 Vite build 通過。桌面、平板、手機 Chromium 的官方更正與消滅案例 6 passed（37.5 秒）。一次重驗時 Docker Desktop 尚未啟動，啟動後重跑完成。
- Tests NOT run and reason: 本機未跑完整跨瀏覽器官方套件。遠端 [45677086302](https://github.com/Johnnnny0823/RAG/actions/runs/45677086302) 在 `fb427f2` 通過三項 API 冒煙、5 項全文與 12 項版本 Playwright。前一提交的一般 [CI](https://github.com/Johnnnny0823/RAG/actions/runs/45679858852) 通過。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 核對公告原檔 `ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/114/PatentIsuRegSpecXMLA_052006/index.xml`、消滅原檔 `ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053033/sud08.xml`，雜湊及授權見 DATA_SOURCES。
- Known bugs / risks / blockers: 事件限使用所匯入的官方公報，任意案件的最新狀態查詢與全歷程尚未驗證。
- Decisions made (ADR links): 對已核對格式的官方公告卷期索引沿用 32 MiB 有界限制，個案說明書、其他非公報 XML 維持 16 MiB。
- Uncommitted changes / file ownership warnings: 原始檔與測試資料卷保留於隔離環境。
- Next 1–3 concrete actions: 核對遠端快取命中並複驗最新提交，補人工相關性判定與正式部署驗收。
- Exact reproduction steps: 依 SETUP 的官方異動公報段落匯入固定證書，再以 `PATENTSCOPE_E2E_TIPO=events` 啟動異動公報測試套件。

## 研究頁專利號碼查詢

- Codex 負責研究頁號碼查詢、官方資料瀏覽器驗收與文件。

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `12d9daf`。
- Current milestone and status: M4 研究頁號碼查詢驗收通過，完整 Goal IN_PROGRESS。
- Goal of this session: 讓已知申請號、公開號或公告號的使用者直接開啟正確版本的詳情。
- Files changed (with purpose): `research.tsx` 新增號碼查詢、結果及分頁。沿用共同專利詳情。新增 `patent-number.spec.ts` 並更新 README、驗收、進度與交接。
- Database migrations added/applied: 無新增。查詢使用已匯入官方語料的隔離資料庫。
- API/Schema changes: 無。沿用 `GET /api/v1/patents` 的號碼類型、標準化與分頁契約。
- Commands actually run and results: `npm run lint --prefix apps/web`、`npm run build --prefix apps/web` 通過。官方號碼查詢桌面、平板、手機 Chromium 3 passed（16.7 秒），核對同案三版本、公告 13 項請求項、全形公開號、小寫公告號、空結果與錯誤。桌面搜尋錯誤與研究工作台回歸 4 passed（15.8 秒）。API 未設定嵌入與分析模型。
- Tests NOT run and reason: 本輪前端功能未改 API 實作或資料庫，未重跑 pytest。尚未對超過單頁版本的官方案例執行號碼查詢分頁。前一提交的遠端官方工作 [45737654914](https://github.com/Johnnnny0823/RAG/actions/runs/45737654914) 已精確命中公開快取並重新驗證 24 檔，其他步驟仍在執行。
- Data sources checked (exact URL/date) and license/access notes: 沿用 DATA_SOURCES 已核對的第 024019 與 053028 期，未下載新資料。
- Known bugs / risks / blockers: 自然語言檢索仍需模型，實際檢索品質待人工複核。正式部署驗收及最新法律狀態查詢待補。
- Decisions made (ADR links): 號碼查詢的分頁由既有 API 處理，點選同一文件版本時使用共用詳情。
- Uncommitted changes / file ownership warnings: 使用隔離本機服務與測試帳號，資料卷保留。
- Next 1–3 concrete actions: 查核最新官方案例與遠端驗收，完成人工相關性評估及部署驗收。
- Exact reproduction steps: 依 TESTING 啟動官方隔離語料，令 `PATENTSCOPE_E2E_TIPO=versions` 並以 `--grep=official.identifier.lookup` 執行。

## 靜態部署驗收

- Codex 負責 Nginx 部署安全標頭、冒煙驗收及重建官方語料的研究流程測試。

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `ef3c6fa`。
- Current milestone and status: 正式建置的本機部署與核心研究流程驗收通過，完整 Goal IN_PROGRESS。
- Goal of this session: 在全新隔離資料庫、Nginx 同源代理與背景工作程序上驗證官方語料的研究流程，讓遠端官方套件使用相同部署配置。
- Files changed (with purpose): `apps/web/nginx.conf` 強制執行同源內容安全政策，`scripts/smoke.py` 加入正式頁面及標頭檢查，`.github/workflows/tipo-e2e.yml` 改用正式部署覆蓋檔及同源連接埠，並更新 SETUP、TESTING、PROGRESS 及交接文件。
- Database migrations added/applied: 無新增，空白隔離資料庫遷移至 `0015_legal_events`。匯入 117 筆官方文件版本，建立 1,624 筆已驗證模型版本的向量。
- API/Schema changes: 無。API、資料庫及工作程序維持在容器網路內，對外測試只透過 Nginx 的本機連接埠。
- Commands actually run and results: 獨立 Compose 專案 `patentscope-release-check` 正式映像建置及啟動通過，部署冒煙與專利號碼、詞彙及語意 API 三項冒煙通過。Chromium 實際封鎖同源 iframe，通過官方全文與證據、儲存紀錄及私有 PDF 輸出一項流程。Firefox、WebKit 各通過一項官方號碼查詢。重啟 API 與工作程序後，部署及專利 API 冒煙再次通過，資料庫仍有 117 筆版本、1,624 筆向量，測試帳號已清理。Ruff 與 `git diff --check` 通過。
- Tests NOT run and reason: 本地未完整跑全部瀏覽器套件，本次變更範圍是代理、部署冒煙及工作流程，未重跑後端 pytest。舊版 [45669425487](https://github.com/Johnnnny0823/RAG/actions/runs/45669425487) 因 TIPO FTPS 425 未進入測試，後續 [45677086302](https://github.com/Johnnnny0823/RAG/actions/runs/45677086302) 使用已核對的官方樣本通過 API 與 Playwright。採用正式覆蓋檔的遠端結果需獨立核對。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 重驗 DATA_SOURCES 所載第 024019、053028 期共 24 個固定官方原檔的 SHA-256，使用先前匿名 FTPS 取得的快取。
- Known bugs / risks / blockers: 外部主機與 TLS、人工相關性標註、官方法律事件的完整覆蓋尚待驗收。快取失效後仍可能受到官方 FTPS 暫時限制。
- Decisions made (ADR links): 保留既有 Compose 架構，由正式 Nginx 入口提供同源 API，並沿用已固定雜湊的官方樣本。
- Uncommitted changes / file ownership warnings: 隔離資料卷保留供重驗，測試未接觸既有開發資料庫。
- Next 1–3 concrete actions: 複驗正式覆蓋檔的 GitHub Actions、完成人工相關性複核、取得外部部署環境後驗證 TLS。
- Exact reproduction steps: 依 SETUP 的靜態部署段落啟動 Compose，依 TESTING 準備官方樣本和模型，將預設測試入口改為該 Compose 的 Nginx 連接埠，執行部署與官方 API 冒煙及 Playwright 官方套件。

## 背景工作程序的關閉行為

- Codex 負責 `services/api/search_worker.py`、Compose、工作程序測試及操作文件。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `dfdc82c`。
- Current milestone and status: 部署工作程序關閉行為已驗收，完整 Goal IN_PROGRESS。
- Goal of this session: 部署關閉時完成手上的背景工作，避免一般停止指令留下不必要的執行中紀錄。
- Files changed (with purpose): `services/api/search_worker.py` 接收 SIGTERM／SIGINT 並在工作之間停止取件，`docker-compose.yml` 允許三分鐘關閉時間，`tests/test_search_worker.py` 驗證搜尋完成後停止取件，更新 SETUP、PROGRESS 與交接。
- Database migrations added/applied: 無新增。沿用先前隔離部署和既有語料。
- API/Schema changes: 無。
- Commands actually run and results: 初次 pytest 碰到 Windows 共用暫存目錄權限，82 passed、7 skipped、8 errors。改用唯一 `--basetemp` 後 90 passed、7 skipped，既有 Starlette 棄用警告 1 則。Ruff 和 `git diff --check` 通過。本機 Docker 的預設建置器遇到工作區路徑編碼問題，改用 `COMPOSE_BAKE=false`；新隔離專案因 Docker IP 位址池已滿，沿用先前的隔離專案完成重建與部署冒煙。新版 Compose 的背景程序停止後為退出碼 0、非記憶體不足終止，生效的停止期限為 180 秒。另以同一工作映像執行替代搜尋，使用 `docker stop` 送出 SIGTERM，觀察搜尋完成、未開始報告、正常退出。
- Tests NOT run and reason: 本輪未啟用 PostgreSQL pytest 整合（7 skipped），未透過 Playwright 重跑完整研究流程。Docker 訊號測試以受控工作驗證時序，未測真實模型推論中途關機及逾越三分鐘。
- Data sources checked (exact URL/date) and license/access notes: 本輪未下載資料，沿用既有隔離環境。
- Known bugs / risks / blockers: 主機斷電、強制終止及超過 Compose 關閉期限仍依賴既有工作逾時機制。外部部署及人工相關性複核仍待完成。
- Decisions made (ADR links): 保留單一工作程序與既有資料庫狀態機，在搜尋與報告取件之間檢查關閉訊號。
- Uncommitted changes / file ownership warnings: 隔離資料庫及資料卷保留。
- Next 1–3 concrete actions: 核對 [正式建置官方遠端驗收](https://github.com/Johnnnny0823/RAG/actions/runs/45738965469)，完成人工相關性複核及外部部署。
- Exact reproduction steps: 執行 `pytest -q tests/test_search_worker.py`。以 SETUP 的 Compose 部署步驟啟動獨立環境，等 API 就緒後執行 `docker compose stop search-worker`，用 `docker inspect` 確認退出碼 0。

## 官方語料人工複核材料

- Codex 負責評估候選的離線閱讀檔、版本核對及評估操作文件。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `c269906`。
- Current milestone and status: 人工複核材料驗證完成，人工評分及完整 Goal IN_PROGRESS。
- Goal of this session: 讓人工複核者離線閱讀相同版本的官方證據。
- Files changed (with purpose): `scripts/export_review_packet.py` 匯出官方原文和來源，`scripts/evaluate_search.py` 讓既有版本比對回傳實際詳情供匯出使用。更新 EVALUATION、PROGRESS 及本交接。HTML 放在本機已忽略的 `.patent-data/review/`。
- Database migrations added/applied: 無。只讀隔離部署的 117 版本官方語料。
- API/Schema changes: 無。沿用專利號查詢、詳情與請求項。
- Commands actually run and results: CLI 產生四案、34 組材料，其中全文 14 組、請求項版 1 組、書目與摘要版 19 組。以 API 複核重建後 UUID 不同但版本相同，逐字比對 I941082 首項原文與 XPath，修改指紋後正確拒絕匯出。所有分數及理由仍空白。以 Chromium 經本機 HTTP 檢視匯出檔，展開 I941082 請求項並看到原文定位。Pytest 90 passed、7 skipped，Ruff 格式及 lint 通過。
- Tests NOT run and reason: 本輪只改離線工具，未啟用 PostgreSQL pytest 整合及完整網站 E2E。CLI 瀏覽器限制直接載入本機檔案，使用本機 HTTP 檢視。官方遠端正式建置 [45738965469](https://github.com/Johnnnny0823/RAG/actions/runs/45738965469) 已通過部署冒煙且仍在建立向量索引。前一提交一般 CI [45739388410](https://github.com/Johnnnny0823/RAG/actions/runs/45739388410) 通過。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 沿用 DATA_SOURCES 所載第 024019、053028 期。每件閱讀檔列出 API 已保存的官方來源、授權及卷期。
- Known bugs / risks / blockers: 人工評分、完整部署及外部 TLS 尚待驗收。書目摘要版本的判讀受可取得篇幅限制。
- Decisions made (ADR links): 閱讀檔與待填候選分開，保留匿名排序，保留全文字元與來源定位，避免原始標註被覆寫。
- Uncommitted changes / file ownership warnings: 閱讀檔與測試資料卷留在本機，未提交原始專利資料。
- Next 1–3 concrete actions: 人工複核 34 組候選並重算評估，追蹤官方 CI，驗收外部部署。
- Exact reproduction steps: 依 EVALUATION 的人工複核段落執行 `python -m scripts.export_review_packet`，使用已匯入 117 版本的隔離 API 和固定候選池。

## 向量索引並行控制

- Codex 負責 `services/retrieval/index_semantic.py`、索引測試與操作文件。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `aed8e68`。
- Current milestone and status: 向量索引並行控制本機驗收通過，完整 Goal IN_PROGRESS。
- Goal of this session: 防止操作員匯入流程及獨立指令同時重建相同模型索引，避免重複推論。
- Files changed (with purpose): `services/retrieval/index_semantic.py` 依模型資料列取得 PostgreSQL session advisory lock，`tests/test_semantic_index.py` 更新分批及回滾測試的連線行為。另更新 SETUP、PROGRESS 與交接。
- Database migrations added/applied: 無。隔離庫既有 117 個文件版本與 1,624 筆向量。
- API/Schema changes: 無。CLI 競爭同一模型時以退出碼 1 回報。
- Commands actually run and results: Pytest 90 passed、7 skipped，索引測試重跑 6 passed。Ruff lint 及格式通過。以隔離 Docker PostgreSQL 驗證一條連線持鎖時，同模型的第二次索引立即拒絕，不同模型鍵可取得，放鎖後重跑新增 0 筆、原有 1,624 筆向量保留。測試替身在任何重新嵌入時會使驗收失敗。
- Tests NOT run and reason: 本輪未跑全套 PostgreSQL pytest 或 Playwright，也未重新計算 1,624 筆向量。遠端正式部署 [45738965469](https://github.com/Johnnnny0823/RAG/actions/runs/45738965469) 仍在建立索引。
- Data sources checked (exact URL/date) and license/access notes: 無新增下載，沿用先前固定第 024019、053028 期。
- Known bugs / risks / blockers: 本輪未量測建置時間改善。人工相關性與外部部署仍待驗收。
- Decisions made (ADR links): 同模型使用負的 bigint 鎖鍵，與現有匯入流程的正值鎖鍵分開。沿用 NullPool，實體連線結束後 PostgreSQL 釋放鎖。
- Uncommitted changes / file ownership warnings: 測試使用先前的隔離資料卷，未變更既有原文或向量。
- Next 1–3 concrete actions: 追蹤正式建置遠端結果，完成人工相關性複核和外部部署驗收。
- Exact reproduction steps: 在官方隔離資料庫以獨立連線對模型資料列 ID 的負值取得 `pg_try_advisory_lock`。使用該模型執行索引 CLI 應回報忙碌。關閉持鎖連線後重跑，原本完成的版本應保留並略過。

## 正式入口速率限制

- Codex 負責 Nginx 入口限制、部署冒煙與操作文件。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `802cfed`。
- Current milestone and status: 本機正式入口驗收通過，完整 Goal IN_PROGRESS。
- Goal of this session: 限制公開入口高成本請求，保留既有 API 各自的節流訊息與狀態查詢。
- Files changed (with purpose): `apps/web/nginx.conf` 新增帳號與研究的來源 IP 配額，`scripts/smoke.py` 驗證兩組入口限制與狀態端點，官方 E2E 工作加入部署冒煙檢查，更新 API、SETUP、TESTING、PROGRESS 及交接。
- Database migrations added/applied: 無新增。隔離正式部署沿用先前遷移與官方語料。
- API/Schema changes: FastAPI 無修改。正式代理的 429 加入 `RATE_LIMITED`、`Retry-After: 2` 與 `Cache-Control: no-store`。
- Commands actually run and results: Nginx 語法檢查、部署及兩組限流冒煙通過。429 保留安全標頭，健康與工作進度請求抵達 API。首次誤將三種裝置連續用同一來源跑，3 passed、3 failed，觸發共用入口配額。每組使用新的入口配額重跑後，桌面、平板和手機的登入節流及專案操作共 6 passed，三種裝置官方專利號碼共 3 passed。pytest 90 passed、7 skipped，Ruff 及 Git diff 檢查通過。
- Tests NOT run and reason: 本輪未啟用後端 PostgreSQL pytest 整合、未重跑完整官方模型研究流程。既有的 [正式建置官方遠端工作](https://github.com/Johnnnny0823/RAG/actions/runs/45738965469) 在較早提交，尚未涵蓋本輪新增的速率檢查。
- Data sources checked (exact URL/date) and license/access notes: 無新下載，號碼查詢沿用固定官方語料。
- Known bugs / risks / blockers: 同一來源 IP 共用配額。外部代理和 TLS、跨實例配額與人工評分待驗收。
- Decisions made (ADR links): 僅於正式入口使用直連來源 IP。代理前方增加其他入口時須按已知代理網路重新設定來源識別。
- Uncommitted changes / file ownership warnings: 隔離資料卷保留，未修改既有開發服務。
- Next 1–3 concrete actions: 驗收正式入口的遠端冒煙、人工評分及外部部署。
- Exact reproduction steps: 依 SETUP 啟動隔離靜態部署，以 `scripts/smoke.py --deployment --deployment-rate-limit` 驗證。在同一來源反覆測試裝置的登入節流前，需重設隔離入口或等待配額恢復。

## HTTPS 正式入口驗收

- Codex 負責 HTTPS 覆蓋檔、Nginx、部署冒煙及操作文件。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `e84ea06`。
- Current milestone and status: 本機 HTTPS 驗收通過，完整 Goal IN_PROGRESS。
- Goal of this session: 從部署文件可在同一個 Nginx 正式入口啟用 HTTPS，並驗證官方資料與帳號 API。
- Files changed (with purpose): `docker-compose.tls.yml` 加入憑證掛載和僅發布 HTTPS 的連接埠，`apps/web/nginx-tls.conf` 加入 TLS listener，`apps/web/nginx.conf` 及 `docker-compose.deploy.yml` 正確轉送隔離代理的 scheme 和來源。`scripts/smoke.py` 支援信任測試 CA 並驗證重新導向，一般 CI 會執行 HTTPS 冒煙。
- Database migrations added/applied: 無新增。沿用原隔離部署與官方語料。
- API/Schema changes: 無。代理覆寫來源與協定標頭，讓 FastAPI 的尾斜線重新導向保留 HTTPS 與原始主機及連接埠。
- Commands actually run and results: Compose 建置與啟動、Nginx 含及不含 HTTPS 設定的語法檢查均通過。只有 `127.0.0.1:18443` 發布到主機。使用一天期測試憑證核對 TLS 1.2／1.3、系統未信任的憑證會被拒，指定該憑證後 HTTPS 冒煙、速率限制及官方專利版本、分頁與原始檔雜湊檢查均通過。驗證測試帳號註冊、登入、讀取和刪除。pytest 90 passed、7 skipped，Ruff lint 和格式通過。
- Tests NOT run and reason: 本輪未啟用 PostgreSQL pytest 整合，未以瀏覽器安裝測試憑證信任或重跑完整模型流程。一般 CI 新加入的 HTTPS 步驟未取得遠端完成結果。既有 [官方 E2E](https://github.com/Johnnnny0823/RAG/actions/runs/45738965469) 屬較早提交。
- Data sources checked (exact URL/date) and license/access notes: 沿用既有第 024019、053028 期，未下載新來源。
- Known bugs / risks / blockers: 外部網域公開 CA 憑證與續期、實際反向代理、防火牆、外部主機連線尚待驗證。人工相關性評分尚待完成。
- Decisions made (ADR links): 保留目前單一 Nginx 入口。只在使用 HTTPS 覆蓋檔時掛載部署方提供的憑證，預設綁定回環位址。
- Uncommitted changes / file ownership warnings: 測試憑證及私鑰位於作業系統暫存目錄，均未進入 repository。隔離測試服務已停止。
- Next 1–3 concrete actions: 驗證 HTTPS 遠端冒煙與官方 E2E，完成人工相關性複核，取得實際主機及憑證後驗收公開部署。
- Exact reproduction steps: 依 [HTTPS 部署操作](SETUP.md#使用自備憑證啟用-https) 啟動隔離 Compose，以 `scripts/smoke.py --deployment --deployment-rate-limit --ca-file` 驗證同源 HTTPS。

## 私人研究資料匯出

- Codex 負責帳號匯出 API、研究工作台入口、隔離測試及操作文件。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `a01fcd0`。
- Current milestone and status: 私人研究資料匯出已驗收，完整 Goal IN_PROGRESS。
- Goal of this session: 讓登入者可在研究工作台下載已保存的個人研究成果。
- Files changed (with purpose): `services/api/research_export.py` 查詢明確欄位及帳號範圍，`services/api/accounts.py` 提供受權限保護的下載。研究頁沿用私人下載處理並新增入口。Nginx 將匯出納入研究配額。新增 PostgreSQL 隔離測試及工作台下載斷言。另修正遠端 HTTPS 憑證生成指令。
- Database migrations added/applied: 無新增。匯出以 PostgreSQL 可重複讀取的快照取得資料。
- API/Schema changes: 新增 `GET /api/v1/me/export`，匯出 JSON 格式版本 1，附件回應為 `private, no-store`，未登入回傳 401。
- Commands actually run and results: 首次 pytest 收集發現測試段落插入位置錯誤，修正後包含隔離 PostgreSQL 共 98 passed、1 則既有警告。前端 lint、TypeScript、Vite build 及 Ruff 通過。正式建置在 Chromium 桌面、平板、手機各一項通過，核對檔名、帳號、已編輯專案及無密碼欄位。一般 CI [45741238355](https://github.com/Johnnnny0823/RAG/actions/runs/45741238355) 的舊 HTTPS 步驟因 OpenSSL 指令含額外加號失敗。修正成單行並從工作流程讀取同一命令，在 Linux 容器生成憑證且核對 IP SAN。
- Tests NOT run and reason: 未重跑完整模型與官方瀏覽器工作流程，尚待確認新版遠端 HTTPS 完整結果。
- Data sources checked (exact URL/date) and license/access notes: 本次使用隔離測試帳號，無新下載官方資料。
- Known bugs / risks / blockers: 大量私人資料匯出的資源用量尚未壓測。外部部署與人工相關性複核仍待驗收。
- Decisions made (ADR links): 匯出以獨立的 JSON 版本保存已持久化的研究資料。PDF 繼續由各研究結果下載。
- Uncommitted changes / file ownership warnings: 未提交私人帳號資料、下載檔或憑證。
- Next 1–3 concrete actions: 核對新版 HTTPS CI 及官方 E2E，完成人工相關性複核與外部部署。
- Exact reproduction steps: 啟動隔離測試庫，依 TESTING 執行 PostgreSQL 整合；以研究頁 `匯出我的研究資料（JSON）` 按鈕或帶本人 Bearer token 呼叫 `GET /api/v1/me/export`。

## 官方資料先行驗收

- Codex 負責官方 E2E 工作流程及測試文件。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `1169ddd`。
- Current milestone and status: 已在本機驗收資料先行階段，完整 Goal IN_PROGRESS。
- Goal of this session: 讓官方原檔、資料庫、詞彙檢索及號碼查詢先提供結果，並保留完整模型流程。
- Files changed (with purpose): `.github/workflows/tipo-e2e.yml` 新增手動執行的 `coverage`、拆分來源與模型測試、將會消耗測試配額的限流冒煙放在尾端。更新 TESTING、PROGRESS 及交接。
- Database migrations added/applied: 無新增。本機沿用 117 個版本的隔離資料庫。
- API/Schema changes: 無。
- Commands actually run and results: `scripts.seed_tipo_e2e --prepare-only --offline` 核對 24 檔 SHA-256。正式部署冒煙、官方專利資料與詞彙 API 以及桌面、平板與手機 Chromium 號碼查詢 3 passed。第一次把限流冒煙放前面，後續詞彙 API 遇到 429；將限流放在流程尾端後，來源階段與限流冒煙依序通過。
- Tests NOT run and reason: 本輪無產品程式變更，未重跑 pytest。未用本機重新建空白庫或全量向量，前一輪 [正式官方 E2E](https://github.com/Johnnnny0823/RAG/actions/runs/45738965469) 仍在建索引。新版來源模式須以遠端實跑驗收。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 使用固定第 024019、053028 期的本機雜湊快取，未下載新文件。
- Known bugs / risks / blockers: 來源模式的成功只證明來源與純詞彙功能。完整模型測試、人工相關性複核和公開部署需分別驗收。
- Decisions made (ADR links): `full` 保留為預設，要求同一組來源檢查全部通過後再啟動模型。各瀏覽器的號碼案例只在前段執行一次。
- Uncommitted changes / file ownership warnings: 本機驗收使用隔離 Compose，保留資料卷。
- Next 1–3 concrete actions: 核對新版來源模式、舊版尚在執行的完整官方工作及 HTTPS CI。
- Exact reproduction steps: 在 GitHub Actions 手動執行 `Official patent E2E`，選擇 `coverage=source`。完整模型驗收選擇 `coverage=full`。

## 官方語料展示與現況文件

- Codex 負責展示流程、架構文件及本機核心瀏覽器驗收。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `69f6521`。
- Current milestone and status: 本機完整核心展示及遠端來源模式已驗收，完整 Goal IN_PROGRESS。
- Goal of this session: 提供從 README 可重現的官方語料展示，更新架構現況與遠端驗收紀錄。
- Files changed (with purpose): README 提供展示入口，`docs/DEMO.md` 記錄按號碼與從構想到報告的流程，`docs/ARCHITECTURE.md` 更新工作佇列、來源核對、HTTPS 及資料邊界。同步進度及交接。
- Database migrations added/applied: 無新增，沿用 117 個版本、1,624 個向量的隔離資料庫。
- API/Schema changes: 無。
- Commands actually run and results: 隔離正式 Compose 建置暨啟動，核對兩個本機 Qwen 模型 digest，語意 API 冒煙通過，兩個已知公開號均為首筆。桌面 Chromium `tipo-research.spec.ts` 1 passed（1.3 分鐘），涵蓋拆解、特徵修改、RAG 搜尋、引用核對、歷史重開和私人 PDF。下載再以 pypdf 核對繁中、官方文件及來源。報告保存於 `.patent-data/demo/patentscope-official-research-sample.pdf`，SHA-256 `d32325fb4e71acfb2c68f8b94de512c460b122e6d3987959dcac7ef5b68a1772`。
- Tests NOT run and reason: 本輪未改產品程式碼，未重跑 pytest 或完整跨瀏覽器模型回歸。遠端 [來源模式](https://github.com/Johnnnny0823/RAG/actions/runs/45742177190) 已通過，模型階段按配置跳過。修正後的 [HTTPS CI](https://github.com/Johnnnny0823/RAG/actions/runs/45741807070) 已通過。先前完整官方遠端工作仍在建立索引。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 使用已匯入第 024019 與 053028 期，無新下載。PDF 內的官方來源 URL 已由測試核對。
- Known bugs / risks / blockers: 外部部署與人工相關性評分待驗。隔離資料庫另留一個先前測試帳號，本輪新增帳號經瀏覽器測試清理。
- Decisions made (ADR links): 選任一固定官方樣本可展示；此次使用公開樹脂案例便於重現。
- Uncommitted changes / file ownership warnings: 本機 PDF 為測試輸出，未放入 Git。隔離資料卷保留。
- Next 1–3 concrete actions: 完整遠端模型驗收、人工相關性複核及目標主機部署。
- Exact reproduction steps: 依 [展示指南](DEMO.md) 準備語料與模型，令 `PATENTSCOPE_E2E_TIPO=1` 並執行 `tipo-research.spec.ts`。

## API 主要操作紀錄

- Codex 負責 API 操作日誌、容器日誌設定、測試與操作文件。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `5d0a8ac`。
- Current milestone and status: 主要操作結果本機驗收通過，完整 Goal IN_PROGRESS。
- Goal of this session: 提供部署操作員可檢查的請求結果及工作完成紀錄，避開研究文字和識別資料。
- Files changed (with purpose): `services/api/activity.py` 與 `patents.py` 記錄路由樣板、操作方法、狀態及耗時，`search_worker.py` 與 `report_jobs.py` 記錄已提交的工作結果。API Docker 命令移除原始存取日誌，Compose 設置日誌輪替。增加單元及整合斷言，更新 ARCHITECTURE、SETUP、PROGRESS 和交接。
- Database migrations added/applied: 無新增，不建立帳號活動資料表。
- API/Schema changes: 無。
- Commands actually run and results: Ruff、Git diff 檢查及正式容器部署冒煙通過。完整 pytest 含 PostgreSQL 為 99 passed、1 則既有 Starlette 警告。兩項背景工作整合測試加入事件斷言後再跑，2 passed。實際送出帶合成標記的無效請求及測試帳號匯出，容器日誌含樣板與 422／200，未出現測試查詢、構想、文件 UUID、密碼或 Bearer token。測試帳號已清理。
- Tests NOT run and reason: 未修改介面契約，本輪未重跑 Playwright。較早的完整官方遠端工作仍在向量索引階段。
- Data sources checked (exact URL/date) and license/access notes: 本輪未下載官方資料。容器測試只使用隔離環境與合成隱私標記。
- Known bugs / risks / blockers: 不提供依帳號查詢的活動歷程或外部稽核保存。代理及其他服務日誌需在目標環境另驗。人工相關性及公開部署尚待完成。
- Decisions made (ADR links): 以固定欄位結構化日誌提供維運觀測，避免在日誌引入帳號及私人研究識別碼。
- Uncommitted changes / file ownership warnings: 日誌與測試資料留在隔離容器，未放入 Git。
- Next 1–3 concrete actions: 核對遠端完整官方驗收，完成人工評估與公開部署。
- Exact reproduction steps: 於隔離環境使用 `docker compose logs api search-worker`。先跑 `tests/test_activity.py`，再依 TESTING 啟用 PostgreSQL 整合驗證背景工作。

## 最新發明公開卷期匯入

- Codex 負責 S10 來源驗證、卷期解析、更新指令及資料文件。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `53f8f73`。
- Current milestone and status: 最新發明公開書目更新已驗收，完整 Goal IN_PROGRESS。
- Goal of this session: 從已核對的官方 S10 取得當期卷期及書目，安全試跑並保存匯入結果。
- Files changed (with purpose): `latest_publication.py` 提供預覽與可選匯入，`download.py` 共用固定 S10 下載，`issue_index.py` 驗證完整性與一致卷期，`test_tipo_issue.py` 驗證混期與宣告筆數錯誤。更新 DATA_SOURCES、SETUP、PROGRESS及交接。
- Database migrations added/applied: 無新增。全新隔離資料庫套用既有遷移與受限 API 角色。
- API/Schema changes: 無。以現有公開專利精確查詢、詳情與詞彙 API 驗收。
- Commands actually run and results: 從 S10 發現第 024020 期 1,639 筆。兩次 `--apply --limit 5` 保持 5 筆書目、20 個詞彙片段及 1 批次；第二次匯入標示重用、索引新增 0。兩次的來源內容皆為書目摘要，監控狀態顯示部分完成。唯讀 API 可精確及詞彙查到官方 `202642194`，詳情含 S10 和同一份來源雜湊。pytest 92 passed、8 skipped，Ruff 及 Git diff 通過。
- Tests NOT run and reason: 本輪未跑全部 PostgreSQL pytest 或瀏覽器套件。隔離 PostgreSQL 與 API 直接驗收最新書目匯入，未重建語意向量。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 核對 `https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S10`。輸入與輸出雜湊記在 DATA_SOURCES。
- Known bugs / risks / blockers: 最新個案全文、公告與異動公報各有來源方法，尚未併入此更新指令。未設定自動排程。完整遠端官方模型工作仍待確認。
- Decisions made (ADR links): 從 S10 XML 自身取得卷期，使用固定來源並驗證整份索引。預覽預設不寫入資料庫。
- Uncommitted changes / file ownership warnings: 最新期樣本留在隔離資料庫和物件卷，未提交原始資料。
- Next 1–3 concrete actions: 驗證最新期官方個案封存清單、自動更新及模型索引；持續核對遠端結果。
- Exact reproduction steps: 依 SETUP 的最新發明公開書目段落執行預覽及 `--apply --limit 5`。來源更新後當期號碼及雜湊會不同。

## 最新發明公開全文更新

- Codex 負責最新卷期的官方全文清單核對、更新指令與驗收文件。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `edbf653`。
- Current milestone and status: 最新期選取全文已驗收，完整 Goal IN_PROGRESS。
- Goal of this session: 從官方封存清單取得同一卷期的個案全文，保留原書目版和可回溯引文。
- Files changed (with purpose): `latest_publication.py` 新增三位數民國年參數，驗證封存清單與 S10 選取書目的一致性。`run_pipeline.py` 提供要求全數完成的離開狀態。補新增路徑的測試及資料、操作、進度與交接文件。
- Database migrations added/applied: 無新增。沿用隔離驗收資料庫。
- API/Schema changes: 無。使用既有公開號、詳情及請求項 API 驗收。
- Commands actually run and results: 在主機核對官方封存清單與兩份個案 XML，在隔離容器執行兩次 `latest_publication --archive-year 115 --apply --limit 2`，均回傳成功。首次新增 2 個全文版本及 143 個詞彙片段，保留原本 5 個書目版。重跑重用相同批次、索引新增 0。`verify_document 202642194` 從封存原文核對 9 項請求項與 62 段，API 檢查兩案同時保有書目與全文，請求項分別為 9、10 項。pytest 93 passed、8 skipped，Ruff 檢查通過。
- Tests NOT run and reason: 未重跑完整 PostgreSQL pytest 或瀏覽器套件。使用實際 PostgreSQL 與 API 驗收匯入；本輪只建立詞彙索引，未重建向量。一般 CI [45743650472](https://github.com/Johnnnny0823/RAG/actions/runs/45743650472) 在前一提交已通過。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 核對 S10 與 `ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024020/index_all.xml`，兩份公開說明書、原檔雜湊及來源授權見 DATA_SOURCES。
- Known bugs / risks / blockers: 只驗收本期所選兩案。資料更新排程、跨期容錯、最新公告及最新異動仍待驗收。
- Decisions made (ADR links): 封存年由已核對的目錄提供，個案下載沿用既有來源校驗、快取及隔離流程。
- Uncommitted changes / file ownership warnings: 新原檔與驗收資料保留在隔離資料卷，未提交原始資料。
- Next 1–3 concrete actions: 驗證自動排程及跨期切換，追蹤官方模型驗收。
- Exact reproduction steps: 依 SETUP 的最新發明公開書目段落預覽並執行全文命令，再查閱 API 與 `verify_document`。

## 第 024020 期語意檢索與引文驗收

- Codex 負責新卷期的向量、混合檢索及版本引文驗收腳本。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `a518038`。
- Current milestone and status: 新卷期語意與引文增量驗收通過，完整 Goal IN_PROGRESS。
- Goal of this session: 確認由新匯入流程取得的官方原文能經向量搜尋發現並回溯。
- Files changed (with purpose): `scripts/smoke_semantic.py` 新增第 024020 期已知案件及混合檢索核對。 `scripts/evaluate_citations.py` 增加同卷期精確引文與語意證據案例，更新 TESTING、EVALUATION、PROGRESS 與交接文件。
- Database migrations added/applied: 無新增。隔離資料庫以 Qwen3 Embedding 建立 7 個版本、166 筆向量。重跑新增 0 筆。
- API/Schema changes: 無。
- Commands actually run and results: `smoke_semantic.py --issue-024020` 通過，`202642194`、`202642585` 語意查詢各排第一，混合結果沒有重複同公開號。 `evaluate_citations.py --issue-024020` 對三版本執行字詞比對共 6 判定，兩段引文均核對成功。另測英文改寫，關閉語意查找時未找到證據，啟用後得到同版本說明書引文且逐字吻合。Ruff 與 Git diff 檢查通過。
- Tests NOT run and reason: 本輪只改驗收工具及文件，未重跑全套 pytest 與 Playwright。使用真實 PostgreSQL、Ollama 與 API 驗證新卷期。前一提交一般 CI [45744322517](https://github.com/Johnnnny0823/RAG/actions/runs/45744322517) 通過。較早的完整官方 E2E 仍在建索引。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 沿用第 024020 期既有核對原檔，未下載新資料。
- Known bugs / risks / blockers: 已知案件驗收不足以推論其他技術領域的相關性。人工評分、跨期更新排程與公開部署仍待完成。
- Decisions made (ADR links): 保留舊種子組的預設行為，以明確的卷期參數啟用增量驗收。
- Uncommitted changes / file ownership warnings: 隔離語料與向量未提交。
- Next 1–3 concrete actions: 核對完整官方遠端測試，複核人工評分，驗證更新排程與跨期切換。
- Exact reproduction steps: 先依 SETUP 匯入第 024020 期兩份全文並建向量，依 TESTING 在該 API 執行兩支 `--issue-024020` 驗收指令。

## 發明公開資料定期更新

- Codex 負責定期更新程序、Compose 選用服務、測試及操作文件。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `25114c2`。
- Current milestone and status: 發明公開定期更新已在隔離 Compose 驗收，完整 Goal IN_PROGRESS。
- Goal of this session: 部署方可選擇在容器內定期輪詢官方 S10，並沿用原有匯入及索引記錄。
- Files changed (with purpose): `refresh_publications.py` 提供更新、等待與失敗重試，Compose 增加預設停用的選用服務，環境範本與架構說明列出輪詢設定；新增測試驗證失敗及成功間隔。
- Database migrations added/applied: 無新增。沿用隔離資料庫及物件卷。
- API/Schema changes: 無。匯入繼續寫入既有操作員監控資料。
- Commands actually run and results: 確認未啟用 profile 時 Compose 無更新服務，啟用後正式建置並啟動服務。以 60 秒間隔輪詢 S10 兩次，兩次均核對第 024020 期並重用既有批次，新增詞彙片段均為 0，資料庫仍有 7 個文件版本、166 筆向量和 2 個批次。停止時退出碼 0。驗證失敗到下一次重試的測試時鐘，pytest 94 passed、8 skipped，Ruff 與 Git diff 檢查通過。
- Tests NOT run and reason: 本輪未重跑全部 PostgreSQL pytest 與瀏覽器套件。Compose 實測為書目輪詢，未在更新服務開啟全文年度參數或令官方服務刻意失敗。未等待下一個實際卷期發布。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 兩次請求 `https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S10` 均取得第 024020 期同一來源雜湊。
- Known bugs / risks / blockers: 只追蹤當次 S10 所提供卷期，停機或錯過的期別需從封存補入。全文模式跨年度需更新已核對的年目錄。公告、異動公報尚無定期更新。
- Decisions made (ADR links): 定期更新只在顯式啟用 Compose 服務後執行。預設每日查一次，錯誤後等 15 分鐘，原有資料完整性與來源規則照常適用。
- Uncommitted changes / file ownership warnings: 隔離排程測試已停止；本機既有專案未啟用排程。
- Next 1–3 concrete actions: 驗收跨期過渡、後補期間與公告更新，持續追蹤完整官方 E2E。
- Exact reproduction steps: 依 SETUP 的「定期更新」小節，在隔離專案用 `--profile patent-refresh` 啟動服務。使用日誌核對來源和週期間隔，從管理員監控或資料庫查詢工作狀態。

## 發明公告多案匯入

- Codex 負責公告解析、批次匯入及官方 S01 驗收。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `aa219a3`。
- Current milestone and status: 同一期所選公告的批次匯入已驗收，完整 Goal IN_PROGRESS。
- Goal of this session: 從同一份官方公告索引保存多件公告，維持各自的證書號及請求項來源。
- Files changed (with purpose): `download.py` 支援取得官方 S01 最新 XML，`grant_index.py` 一次解析選取公告，`import_issue.py` 支援重複指定 `--grant-number` 並將各件引文連到自己的 XML 位置。新增解析回歸與來源、操作文件。
- Database migrations added/applied: 無新增。隔離庫原有 7 個公開版本，驗收後另有 2 個公告版本。
- API/Schema changes: 無。從現有精確查詢、詳情及請求項 API 驗收兩案。
- Commands actually run and results: S01 官方原檔 SHA-256 核對通過。第 053030 期 `I942697`、`I942698` 批次匯入成功，建立 66 個詞彙片段。調換證書號順序重跑仍重用批次，新增索引 0。`verify_document` 核對 38、24 項請求項，唯讀 API 驗證不同申請號、公告類型、書目與請求項範圍、來源雜湊與不同的原文定位。pytest 95 passed、8 skipped，調整合成測試識別碼後重跑公告解析測試 3 passed。Ruff 與 Git diff 通過。
- Tests NOT run and reason: 未重跑完整 PostgreSQL pytest／Playwright，本輪以隔離 PostgreSQL 及 API 直接驗收公告匯入，未建立公告語意索引。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 核對 `https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S01`，實際來源細節見 DATA_SOURCES。
- Known bugs / risks / blockers: 目前只驗收選取兩件的公告請求項，未匯入公告說明書或啟用公告排程。
- Decisions made (ADR links): 保持舊單案命令及批次識別相容，多案批次以排序後的選取清單識別。
- Uncommitted changes / file ownership warnings: 官方案例存於隔離資料庫及未追蹤物件卷。
- Next 1–3 concrete actions: 驗收公告全文、公告排程及跨期補匯，持續查核完整模型遠端結果。
- Exact reproduction steps: 依 SETUP 的追蹤匯入小節取得該期官方索引並重複傳入兩個 `--grant-number`。

## 發明公告全文匯入

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `364165b`。
- Current milestone and status: 官方公告全文兩案例已驗收，完整 Goal IN_PROGRESS。
- Goal of this session: 從官方封存清單取得公告個案全文，保持與 S01 請求項版的來源隔離。
- Files changed (with purpose): `download.py` 驗證官方公告清單與個案路徑，`issue_manifest.py` 綁定證書號、申請號和期別，`specification.py` 解析公告個案根元素，`import_issue.py` 保存獨立全文版本，`verify_document.py` 支援核對公告全文。新增解析及來源回歸測試，更新 SETUP、DATA_SOURCES、PROGRESS、HANDOFF。
- Database migrations added/applied: 無新增，沿用隔離受限角色與原始物件卷。
- API/Schema changes: 無。兩個版本延用既有 `claims_only` 和 `fulltext` 欄位。
- Commands actually run and results: 官方封存清單 17,429,839 bytes，放寬限額僅套用已驗證的公告卷期清單。隔離庫先匯入兩件 S01 書目加請求項，再以清單匯入兩份公告全文，新增 252 個詞彙片段。重跑重用批次且新增 0。從官方原檔核對 `I942741` 的 13 項請求項與 165 段、`I942850` 的 5 項與 66 段。API 確認兩案各兩版；全文版請求項與段落的來源 SHA-256 相同，且與 S01 版本來源不同。忽略空白後兩案分別有 4 與 5 項請求項措辭不同。pytest 97 passed、8 skipped，Ruff 與 Git diff 通過。
- Tests NOT run and reason: 未跑完整 PostgreSQL pytest 和 Playwright，使用隔離真實 PostgreSQL、API 及官方原文驗收。公告全文向量未建立。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 核對政府目錄 15987、15983，S01、官方清單及 `PatentPubXML` 個案路徑。細節見 DATA_SOURCES。
- Known bugs / risks / blockers: 不是每份官方全文都具完整請求項標記；缺號或內容無法核對時將保留已驗證的 S01 版本並回報部分完成。公告自動排程、跨期補齊、人工相關性與外部部署待驗。
- Decisions made (ADR links): 公告個案內文與請求項取自同一份全文 XML，S01 文字獨立保留，避免版本內混用。
- Uncommitted changes / file ownership warnings: 原檔留在隔離物件卷與暫存目錄、未提交至 Git。
- Next 1–3 concrete actions: 驗證公告全文向量與更新排程，核對最新完整官方 CI。
- Exact reproduction steps: 按 SETUP 的公告個案全文段落下載並匯入同一期來源，以 `verify_document --grant-issue 053030 --grant-fulltext` 逐件驗證。

## 專利文件內容篩選

- Codex 負責搜尋篩選、報告、研究頁與官方公告向量驗收。
- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `ed4ef6d`。
- Current milestone and status: 文件內容篩選、公告向量與同版本引文已驗收，完整 Goal IN_PROGRESS。
- Goal of this session: 讓研究者可明確選擇全文、書目與請求項或書目與摘要，避免範圍不同的版本影響驗收。
- Files changed (with purpose): `services/api/patents.py` 讓三種檢索與涵蓋筆數共用篩選，`services/api/reports.py` 納入報告策略，研究頁增加輸入與結果條件。新增官方公告驗收腳本及更新既有 PDF E2E。
- Database migrations added/applied: 無新增。隔離語料的 6 個公告版本建立 340 筆向量，重跑新增 0。
- API/Schema changes: 搜尋請求新增可選 `content_scope`，舊搜尋與呼叫端省略時沿用原有行為。
- Commands actually run and results: 兩件第 053030 期公告逐一通過全文與請求項版的詞彙、語意、混合篩選及全文引文核對。正式建置桌面 Chromium 的模型拆解、全文篩選、搜尋保存、歷史與 PDF 測試 1 passed（45.8 秒），PDF 確認標示「文件內容 全文」。初次前端 lint 指出測試變數名稱重複，修正後 lint、型別及 Vite 建置通過。pytest 97 passed、8 skipped，Ruff 及 Git diff 通過。
- Tests NOT run and reason: 本輪未執行其餘瀏覽器及 PostgreSQL pytest 整合測試。新公告以針對實際 PostgreSQL、Ollama 及 API 的驗收腳本核對。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 使用既有第 053030 期公告及第 024019 期瀏覽器樣本，無新檔案下載。
- Known bugs / risks / blockers: 新篩選不改變未指定範圍時的版本排序策略。完整外部部署、人工相關性複核及跨期自動補匯尚待驗。
- Decisions made (ADR links): 使用現成的版本內容範圍枚舉，不增加資料庫欄位。舊的找回或報告流程保持相容。
- Uncommitted changes / file ownership warnings: 實際驗收使用兩個隔離資料庫。資料及 PDF 保留在未追蹤路徑。
- Next 1–3 concrete actions: 驗收公告與異動的更新流程，核對最新完整官方 CI，完成相關性人工複核。
- Exact reproduction steps: 依 TESTING 加入第 053030 期兩件公告的兩種版本並建向量，執行 `scripts/smoke_grant_versions.py`。以既有固定官方語料執行 `tipo-research.spec.ts` 驗證 UI 與 PDF。

## 發明公告定期更新

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `fc05c7b`。
- Current milestone and status: 官方資料定期更新 IN_PROGRESS。
- Goal of this session: 將 S01 公告加入選用的更新服務，核對重跑去重，查核使用者收到的官方 E2E 失敗通知。
- Files changed (with purpose): `services/ingestion/{download,grant_index,latest_publication,refresh_publications}.py` 新增最新公告下載、卷期驗證、CLI 與排程。`docker-compose.yml` 及 `.env.example` 提供選項。`tests/test_grant_index.py` 與 `tests/test_refresh_publications.py` 覆蓋公告發現及來源獨立性。本次同步更新操作、架構、進度與交接文件。
- Database migrations added/applied: 無新增。隔離 Compose 的 migration 服務成功執行。
- API/Schema changes: 無。
- Commands actually run and results: 本機 pytest 98 passed、8 skipped、1 則既有 Starlette 警告。Ruff 與 Git diff 檢查通過。`latest_publication --grants --limit 2` 實際讀得 1,162 件發明公告。隔離 Compose 兩輪均選 S10、S01 各 3 筆。首輪新增 `I942699`，API 驗證 5 項請求項及來源雜湊。第二輪兩源均重用批次，新增詞彙索引版本均為 0，資料庫維持公開、公告各 7 版本。S10 書目批次依資料範圍標為 `partial`。排程容器退出碼 0。另重查舊 [45669425487](https://github.com/Johnnnny0823/RAG/actions/runs/45669425487) 日誌，TIPO FTPS 資料連線 425 先於 API／瀏覽器測試。後續 [45737654914](https://github.com/Johnnnny0823/RAG/actions/runs/45737654914) 完整通過。
- Tests NOT run and reason: 此次本機 pytest 未啟用 8 項 PostgreSQL 整合案例。以隔離資料庫和 API 驗證排程，未重跑瀏覽器。S01 排程的封存全文與向量更新組合未在本輪驗證。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 查核官方 `https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S01` 第 053030 期與 `https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S10` 第 024020 期，沿用 DATA_SOURCES 記錄的來源條款與限制。
- Known bugs / risks / blockers: 固定樣本快取失效時，TIPO FTPS 仍可能回傳 425。尚未自動補匯跳過的卷期或更新法律事件。
- Decisions made (ADR links): S01 排程預設關閉，啟用後兩個來源各自執行。未指定封存年度時，S01 匯入請求項版。見 [定期更新](SETUP.md#定期更新)。
- Uncommitted changes / file ownership warnings: 隔離驗收容器已停止，保留隔離資料卷。其他專案的執行環境未動。
- Next 1–3 concrete actions: 核對正式建置官方 E2E、驗證跨期補匯規則，以及持續人工相關性複核。
- Exact reproduction steps: 依 SETUP 啟用 `TIPO_REFRESH_INCLUDE_GRANTS=yes`，等待兩輪後查驗 `ingestion_jobs` 的 `counts.import.reused`、`counts.lexical.versions` 及公告詳情 API。

## 最新卷期的官方日期

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `7f0b757`。
- Current milestone and status: 官方資料定期更新 IN_PROGRESS。
- Goal of this session: 補齊最新公開及公告版本日期，驗證不重複記錄來源，查核正式部署 E2E。
- Files changed (with purpose): `services/ingestion/latest_publication.py` 加入公報預覽與日期匯入，`services/ingestion/refresh_publications.py`、`docker-compose.yml`、`.env.example` 串接設定，`tests/test_gazette_dates.py` 覆蓋預覽、失敗與寫入順序，`docs/{DATA_SOURCES,SETUP,PROGRESS,HANDOFF}.md` 記錄。
- Database migrations added/applied: 無新增，沿用已遷移的隔離資料庫。
- API/Schema changes: 無。使用既有日期與來源欄位。
- Commands actually run and results: 啟用 PostgreSQL 的完整 pytest 107 passed、1 則既有 Starlette 警告。Ruff lint、format 及 Git diff 檢查通過。隔離排程容器成功跑一輪 S10 及 S01，補上各 7 個版本的日期。API 核對 `202642194` 的書目摘要及全文版、`I942697` 的請求項版，日期、來源雜湊及位置一致。以已保存原檔呼叫 `apply_dates` 重跑，兩來源各維持 1 筆批次、1 件原檔、7 筆連結。[正式部署官方 E2E 45738965469](https://github.com/Johnnnny0823/RAG/actions/runs/45738965469) 在 `dfdc82c` 完成向量索引、API 冒煙與 20 項瀏覽器測試。
- Tests NOT run and reason: 日期功能未在該次遠端 E2E 範圍內，也未本機重跑 Playwright。此次重跑驗證直接使用已保存公報，未等待第二次線上排程下載。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 取得民國 115 年第 024020、053030 期公報，網址、大小、SHA-256 及授權見 [來源](DATA_SOURCES.md#最新卷期的日期公報)。同日重抓 `https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/P10`，索引無卷期欄位。
- Known bugs / risks / blockers: Docker 新網路位址池不足，初始 Compose 啟動失敗。改在既有隔離網路以同一建置映像、排程模組及資料卷完成驗收。跨期補匯及法律事件自動定位待完成。
- Decisions made (ADR links): 日期年度為獨立選用設定，預設關閉。公報先驗證卷期及年份，再匯入文件與日期。見 [定期更新](SETUP.md#定期更新)。
- Uncommitted changes / file ownership warnings: 保留隔離資料卷供複驗，未變更其他 Docker 專案。
- Next 1–3 concrete actions: 驗證封存目錄能否支援可靠的跨期補匯及法律事件定位，持續人工相關性複核。
- Exact reproduction steps: 依 SETUP 設定 `TIPO_REFRESH_GAZETTE_YEAR=115` 和 `TIPO_REFRESH_INCLUDE_GRANTS=yes`，比對排程日誌、兩期官方原檔 SHA-256 及兩筆號碼查詢的詳情日期。

## 官方封存卷期補匯

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `981867f`。
- Current milestone and status: 官方資料更新 IN_PROGRESS。
- Goal of this session: 從已驗證的官方目錄補匯指定公開、公告卷期，保留個案來源並確認重試不重複。
- Files changed (with purpose): `services/ingestion/download.py` 讀取 FTPS 封存目錄，`latest_publication.py` 驗證固定卷期，`archive_backfill.py` 預覽並依期匯入，`tests/test_archive_backfill.py` 驗證缺期拒絕、出錯中止及原檔卷期不符。
- Database migrations added/applied: 無新增，沿用隔離資料庫。
- API/Schema changes: 無。
- Commands actually run and results: 含 PostgreSQL 的 pytest 110 passed、1 則既有 Starlette 警告。補匯專屬測試最後重跑 3 passed，Ruff 及 Git diff 檢查通過。正式容器實際補入 `202637274`、`I943859`、`I945115`，三筆 API 原檔雜湊一致，兩件公告各 20 項請求項與官方 XML 逐字比對通過。公開 024021 未列於目錄，預覽回傳非零代碼。首次離線重跑碰到同庫進行中的公開匯入，被既有鎖拒絕。等待完成後以保存原檔依序重跑三批，均重用批次、各新增 0 個索引版本。前筆提交的一般 [CI 45748570074](https://github.com/Johnnnny0823/RAG/actions/runs/45748570074) 通過。
- Tests NOT run and reason: 此切片未改前端，未重跑 Playwright。實際補匯使用公開書目、公告請求項與詞彙索引，全文、日期與向量組合未在此輪驗收。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 官方 FTPS 目錄與三個固定卷期索引，網址、雜湊及可用範圍見 [封存卷期目錄](DATA_SOURCES.md#封存卷期目錄)。
- Known bugs / risks / blockers: 公告封存最大期別與 S01 最新期可能不同。自動排程仍只處理最新索引，法律事件自動對期尚待驗證。
- Decisions made (ADR links): 操作者可指定同卷連續期別與每期案件上限，來源缺期即停止。見 [封存卷期補匯](SETUP.md#封存卷期補匯)。
- Uncommitted changes / file ownership warnings: 隔離驗收資料卷保留，其他專案服務未變更。
- Next 1–3 concrete actions: 依官方封存與入庫證據定位缺期，納入選用排程；持續檢查法律事件卷期及人工相關性標註。
- Exact reproduction steps: 依 SETUP 的命令預覽及補匯 `053031`～`053032`，以 API 和 `verify_document --grant-issue` 核對兩件公告。

## 封存卷期自動補匯

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `a5169a1`。
- Current milestone and status: 官方資料更新 IN_PROGRESS。
- Goal of this session: 在選用排程依官方目錄補期，用 PostgreSQL 進度驗證重啟後接續。
- Files changed (with purpose): `services/ingestion/archive_refresh.py` 辨識官方期別及完成紀錄，`refresh_publications.py`、Compose 及環境範例加入排程設定。`tests/test_refresh_publications.py` 覆蓋失敗重試、缺期及設定變更。
- Database migrations added/applied: `0016_archive_refresh` 在既有隔離庫、整合測試庫及全新 `patentscope_archive_clean` 套用成功。新庫進度表為空，向量運算回傳 1，API 角色無進度表讀權限。
- API/Schema changes: 公開 API 契約無變更。新增內部進度表 `archive_refresh_checkpoints`。
- Commands actually run and results: 含 PostgreSQL 的 pytest 111 passed、1 則既有 Starlette 警告，排程測試最後重跑 3 passed。Ruff lint、格式及 Git diff 檢查通過。第一輪重用 `053032` 匯入並寫進度，尚有待補時採 900 秒重試間隔。重啟後跳過已完成期別，實際匯入 `053033` 新增 1 筆版本及其詞彙索引。再次重啟，完成進度仍為兩期，當輪公告匯入 0 期。`verify_document` 及詳情、請求項 API 核對 `I946357` 的 14 項請求項與原始 XML 雜湊。隔離排程退出碼 0。上一筆提交的一般 [CI 45749375252](https://github.com/Johnnnny0823/RAG/actions/runs/45749375252) 通過。
- Tests NOT run and reason: 本輪未重跑 Playwright，未跑公開封存與日期、全文、向量同時啟用的排程組合。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 實下載 `ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053033/index.xml`，17,701,169 bytes、1,182 筆發明，SHA-256 `603792125d33dc6c01523af0bc83fa0591fb0d63a070df60908ad4dabb897446`。P10 與第 053033 期異動封存索引逐位元一致，見 [資料來源](DATA_SOURCES.md#專利權異動公報)。
- Known bugs / risks / blockers: 啟用自動補期時需設定同卷起始期及封存年份。跨年或換卷自動發現、法律事件更新、完成期別的自動修訂偵測均未實作。
- Decisions made (ADR links): 排程只在匯入成功後寫入完成紀錄，依資料階段、民國年、設定雜湊與期別查詢；工作本身沿用既有匯入鎖與去重。[資料庫設計](DATABASE.md)
- Uncommitted changes / file ownership warnings: 測試容器已停，保留隔離資料庫及官方原始物件。
- Next 1–3 concrete actions: 以 P10 與封存索引相等核對異動卷期，串接異動排程並對已索引案件驗收。
- Exact reproduction steps: 依 SETUP 啟用公告自動補期，起始 `053032`，每輪 1 期。第一輪寫入進度後重啟，再比對 `archive_refresh_checkpoints` 與 `I946357` API。

## 官方異動公報定期更新

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `822d143`。
- Current milestone and status: 官方資料更新 IN_PROGRESS。
- Goal of this session: 自動定位最新 P10 卷期，驗證原文後更新已收錄案件的消滅及更正事件。
- Files changed (with purpose): `services/ingestion/legal_refresh.py` 核對來源與事件身分，`download.py` 新增 P10 與固定封存索引讀取，`refresh_publications.py`、Compose、環境範例接上排程。擴充 pytest 及 `apps/web/e2e/legal-events.spec.ts` 的真實號碼查詢驗收。
- Database migrations added/applied: 無新增，沿用 `0016_archive_refresh`。
- API/Schema changes: 無，沿用既有 `legal_events` 詳情欄位。
- Commands actually run and results: pytest 含 PostgreSQL 115 passed、1 則既有 Starlette 警告，異動與排程專屬 10 passed。Ruff、前端 lint 及 TypeScript 通過。實際排程首輪 FTPS `425`，依 60 秒設定重試後新增 `I874215` 消滅紀錄。下一輪重跑該筆新增數為 0。`202639186` 入庫後，再由同一份官方公報新增 `I927657` 更正紀錄。正式建置專利號碼查詢的 Chromium 桌面、平板、手機共 3 passed。前一筆提交的一般 [CI 45749996252](https://github.com/Johnnnny0823/RAG/actions/runs/45749996252) 通過。
- Tests NOT run and reason: 最初執行兩個既有自然語言案例時，隔離 API 沒有設定嵌入模型，首案逾時並停止該套件。之後使用專利號碼查詢補驗事件 UI，未重跑模型搜尋案例。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26，`https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/P10` 與 `ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053033/index.xml` 逐位元一致。`sud08` 的 838 筆與 `sud24` 的 31 筆發明事件均符合索引身分。授權及各原檔 SHA-256 見 [資料來源](DATA_SOURCES.md#專利權異動公報)。
- Known bugs / risks / blockers: 指定年份的最近 8 期內必須有與 P10 相同的索引。歷史期別須手動補匯，其他事件類別與任意案件的即時法律狀態尚未整合。
- Decisions made (ADR links): 預設關閉，按檔案相等及原始卷期核對，保留既有兩類事件與去重方式。[設定](SETUP.md#最新異動公報定期更新)
- Uncommitted changes / file ownership warnings: 保留隔離資料庫及原始檔供複驗。
- Next 1–3 concrete actions: 核對完整的自動法律異動歷史匯入需求及授權條件，並追蹤人工相關性複核及正式目標主機驗收。
- Exact reproduction steps: 匯入 SETUP 的 `I874215` 和 `202639186` 範例，將 `TIPO_REFRESH_LEGAL_YEAR` 設為 `115`，再使用 TESTING 的號碼查詢測試。

## 歷史異動公報補匯

- Date/time (timezone): 2026-11-26（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `fix/cpu-embedding-index`，起點 `4d6bdb0`。
- Current milestone and status: 官方資料更新 IN_PROGRESS。
- Goal of this session: 歷史異動公報可先單期預覽，再由排程依序補匯且保留最新 P10 更新。
- Files changed (with purpose): `services/ingestion/legal_refresh.py` 加入封存卷期選項，`archive_refresh.py` 與 `refresh_publications.py` 串接歷史進度，Compose 及環境範例增加起始設定，擴充異動及排程測試。
- Database migrations added/applied: `0017_legal_archive_refresh` 擴充既有進度表的階段約束。既有隔離庫保留兩筆發明公告進度，試驗庫從空白遷移成功並通過 pgvector 運算。有法律異動進度時，舊約束不允許降版，遷移不會刪除進度。
- API/Schema changes: 公開 API 契約維持原有 `legal_events` 欄位。
- Commands actually run and results: pytest 含 PostgreSQL 117 passed、1 則既有 Starlette 警告，排程及異動 12 passed。`053032` 預覽核對 982 筆消滅及 33 筆更正發明事件。隔離排程成功記錄 `053032`、`053033`，新增 `I874722` 的更正事件。API 核對申請號、卷期、原始檔雜湊與 `sud24` 第 1 筆來源位置。重啟後歷史匯入 0 期，最新 P10 仍成功核對並新增 0 筆。上一筆的一般 [CI 45836596899](https://github.com/Johnnnny0823/RAG/actions/runs/45836596899) 通過。
- Tests NOT run and reason: 重新啟動隔離 Web 並執行 Playwright 的命令被本機執行政策攔下。本輪以已啟動的隔離 API 核對歷史事件。前一筆的號碼查詢 Chromium 三裝置驗收有獨立紀錄。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-26 實際下載 [第 053032 期異動封存](DATA_SOURCES.md#第-053032-期異動封存)，沿用資料集 15974 政府資料開放授權條款第 1 版。公告 `I874722` 自官方 `ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/114/PatentIsuRegSpecXMLA_052007/index.xml` 取得。
- Known bugs / risks / blockers: 歷史卷期完成後才收錄的新申請案，須手動重跑單期才會附上舊事件。跨年換卷、其餘事件種類與任意案件即時權利狀態仍待處理。
- Decisions made (ADR links): 歷史完成紀錄與既有公告／公開共用同一架構，最新 P10 每輪仍會對照新案重新配對。[設定](SETUP.md#歷史異動公報補匯)
- Uncommitted changes / file ownership warnings: 原始物件與隔離資料庫保留供複驗。
- Next 1–3 concrete actions: 考量歷史事件與新收錄案件重新配對的負載和完整性，持續人工相關性複核與正式目標主機驗收。
- Exact reproduction steps: 匯入官方 `I874722`，以 `TIPO_REFRESH_LEGAL_YEAR=115`、`TIPO_REFRESH_LEGAL_FROM=053032` 啟動隔離排程。在 `archive_refresh_checkpoints` 核對 `legal` 兩期，重啟後核對跳過紀錄與專利詳情 API。

## Gemini M6 選擇性整合

- Date/time (timezone): 2026-11-27（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `codex/gemini-m6-integration`，起點 `90ddd1f`。
- Current milestone and status: 整合與部署驗收 IN_PROGRESS。
- Goal of this session: 審查 ZIP 獨立檔與附帶補丁，整合符合目前分支的功能。
- Files changed (with purpose): 公開語料狀態與面板、帳號操作歷程、API 安全標頭、正式部署新增限流路徑、混合候選日期排序、PWA 靜態離線備援、原文標記與同案版本介面、測試及工作流程版本。
- Database migrations added/applied: `0018_audit_logs` 續接 `0017_legal_archive_refresh`。在既有測試庫及空白 `patentscope_gemini_m6` 套用成功。現有另一工作區尚未提交的 `0018_legal_event_catalog` 保留，將來合併需重新接續編號。
- API/Schema changes: 加入 `/api/v1/corpus/status`、本人 `/api/v1/audit-logs` 與混合查詢 `sort_by`。請求項依附與法律異動沿用開發分支實作。
- Commands actually run and results: Ruff、Oxlint、TypeScript、Vite 正式建置、pytest 含 PostgreSQL 123 passed、Nginx 冒煙與限流通過。實測受限 API 角色能寫入並讀取本人的歷程、無刪除權限。正式 Chromium 工作台冒煙與 PWA 離線頁、API 快取排除、靜態安全標頭驗證通過。初次前端建置缺少 Vite 型別宣告，補齊後成功。初次正式 Chromium 混跑限流冒煙與登入案例發生入口限流干擾，也發現代理重複標頭。後續隔離執行，Nginx 統一對外標頭後正式桌面工作台回歸通過。
- Tests NOT run and reason: 正式外部主機及實體裝置安裝尚未驗證。人工標註需由人員完成。
- Subsequent verification: `workspace.spec.ts` 與 `search-errors.spec.ts` 使用開發前端及同一隔離 API，在 Chromium 桌面、平板、手機及 Firefox／WebKit 桌面共 20 項通過。首次案例均完成，但 Windows 拒絕建立 HTML 報告目錄。改用暫存輸出與 list reporter 後重跑，以退出碼 0 完成。提交 `daa86ac` 的 [一般 CI](https://github.com/Johnnnny0823/RAG/actions/runs/45874611331) 與 [官方完整 E2E](https://github.com/Johnnnny0823/RAG/actions/runs/45874632186) 已啟動。
- Data sources checked (exact URL/date) and license/access notes: 本地驗收以隔離空白資料庫與既有測試資料為主。官方語料由原有 E2E 流程載入。本輪未擴大資料源或授權範圍。
- Known bugs / risks / blockers: 依帳號提供的操作歷程目前只涵蓋三種操作，寫入失敗會記錄告警。PWA 離線提供說明頁。背景模型操作及專利詳情須連線。
- Decisions made (ADR links): 保留已有 Nginx 限流與 TLS。未導入未設容量上限的行程內 IP 限流。公開批次監控只回傳固定名稱的非負整數。高亮先核對文件版本、來源雜湊、XPath 與字元位置。
- Uncommitted changes / file ownership warnings: ZIP 未整批套用，原工作區的歷史異動配對變更維持現況。
- Next 1–3 concrete actions: 核對此提交一般及官方 CI，接續保留的歷史異動配對並整合遷移鏈，完成人工檢索複核與正式環境驗收。
- Exact reproduction steps: 依 TESTING 跑 PostgreSQL 整合、工作台 Playwright 及 `PATENTSCOPE_E2E_TIPO=1`。使用正式映像完成服務工作程序註冊後，將瀏覽器切為離線並重整，以確認離線頁及 API 快取隔離。

## 晚入庫案件的歷史異動配對

- Date/time (timezone): 2026-11-27（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `codex/gemini-m6-integration`，起點 `057654a`。
- Current milestone and status: 官方資料匯入與整合驗收 IN_PROGRESS。
- Goal of this session: 將晚入庫案件的自動歷史異動配對接到 Gemini 整合分支。
- Files changed (with purpose): 增加 `legal_linking.py`，串接 `import_issue.py`、`legal_events.py`、`run_pipeline.py` 及定期更新；異動重播測試覆蓋損壞物件及續跑。
- Database migrations added/applied: `0019_legal_event_catalog` 接在 `0018_audit_logs`，Alembic 單一 head。空庫及既有隔離庫套用成功，空測試庫亦通過回復至 `0018_audit_logs` 再升級。API 角色無暫存表讀權限。
- API/Schema changes: 保留專利詳情 `legal_events` 契約。
- Commands actually run and results: 含 PostgreSQL 的 pytest 124 passed、1 則既有 Starlette 警告。Ruff lint 與格式通過。用 `legal_events --replay-stored` 讀取 4 個保存的官方異動原檔，加總 1,884 筆。先核對 `I874744` 尚未入庫，再匯入其官方 `052007` 公告，得到 1 筆 `053032` 更正。API 核對 `sud24` 第 2 筆原文位置、證書號及 SHA-256。同批重跑與再次重播後資料庫仍只有 1 筆。Gemini 程式提交 `daa86ac` 的 [一般 CI](https://github.com/Johnnnny0823/RAG/actions/runs/45874611331) 已通過。
- Tests NOT run and reason: 這次沒有改前端。Gemini 提交的完整官方 E2E 繼續運行，尚未得出結果。
- Data sources checked (exact URL/date) and license/access notes: 使用先前保存的 `ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053032/sud24.xml` 及 `ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/114/PatentIsuRegSpecXMLA_052007/index.xml`，未從來源重新下載。
- Known bugs / risks / blockers: 歷史配對涵蓋已保存且通過解析的事件。其他官方類別、任意案件即時權利狀態及人工檢索評估仍待處理。
- Decisions made (ADR links): 保留原檔、以申請號查找、兩端匯入後以交易鎖同步連結。重播會驗證原檔完整性，錯誤不阻擋其他檔案。
- Uncommitted changes / file ownership warnings: 原工作區的未提交版本仍保留。此分支已重新接續遷移，整合時直接沿用此版本以避免重複移植。
- Next 1–3 concrete actions: 查核官方 E2E，接續正式目標主機驗收及人工相關性複核。
- Exact reproduction steps: 先從有保留物件的測試庫執行 `legal_events --replay-stored`，再匯入公告 `I874744` 並查其 API 詳情。

## 人工相關性複核表

- Date/time (timezone): 2026-11-27（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `codex/gemini-m6-integration`，起點 `d29b891`。
- Current milestone and status: 檢索評估 IN_PROGRESS。
- Goal of this session: 讓複核者在離線頁面直接判讀、保存進度，並輸出評估器可讀的 JSON。
- Files changed (with purpose): `scripts/export_review_packet.py`、`scripts/review_packet.js` 加入離線輸入及版本檢查，`scripts/evaluate_search.py` 接受全不相關案件，補上回歸測試。
- Database migrations added/applied: 無。
- API/Schema changes: 無。評估報告在沒有相關判定時以 `null` 表示未定義的召回率及 nDCG，彙總附可計算的執行次數。
- Commands actually run and results: 在 117 版本隔離 API 重新核對 34 組文件並輸出 `.patent-data/review/patentscope-review.html`，SHA-256 `07cdfe26cc06c4b3a850b33b0ad91876e4b744cb8783582ac9caa87be7e158e7`。Chromium 驗證草稿、重新匯入、拒絕錯誤版本及阻止未完成檔案。DEMO 單件測試核對完成檔的 0 分可保留。pytest 116 passed、9 skipped，Ruff lint、格式通過。[整合 CI](https://github.com/Johnnnny0823/RAG/actions/runs/45875599952) 首次因 Runner 套件來源 403 失敗，重跑已通過瀏覽器安裝。[官方 E2E](https://github.com/Johnnnny0823/RAG/actions/runs/45874632186) 仍在建向量。
- Tests NOT run and reason: 人工標註尚未提交，未執行人工資料集的檢索評估。9 個資料庫測試本輪未啟用，上輪完整整合已執行。
- Data sources checked (exact URL/date) and license/access notes: 使用 2026-11-27 隔離 API 對既有 117 版本官方語料重查，原始網址及雜湊隨文件顯示。
- Known bugs / risks / blockers: 19 組只有書目與摘要，可保留空白並另行取得證據。正式目標主機及完整官方 E2E 尚待。
- Decisions made (ADR links): 歷史 35 組候選與新版 34 組固定版本池分開。人工標註表維持既有池的文件身分與順序，沒有預填相關性。
- Uncommitted changes / file ownership warnings: 互動 HTML 為本機驗收產物，未加入 Git。
- Next 1–3 concrete actions: 確認官方 E2E，待複核檔匯出後用原本固定語料重跑評估。
- Exact reproduction steps: 依 EVALUATION 的 `export_review_packet` 命令產生 HTML，打開並填寫複核。以下載的完成檔傳入 `evaluate_search.py --dataset`。

## PWA 部署回歸

- Date/time (timezone): 2026-11-27（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `codex/gemini-m6-integration`，起點 `08a627f`。
- Current milestone and status: 部署整合與檢索評估 IN_PROGRESS。
- Goal of this session: 將 PWA 斷線及 API 快取隔離納入正式前端映像的驗收。
- Files changed (with purpose): `apps/web/public/sw.js` 的首頁請求明確繞過 HTTP 快取。`apps/web/e2e/pwa.spec.ts`、`apps/web/playwright.config.ts` 與 `.github/workflows/tipo-e2e.yml` 加入包裝版測試及官方 CI 關卡。
- Database migrations added/applied: 無。
- API/Schema changes: 無。
- Commands actually run and results: 前端 lint、build、Docker deploy target build、`scripts/smoke.py --deployment` 通過。隔離 Nginx 的 PWA 回歸 5 passed，涵蓋三種 Chromium 裝置、桌面 Firefox 與 WebKit。Firefox 模擬離線時顯示應用程式的離線橫幅，其他四個專案在嚴格檢查中顯示專用離線頁。
- Tests NOT run and reason: 本輪未重跑正式公開主機與實體手機驗收。一般瀏覽器套件曾誤指向含部署限流的服務，兩件因 429 失敗，另有一件因兩組測試共用 trace 目錄失敗。一般 CI 應使用開發配置，[起點 CI 45876335450](https://github.com/Johnnnny0823/RAG/actions/runs/45876335450) 已通過。完整官方 E2E [45874632186](https://github.com/Johnnnny0823/RAG/actions/runs/45874632186) 仍在建立 CPU 向量索引，對應先前整合提交。
- Data sources checked (exact URL/date) and license/access notes: 本輪測試隔離語料狀態端點及網路行為，未重新下載官方資料。
- Known bugs / risks / blockers: 公開主機、對外 TLS 信任及人工相關性標註仍待驗收。
- Decisions made (ADR links): 共用 Playwright 斷言接受專用離線頁或應用程式的離線橫幅，兩種情形皆必須證明 API 無法離線讀取且可恢復連線。
- Uncommitted changes / file ownership warnings: 實作限於整合工作樹，原工作樹及 `main` 未變動。
- Next 1–3 concrete actions: 等待完整官方 E2E，驗證此提交的遠端來源模式，以及取得人工標註。
- Exact reproduction steps: 啟動正式 Nginx 映像與隔離 API，依 TESTING「部署版 PWA 離線驗收」設定環境變數後執行 Playwright。

## 官方固定樣本匯入檢查

- Date/time (timezone): 2026-11-27（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `codex/gemini-m6-integration`，起點 `82d3188`。
- Current milestone and status: 官方來源回歸 IN_PROGRESS。
- Goal of this session: 使固定樣本檢查相容法律事件整合新增的匯入計數。
- Files changed (with purpose): `scripts/seed_tipo_e2e.py` 接受舊批缺欄位或新批 `legal_events_linked=0`，非零照常拒絕。`tests/test_tipo_e2e_seed.py` 覆蓋兩種新回傳及既有重用批次。
- Database migrations added/applied: 無新增。
- API/Schema changes: 無。
- Commands actually run and results: [一般 CI 45877176064](https://github.com/Johnnnny0823/RAG/actions/runs/45877176064) 通過。改用 Vite 測試配置重跑一般 Playwright，12 passed。官方來源模式 [45877188284](https://github.com/Johnnnny0823/RAG/actions/runs/45877188284) 的 PWA 驗收及 24 份固定原檔檢查均通過，第一批匯入結果新增欄位導致斷言失敗。本機重現一項失敗，修正後 pytest 116 passed、9 skipped，Ruff 格式與 lint 通過。
- Tests NOT run and reason: 本機未重建整套官方模型；此輪的 PostgreSQL pytest 依環境設定略過 9 項。
- Data sources checked (exact URL/date) and license/access notes: 遠端按固定樣本清單以 SHA-256 核對 24 份官方 XML，來源及限制以 DATA_SOURCES 為準。
- Known bugs / risks / blockers: 修正版 `e73e09e` 的[一般 CI](https://github.com/Johnnnny0823/RAG/actions/runs/45877742498)、[官方來源模式](https://github.com/Johnnnny0823/RAG/actions/runs/45877757310) 及[完整官方 E2E](https://github.com/Johnnnny0823/RAG/actions/runs/45878789673) 已通過。公開主機及人工相關性複核仍待。
- Decisions made (ADR links): 明確保留其他計數與錯誤欄位的比對，沒有相關事件的測試語料才允許計數為零。
- Uncommitted changes / file ownership warnings: 僅修改整合工作樹。
- Next 1–3 concrete actions: 觀察 `e73e09e` 完整官方 E2E，記錄模型及跨瀏覽器結果並核對引文。
- Exact reproduction steps: 執行 `pytest -q tests/test_tipo_e2e_seed.py`，再以 `coverage=source` 觸發官方工作流程。

## 檢索評估來源紀錄

- Date/time (timezone): 2026-11-27（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `codex/gemini-m6-integration`，起點 `4463d52`。
- Current milestone and status: 檢索評估 IN_PROGRESS。
- Goal of this session: 檢索評估輸出可以回查使用的標註與官方語料涵蓋。
- Files changed (with purpose): `scripts/evaluate_search.py` 紀錄資料集 SHA-256 與官方語料狀態，發現狀態改變時拒絕輸出。`tests/test_evaluate_search.py` 驗證雜湊穩定性及索引涵蓋變動。
- Database migrations added/applied: 無。
- API/Schema changes: 無。離線評估 JSON 新增 `dataset_sha256` 與 `corpus_status`。
- Commands actually run and results: Ruff format、lint 通過。pytest 117 passed、9 skipped。隔離 117 版本 corpus 以 `--repeats 2` 實跑 24 次，詞彙、向量、混合加重排各 8 次。模式 P50 為 43.31、256.00 與 12958.03 毫秒，報告保存在 `.patent-data/review/tipo-seed-provenance-eval.json`。
- Tests NOT run and reason: 本輪不啟用 pytest PostgreSQL 的 9 個整合測試，另使用真實 PostgreSQL 與 Ollama 執行評估。人工標註仍待提交。
- Data sources checked (exact URL/date) and license/access notes: 沿用第 024019／053028 期固定官方資料快照，網址與授權查 DATA_SOURCES。查詢前後以真實 API 核對 117 個詞彙與向量覆蓋版本。
- Known bugs / risks / blockers: 若內容更新但狀態計數相同，報告的狀態比對無法辨識。完整還原仍需固定語料原檔、資料庫快照與模型版本。
- Decisions made (ADR links): 共用既有公開語料端點，雜湊以排序鍵值的 UTF-8 JSON 內容為準。
- Uncommitted changes / file ownership warnings: 評估 JSON 為本機忽略目錄產物。
- Next 1–3 concrete actions: 核對完整官方工作流程、接收人工標註後對同語料重跑評估、確認實際部署主機。
- Exact reproduction steps: 啟動已匯入官方種子的隔離 API 與既有 Ollama，執行 `python -m scripts.evaluate_search --api http://127.0.0.1:18168 --repeats 2`。

## 混合檢索候選清單的來源與摘要

- Date/time (timezone): 2026-11-27（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `codex/gemini-m6-integration`，起點 `fa352a9`。
- Current milestone and status: 研究工作台增量通過隔離驗收，整體部署與人工評估 IN_PROGRESS。
- Goal of this session: 候選清單直接提供可核對的官方書目、摘要與來源連結。
- Files changed (with purpose): `services/api/patents.py` 批次讀取同版本的摘要、申請人、IPC 與官方資料集，`apps/web/src/research.tsx` 顯示新增資料。`tests/test_fusion.py` 及官方日期、研究 E2E 補回歸檢查。
- Database migrations added/applied: 無新增。將 117 版本測試庫的獨立副本升級至既有 `0019_legal_event_catalog`。
- API/Schema changes: 混合檢索及保存候選加 `abstract_excerpt`、`applicants`、`ipc_codes`、`official_source_url`。舊保存紀錄可讀。
- Commands actually run and results: pytest 126 passed，含 9 項 PostgreSQL 整合測試。Ruff、Oxlint、前端 build 及 API／Nginx 容器建置通過。日期 Playwright 5 passed，涵蓋 Chromium 桌面、平板、手機及桌面 Firefox、WebKit。混合與部署冒煙通過。用合成帳號保存並重開真實候選，欄位與排序參數核對通過，測後刪除該帳號。
- Tests NOT run and reason: 本版尚未執行完整遠端官方工作流程。最近通過的 [完整官方 E2E](https://github.com/Johnnnny0823/RAG/actions/runs/45878789673) 對應 `e73e09e`。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-27 核對公開案 `202639611`，以固定 [TIPO 官方資料集](https://data.gov.tw/dataset/9683) 與現存公報副本核對日期及原檔連結。
- Known bugs / risks / blockers: 首輪手動升級隔離副本未執行角色配置，詳情 API 回傳 503。依 Compose 原有步驟重配 API 角色後，詳情與公報測試通過。pytest 整合測試首次使用公報副本，因資料庫名稱保護觸發 9 項設定錯誤，改至專用 `patentscope_test` 後通過。人工標註及外部主機驗收仍待。
- Decisions made (ADR links): 在檢索的唯讀資料快照內依相同 UUID 讀取摘要及網址，沿用專利詳情的官方來源過濾。
- Uncommitted changes / file ownership warnings: 變更限整合工作樹，手動驗收資料庫為測試副本。
- Next 1–3 concrete actions: 核對新提交的 CI、取得人工標註、確認可供驗收的部署主機。
- Exact reproduction steps: 匯入固定官方語料並補齊第 024019 卷期日期，套用既有遷移與 API 權限配置。依 TESTING 設定 `PATENTSCOPE_E2E_TIPO=dates` 執行 Playwright。

## 候選檢索理由

- Date/time (timezone): 2026-11-27（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `codex/gemini-m6-integration`，起點 `491658a`。
- Current milestone and status: 可解釋檢索增量已在隔離環境驗收，整體部署與人工評估 IN_PROGRESS。
- Goal of this session: 以檢索器實際欄位與順位提供候選相關原因。
- Files changed (with purpose): `services/api/patents.py` 回傳詞彙命中的索引欄位，`apps/web/src/research.tsx` 顯示詞彙區段、語意候選及重排理由。更新 API 文件與融合、日期及重排測試。
- Database migrations added/applied: 無。
- API/Schema changes: 混合與保存候選加 `lexical_match_fields`。舊保存資料缺少此項時仍可顯示檢索分支。
- Commands actually run and results: Ruff、Oxlint 及 API／Nginx 映像建置通過。pytest 126 passed（含 9 項 PostgreSQL）。固定官方公報 Playwright 5 passed，官方重排桌面 1 passed。受限角色對三組查詢各測 20 次詞彙 SQL，前後候選、順位與分數一致，P50 由 0.479／0.632／1.477 ms 至 0.507／1.163／1.687 ms。這是 117 版本小語料與當地環境執行時間。
- Tests NOT run and reason: 本提交的全套遠端官方 E2E 尚未執行。起點一般 CI [45938111033](https://github.com/Johnnnny0823/RAG/actions/runs/45938111033) 通過，[起點官方 E2E](https://github.com/Johnnnny0823/RAG/actions/runs/45938131415) 執行中。
- Data sources checked (exact URL/date) and license/access notes: 隔離回放第 024019／053028 期的 117 個官方版本。2026-11-27 核對公開案 `202639611` 的英文標題、摘要詞彙命中及語意順位，沿用[官方資料集](https://data.gov.tw/dataset/9683)。
- Known bugs / risks / blockers: 大語料的欄位彙總成本與本機資料庫差異仍待量測。人工標註與公開主機仍待。
- Decisions made (ADR links): 使用資料庫實際命中的同版索引欄位，不推論技術特徵相符程度。語意分支說明為候選資格。
- Uncommitted changes / file ownership warnings: 變更限整合工作樹。
- Next 1–3 concrete actions: 核對遠端官方工作流程，取得人工標註與正式主機配置。
- Exact reproduction steps: 啟動 117 版本固定官方語料與 Ollama。在正式 Nginx 測試站用 `dates` 執行公報套件，再用 `versions` 執行 `search-rerank.spec.ts`。

## 部署版 PWA 與官方索引就緒驗收

- Date/time (timezone): 2026-11-27（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `codex/gemini-m6-integration`，起點 `dd779a6`。
- Current milestone and status: 隔離環境驗收通過，公開部署 IN_PROGRESS。
- Goal of this session: 分別驗證部署的靜態入口、PWA 配置與真實專利索引的可用狀態。
- Files changed (with purpose): `apps/web/nginx.conf` 提供正確的 manifest 媒體類型。`scripts/smoke.py` 檢查正式 PWA 及官方索引。官方工作流程在語意檢索通過後追加官方索引就緒檢查，`tests/test_smoke.py` 增加正反向驗證。
- Database migrations added/applied: 無。
- API/Schema changes: 無。冒煙沿用 `/api/v1/corpus/status`。
- Commands actually run and results: Ruff 通過，pytest 122 passed、9 skipped。Nginx 正式映像以空庫及 117 版本庫分別驗證，空庫的官方索引檢查如預期失敗。回環 HTTPS 合併執行部署、官方覆蓋與限流檢查通過。實際語意 API 的 `202640162`、`202639611` 測試各排第一。包裝版 PWA Chromium 3 passed。
- Tests NOT run and reason: 本輪未重跑 PostgreSQL pytest 整合套件，已由實際部署使用隔離 PostgreSQL 驗收。公開 DNS、外部 CA、目標主機與實體裝置待驗證。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-27 使用第 024019／053028 期已核對的固定官方資料。來源及授權見 DATA_SOURCES。
- Known bugs / risks / blockers: 舊映像回傳 `application/octet-stream`，已修正。回環 TLS 首次因 D 槽無法掛載，改以 Windows 暫存路徑成功。手動 API 測試容器補上與 Compose 相同的代理設定後才保持 HTTPS 重新導向。合併限流測試首次得到 429，已將語料檢查移到觸發限流前。
- Decisions made (ADR links): 日常 readiness 可通過空庫，對外語料驗收以額外參數要求詞彙與向量涵蓋大於零。模型與查詢品質仍由真實檢索和人工資料集驗證。
- Uncommitted changes / file ownership warnings: 只修改整合工作樹。驗收憑證與容器未納入版本庫。
- Next 1–3 concrete actions: 確認遠端官方工作流程、公開主機前置條件及人工標註。
- Exact reproduction steps: 依 SETUP 對已匯入官方語料的測試網站執行 `scripts/smoke.py --deployment --require-official-index`。HTTPS 測試載入測試 CA，限流檢查只在隔離網站執行。

## 官方原文查閱入口

- Date/time (timezone): 2026-11-27（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `codex/gemini-m6-integration`，起點 `1179bf9`。
- Current milestone and status: 官方原文回查通過隔離驗收，PDF 匯入及整體交付仍待。
- Goal of this session: 讓使用者可經瀏覽器回查已索引案件，保留精確原始檔追溯資料。
- Files changed (with purpose): `apps/web/src/research.tsx` 提供官方查詢頁、應輸入的文件號與每份已儲存原檔的雜湊及定位。官方日期與號碼測試核對畫面。
- Database migrations added/applied: 無。
- API/Schema changes: 無。前端開始顯示 detail API 既有的 `artifact_sha256` 與 `record_locator`。
- Commands actually run and results: 前端 lint、正式 Nginx 容器 build、部署及官方索引冒煙通過。固定公報在五個 Playwright 瀏覽器專案通過，公告號碼查詢再通過三個 Chromium 尺寸。補上 XPath 精確核對後另重跑桌面用例通過。起點一般 [CI 45939258288](https://github.com/Johnnnny0823/RAG/actions/runs/45939258288) 通過。
- Tests NOT run and reason: 本輪僅改 UI 及其驗收，未重跑 Python 及 PostgreSQL pytest。瀏覽器回歸不送出第三方查詢，官方入口另以讀取官方導覽與首頁確認。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-27 核對[官方查詢入口](https://tiponet.tipo.gov.tw/S092_OUT/2022/out)、[網站導覽](https://tiponet.tipo.gov.tw/S092_OUT/2022/sitemap)及[TIPO 下載方式](https://cloud.tipo.gov.tw/S220/opdata/information/ftp)。既有公開案與公告案來源見 DATA_SOURCES。
- Known bugs / risks / blockers: 官方查詢結果沒有固定網址列表，使用者須在入口輸入文件號。公報 PDF 匯入及站內解析未實作。人工標註與公開主機驗收仍待。
- Decisions made (ADR links): 使用官方導覽提供的 HTTPS 首頁。保留現有官方原檔連結，另提供可選取的 FTPS 位址以供支援的用戶端。
- Uncommitted changes / file ownership warnings: 變更限整合工作樹。
- Next 1–3 concrete actions: 核對完整官方 E2E，確認 PDF 的可用檔案取得與使用條件，取得人工標註。
- Exact reproduction steps: 使用同一套 117 版本固定官方語料，依 TESTING 執行 `dates` 及 `versions` 的 `patent-number.spec.ts`。

## 發明公開公報個案 PDF

- Date/time (timezone): 2026-11-27（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `codex/gemini-m6-integration`，起點 `98905fb`。
- Current milestone and status: 發明公開公報的單案 PDF 來源已驗收。公報 PDF 的全文檢索、其他文件階段及全面匯入仍待。
- Goal of this session: 由官方個案資料查驗 PDF 及首頁編號，附加到指定的已匯入公開版本。
- Files changed (with purpose): `services/ingestion/gazette_pdf.py` 下載、限定同源、核對首頁識別、保存原始位元及批次來源。`tests/test_gazette_pdf.py` 驗證識別與來源拒絕。既有 pypdf 固定版本納入執行依賴。前端詳情提供公報 PDF 連結，混合候選仍優先選政府資料目錄。
- Database migrations added/applied: 無。使用既有批次、原檔和文件來源關係。
- API/Schema changes: 無新欄位。專利詳情的 `sources` 可包含公報 PDF 與 `PDF page 1` 來源定位。
- Commands actually run and results: 單案預覽、套用及重跑成功。API 核對一筆 PDF 來源、SHA-256、122 段說明書仍可取得。Chromium 核對 PDF 連結、雜湊和 19 項請求項。前後端 Docker build、Ruff 與 pytest 124 passed、9 skipped。起點的一般與官方來源模式均通過。
- Tests NOT run and reason: 本輪未啟用 PostgreSQL pytest 整合套件，另以真實 PostgreSQL、正式映像與真實 TIPO 檔案執行整合。尚未驗收公告、掃描 PDF、OCR 或站內預覽。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-27 實際從官方前端的個案查詢取得 `202639611` 的原件連結，下載並核對 PDF。網址、雜湊、下載限制及智財局資料開放宣告見 DATA_SOURCES。
- Known bugs / risks / blockers: 公報網站主要提供近期卷期。程式拒絕身份不符、改網域或無法讀出首頁識別的 PDF。人工評估、對外主機及完整遠端新版驗收仍待。
- Decisions made (ADR links): PDF 當作補充來源，保持 XML 引文來源與向量內容。前端連到智財局原件，暫無 PDF 轉送服務。
- Uncommitted changes / file ownership warnings: 驗收 PDF 與物件位於本機忽略目錄，正式資料庫未修改。
- Next 1–3 concrete actions: 核對新版完整官方 E2E，評估已確認的公告 PDF 案例及人工標註。
- Exact reproduction steps: 依 SETUP 執行 `gazette_pdf` 預覽，指定已驗證的公開版本 UUID 後重跑兩次，從專利詳情核對唯一 PDF 來源。

## 公開及公告公報 PDF 分版

- Date/time (timezone): 2026-11-27（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `codex/gemini-m6-integration`，起點 `ecbee6b`。
- Current milestone and status: 發明公告個案來源通過隔離 PDF 與瀏覽器驗收。掃描檔與全文搜尋仍待。
- Goal of this session: 支援發明公告 PDF，防止公告首頁出現公開號時將其連到公開版本。
- Files changed (with purpose): `services/ingestion/gazette_pdf.py` 加入公告官方資料來源與標頭校驗。`tests/test_gazette_pdf.py` 驗證階段與號碼拒絕。前端重開同案版本會重設來源摘要的展開狀態。
- Database migrations added/applied: 無。
- API/Schema changes: 無，沿用專利詳情既有來源契約。
- Commands actually run and results: pytest 134 passed，含 9 項 PostgreSQL 整合測試。Ruff、前端 lint、API 與前端正式映像建置通過。真實 `114106690` 附加公開與公告 PDF，公告重跑後保持一筆。資料庫拒絕將公告 PDF 附加至同案公開版本。Chromium、Firefox 與 WebKit 各驗證兩種 PDF 的網址、雜湊與既有 13 項請求項。Playwright 號碼查詢與同案切換 5 passed。
- Tests NOT run and reason: 此增量的遠端完整官方 E2E 尚待。起點的一般 CI 已通過，完整官方流程仍在執行。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-27 核對官方第 24 卷第 19 期公開 PDF 與第 53 卷第 28 期公告 PDF，政府網站資料開放宣告與檔案出處見 DATA_SOURCES。
- Known bugs / risks / blockers: 手動瀏覽器驗收首次發現切換版本沿用來源展開狀態，已更正。正式 E2E 首輪漏點「查詢同案其他版本」而逾時，修正後重跑。掃描辨識、其他專利種類、人工標註及對外部署尚待。
- Decisions made (ADR links): 公開與公告使用獨立來源資料集及同版本 XML 證據。只依首頁公報類型與標記過的版本號碼確認 PDF。
- Uncommitted changes / file ownership warnings: 官方 PDF 與測試資料僅存於隔離環境。
- Next 1–3 concrete actions: 核對最新整合 CI，接續防止來源漂移的驗收，取得人工標註與部署主機。
- Exact reproduction steps: 依 SETUP 對已匯入同案的公開、公告文件 UUID 執行 `--publication 202640162` 和 `--grant I941082`，再以號碼查詢切換兩版本。

## 官方公報 PDF 自動化驗收

- Date/time (timezone): 2026-11-27（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `codex/gemini-m6-integration`，起點 `dbfdc07`。
- Current milestone and status: 本機官方 PDF 品質關卡通過，完整交付仍進行中。
- Goal of this session: 建立可重跑的官方公報 PDF 與跨版本驗收。
- Files changed (with purpose): `scripts/smoke_gazette_pdfs.py`、官方工作流程與號碼查詢 E2E。操作指令加入 `--expected-sha256`，於寫入前確認固定原件。
- Database migrations added/applied: 無。
- API/Schema changes: 無。
- Commands actually run and results: 隔離 Compose 跑兩份真實 PDF，跨貼被拒、正確版本各重跑兩次仍保留一個 PDF 來源、兩版 XML 請求項未變。五組 Playwright 通過。pytest 126 passed、9 skipped，Ruff、前端 lint、TypeScript 與 Vite build 通過。提交 `698f747` 的[一般 CI](https://github.com/Johnnnny0823/RAG/actions/runs/45942011730)及[官方 PDF 來源模式](https://github.com/Johnnnny0823/RAG/actions/runs/45942027178)均通過。
- Tests NOT run and reason: 本輪本機 pytest 未啟用 PostgreSQL 套件，實際 Compose 及遠端一般 CI 已完成資料庫驗收。來源模式依設定跳過 Ollama。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-27 重抓第 024019／053028 期已核對的兩份個案 PDF，固定網址及雜湊見 DATA_SOURCES。
- Known bugs / risks / blockers: 智財局近期公報下載會受服務與卷期保存影響。若出處不符，須以官方證據更新測試。掃描辨識、PDF 全文索引、人工評估與公開主機尚待。
- Decisions made (ADR links): 遠端 PDF 驗收採 `gazette_pdf` 選用輸入，核心 XML 工作可獨立完成。
- Uncommitted changes / file ownership warnings: 測試寫入僅在現有隔離副本。
- Next 1–3 concrete actions: 核對完整官方 E2E，取得人工標註與部署主機。
- Exact reproduction steps: 依 TESTING 先啟動隔離 Compose 固定語料，再執行 `scripts.smoke_gazette_pdfs` 或觸發官方工作流程 `coverage=source` 與 `gazette_pdf=true`。
