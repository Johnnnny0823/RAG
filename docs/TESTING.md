# 測試與驗收

每次功能變更先跑相關單元及 API 測試，再用隔離 Compose 專案與測試帳號驗證瀏覽器流程。不得將測試資料匯入正式索引。官方樣本的來源和重建方式見 [資料來源](DATA_SOURCES.md) 與 [環境設定](SETUP.md)。

```powershell
.venv/Scripts/python -m ruff format --check .
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m pytest -q
npm run lint --prefix apps/web
npm run build --prefix apps/web
```

| 檢查 | 執行方式 | 目前驗證範圍 |
| --- | --- | --- |
| HTTP 冒煙 | `python scripts/smoke.py --api <API> --web <Web>` | API 存活、資料庫就緒、同源代理與首頁。 |
| 真實資料回歸 | [SETUP](SETUP.md) 的匯入及 `verify_document` | 核對 XML、文件版本、請求項與說明書。 |
| 私人研究流程 | [Playwright CLI 驗收](SETUP.md#m4-瀏覽器驗收) | 帳號隔離、檢索、比對、保存、刪除及 PDF 下載。 |
| 評估 | [檢索評估](EVALUATION.md) | 三種檢索基線與引文完整性，人工評分待完成。 |
| 部署 | [靜態前端部署](SETUP.md#靜態前端部署) | 2026-11-09 以新資料卷驗證 Nginx、遷移、官方 XML 匯入、索引及瀏覽器下載。 |

測試失敗時先保留錯誤訊息與相關 API 回應、畫面、Trace 或服務日誌。修正後重跑失敗案例及相關回歸。同一根因最多自主修復三輪，仍失敗則記錄原因與復現步驟。只使用公開測試輸入及測試帳號，避免保存真實憑證或私人構想到除錯產物。

功能驗收需具備可執行的實作、前後端及資料庫整合、相關單元與 API 測試、可重跑的關鍵瀏覽器流程，以及 PROGRESS 和 HANDOFF 的實測紀錄。無法驗證的項目應標明待驗證。

## Playwright TypeScript 冒煙測試

在獨立 Compose 專案執行，使用專用連接埠及新 PostgreSQL 資料卷。案例自行註冊合成帳號及新增測試專案，正常完成時透過 UI 刪除。若中途失敗，合成資料可能留在測試卷中。

```powershell
npm ci --prefix apps/web
npm exec --prefix apps/web -- playwright install chromium
$env:WEB_PORT = "18124"
$env:API_PORT = "18024"
docker compose --env-file .env.example -p patentscope-e2e up -d --build --wait
$env:PATENTSCOPE_E2E_URL = "http://127.0.0.1:18124"
npm run test:e2e --prefix apps/web
docker compose --env-file .env.example -p patentscope-e2e stop
```

2026-11-10 在獨立新卷通過兩項 Chromium 案例（桌面與 Pixel 7 模擬），涵蓋 readiness、未登入 API 拒絕、註冊、登入／登出、專案新增／修改／重新登入讀取／刪除及帳號刪除。首次桌面測試因登出按鈕名稱不符而逾時，修正定位後兩項通過。請勿同時從同一工作目錄啟動兩次測試，兩次執行會共用產物路徑。

同一套件另以未註冊的隨機地址連續登入失敗 5 次，確認第 6 次回傳 429、帶 `Retry-After`，且畫面顯示節流訊息。這個案例不建立帳號，失敗紀錄 15 分鐘後失效。PostgreSQL 整合測試另驗證節流期間正確密碼被拒、其他帳號不受影響，以及紀錄逾期後可登入並清除。2026-11-10 在全新資料卷（遷移至 `0010_login_failures`）跑 Chromium 三種裝置共 12 項通過。

CI 已加入 Chromium 測試步驟，失敗時保存 HTML 報告、截圖、Trace 與瀏覽器錯誤附件七天。Trace 可能包含合成測試憑證，僅允許對獨立測試環境執行。GitHub Actions 遠端執行尚待驗證。真實專利檢索、證據和 PDF 可另行執行下節的 TypeScript 測試。

## 真實 TIPO 資料的 TypeScript 回歸

依 [SETUP](SETUP.md#靜態前端部署) 啟動專用 Compose 專案，匯入 24 卷 19 期索引與 `202639611` 全文，再建立詞彙與向量索引。確認模型設定含 embedding 和比對模型。官方下載指令與固定 SHA-256 見 [DATA_SOURCES](DATA_SOURCES.md) 及 [M1 樣本重現](SETUP.md#m1-官方樣本重現)。用 `verify_document 202639611` 核對原始物件和資料庫後，再執行：

```powershell
$env:PATENTSCOPE_E2E_URL = "http://127.0.0.1:18123"
$env:PATENTSCOPE_E2E_TIPO = "1"
.venv/Scripts/python -m pip install -r requirements-dev.txt
$env:PATENTSCOPE_TEST_PYTHON = (Resolve-Path .venv/Scripts/python.exe).Path
npm run test:e2e --prefix apps/web
Remove-Item Env:PATENTSCOPE_E2E_TIPO
```

2026-11-10 在已有官方樣本與本機 Qwen 的獨立部署驗證桌面及手機 Chromium，各通過一次。案例用公開的樹脂技術描述，確認混合檢索可保存、IPC／公開文件／申請人條件可用、詳情顯示官方資料集連結，且引文與同一文件版本的請求項、XPath、固定來源雜湊及 Unicode 字元區間吻合。PDF 驗證下載、檔名、媒體類型與私人快取標頭，並使用 pypdf 讀取下載檔，核對繁中標題、技術特徵、專利公開號、逐字引文、XPath、來源雜湊和官方連結註解。案例完成時刪除合成帳號及其資料。

GitHub Actions 可手動啟動 `Official patent E2E`，在獨立 Compose 網路內啟動 CPU Ollama、下載模型及固定官方樣本，再執行案例。遠端工作尚待驗證。以 Poppler 渲染桌面案例的兩頁並目視核對，繁中可讀，長雜湊有換行，證據延續到第二頁。Windows 若無法寫入 HTML 報告目錄，可先將 `PLAYWRIGHT_HTML_OUTPUT_DIR` 設為本次專用的可寫目錄。既有 CLI 驗收保留跨版本、Session、收藏、歷史與跨帳號隔離流程。

### 自動建立固定官方樣本

依 SETUP 設定兩個本機模型與其摘要，使用專用 Compose 專案和連接埠。種子腳本預設使用 `patentscope-tipo-e2e`，可用 `COMPOSE_PROJECT_NAME` 指定其他專案。它從官方 FTPS 取得 24 個檔案：第 24 卷第 19 期的 `index.xml`、`index_all.xml`、索引前 20 筆的個案說明書，以及第 53 卷第 28 期的公告封存索引。每個檔案的雜湊相符後才匯入。

匯入分三批：前 100 筆公開書目加 `202639611` 全文、前 20 筆的全文、公告 `I941082`。預期結果為 117 個文件版本，其中 17 份全文，3 份官方 XML 缺請求項編號而隔離。筆數不符時腳本會失敗，重跑時也會核對。接著從封存 XML 驗證 `202639611`、`202640162` 和 `I941082`，最後建立詞彙和向量索引。這份語料可執行 `PATENTSCOPE_E2E_TIPO=1` 與 `versions` 兩套案例。

建立索引後可獨立執行下列 API 驗收，並依實際連接埠調整 `--api`。官方 CI 在 Playwright 之前執行同一組命令。

```bash
python scripts/smoke_patents.py --official-e2e --api http://127.0.0.1:8000
python scripts/smoke_lexical.py --official-e2e --api http://127.0.0.1:8000
python scripts/smoke_semantic.py --official-e2e --api http://127.0.0.1:8000
```

此模式使用第 024019 期的光硬化樹脂及動態導通電阻案件，以及第 053028 期的公告。省略旗標則沿用舊雙期樣本，仍須匯入第 024018 期含 `202637274` 的書目。

```powershell
$env:API_PORT = "18025"
$env:WEB_PORT = "18125"
docker compose --env-file .env.example -p patentscope-tipo-e2e up -d --build --wait
.venv/Scripts/python -m scripts.seed_tipo_e2e .patent-data/tipo-e2e
$env:PATENTSCOPE_E2E_URL = "http://127.0.0.1:18125"
```

已有已驗證快取時可加 `--offline` 重跑，不會重新連到 TIPO。檔案雜湊錯誤會在匯入前失敗，保留原檔供排查。Docker Desktop 若無法掛載快取所在的磁碟（曾在 D: 槽遇到 `mkdir /run/desktop/mnt/host/d: file exists`），把快取目錄放到 C: 槽再加 `--offline` 重跑。

2026-11-10 在全新資料卷實測：下載與匯入約 4 分鐘，本機 GPU 建立 1,677 個詞彙片段與 1,624 個向量約 100 秒。離線重跑三批皆 `reused`，各表筆數不變。Chromium 桌面、平板與手機的 `versions` 套件 12 項、`@tipo` 套件 3 項通過。

### 研究歷史與平板

真實資料案例保存比對後會登出、重新載入頁面並登入，從歷史開啟相同搜尋。測試比對 API 重新讀取的文件 ID、判定和引文，展開原文定位，並驗證從重開的研究紀錄匯出的 PDF。兩套 E2E 均使用桌面、Pixel 7 與 iPad 第七代的 Chromium 模擬。Firefox 與 WebKit 見下節。

### Firefox 與 WebKit 相容性

先完成前述隔離環境設定，再安裝相應的 Playwright 瀏覽器。開啟下列旗標後，可用 `--project` 選擇瀏覽器。設定 `PATENTSCOPE_E2E_TIPO=1` 時執行官方資料流程，否則執行帳號與專案冒煙測試。

```powershell
npm exec --prefix apps/web -- playwright install firefox webkit
$env:PATENTSCOPE_E2E_CROSS_BROWSER = "1"
npm run test:e2e --prefix apps/web -- --project=desktop-firefox --project=desktop-webkit
Remove-Item Env:PATENTSCOPE_E2E_CROSS_BROWSER
```

一般 push／PR CI 保持 Chromium。手動 `Official patent E2E` 工作包含 Chromium、Firefox 與 WebKit。Windows 的 Playwright WebKit 結果只代表該引擎組態，macOS／iOS Safari 與實體裝置仍需另驗。

2026-11-10 在 Windows 隔離部署上，Firefox 與 WebKit 的帳號／專案冒煙測試及官方全文、引文、歷史與 PDF 驗收各通過一項，共 4 項。

### 同案公開與公告版本

用上節的 `seed_tipo_e2e` 建立語料並啟用本機模型。語料含公開 `202640162` 全文和公告 `I941082` 請求項。公告來源是官方 FTPS 的第 53 卷第 28 期封存索引，案例核對的雜湊是這份封存檔，見 [資料來源](DATA_SOURCES.md#公告期別的固定封存檔)。2026-11-09 以 S01 端點副本手動匯入的舊驗收庫雜湊不同，不適用此案例。

```powershell
$env:PATENTSCOPE_E2E_TIPO = "versions"
npm run test:e2e --prefix apps/web
Remove-Item Env:PATENTSCOPE_E2E_TIPO
```

測試在同一搜尋比對兩個版本，驗證申請號相同、文件 ID 相異、各版本請求項的引文範圍及來源雜湊正確，並檢查矩陣分欄呈現。

2026-11-10 桌面、平板及手機 Chromium 重跑共 3 項通過。首次手機案例等待比對回應逾時，已記錄於交接。

### 前端靜態檢查

`npm run lint --prefix apps/web` 檢查前端、Vite 設定及 Playwright TypeScript。使用 Oxlint 的正確性規則，並驗證 React Hooks 的呼叫位置及依賴清單。警告也會造成失敗。一般 push／PR CI 先執行 lint，再執行包含 TypeScript 型別檢查的正式建置。

### PostgreSQL 與 API 整合

下列指令從測試專案啟動 PostgreSQL 並套用 Alembic。測試要求回環位址和資料庫名稱 `patentscope_test`，使用合成帳號並透過帳號 API 清理。

```powershell
$env:POSTGRES_DB = "patentscope_test"
$env:PGPORT = "15433"
$compose = @("--env-file", ".env.example", "-f", "docker-compose.yml", "-f", "docker-compose.test.yml", "-p", "patentscope-pg-integration")
docker compose @compose up -d --wait db
docker compose @compose run --rm --build migrate
$env:PATENTSCOPE_PG_INTEGRATION = "1"
$env:PGHOST = "127.0.0.1"
$env:PGDATABASE = "patentscope_test"
$env:PGUSER = "patentscope_api"
$env:PGPASSWORD = "dev_api_only_change_me"
$env:PATENTSCOPE_PG_ADMIN_USER = "patentscope"
$env:PATENTSCOPE_PG_ADMIN_PASSWORD = "dev_only_change_me"
.venv/Scripts/python -m pytest -q tests/integration
docker compose @compose stop
```

CI 在空白測試資料卷套用遷移後執行此套件。測試驗證 Alembic head、pgvector 距離運算、真實 DB readiness、研究專案讀寫、另一帳號讀取遭拒，以及 PostgreSQL 拒絕跨帳號的搜尋紀錄外鍵。單獨執行整合套件時須設定上方旗標。

跑 PostgreSQL pytest 整合測試時，保持 Compose 的 `search-worker` 停止。測試會用真實資料庫、TestClient 和固定的檢索回應，驗證背景工作認領、跨帳號隔離、結果保存及執行中取消。執行官方 Playwright 前則要啟動工作程序，該套件使用真實檢索與模型。

整合測試用 API 角色連線，另用管理帳號查遷移版本並調整合成登入失敗時間。權限測試以交易及 savepoint 確認 PostgreSQL 拒絕 API 修改語料、建立持久資料表、讀取遷移版本。

### 搜尋失敗、空結果與逾時

在一般無模型的測試環境，`search-errors.spec.ts` 驗證空白搜尋按鈕停用、日期倒序回傳 422、模型未設定回傳 503，以及瀏覽器搜尋逾時後可保留輸入並重試。逾時案例只暫停一次網路請求並縮短該次用戶端計時，重試恢復實際等待時間且呼叫真實 API。

官方資料案例使用單筆固定語料，先用不相符的 IPC 條件驗證 200 與空結果訊息，再改回相符的條件進行保存、引文與 PDF 驗收。

2026-11-10 修正 WebKit 的逾時分類後，工作台與錯誤流程 15 項、官方資料流程 5 項通過。

### 檢索排序與分頁

`PATENTSCOPE_E2E_TIPO=versions` 也執行 `search-pagination.spec.ts`。此案例需要能以「動態導通電阻」取得超過 20 個真實候選的隔離語料。它以未啟用模型重排的混合檢索驗證 API 融合名次、畫面順序、跨頁文件 ID 去重，以及返回第一頁後的結果一致性。`seed_tipo_e2e` 建立的 117 個文件版本符合此條件。

同一配置也會以合成帳號保存一次搜尋、登出並重新登入，再從歷史開啟該紀錄。測試先比對保存當下及歷史重開取得的 API 候選與條件，再依保存的候選順序逐頁比對，確認末頁無下一頁、返回上一頁順序一致，且翻頁不再呼叫混合檢索。案例會清理合成帳號與其研究紀錄。

### 本機模型重排序

在含兩種官方文件版本且啟用本機分析模型的環境，以 `PATENTSCOPE_E2E_TIPO=versions` 執行 `search-rerank.spec.ts`。案例比較關閉與開啟重排時的文件 ID 集合，驗證模型版本、候選數及雜湊，並逐筆核對 API 重排名次和畫面順序。小語料中兩種排序可以一致，這項測試驗證重排流程與候選完整性。

### CPU 離線向量索引

CPU 環境可以縮小嵌入批量，避免單一推論超過等待上限：

```bash
python -m services.retrieval.index_semantic --batch-size 2 --request-timeout 180
python -m scripts.seed_tipo_e2e <cache> --embedding-batch-size 2 --embedding-timeout 180
```

批量範圍 1–24，等待範圍 1–1800 秒；預設仍是 24／90。不合法的 CLI 參數會在連線或下載前拒絕。這些旗標只影響離線索引，不改模型識別、向量內容、線上查詢預設或 SQL schema。已有完整文件索引會略過；一組文件的全部推論成功才進入寫入交易，推論中途失敗不會將該組部分向量公開。

`tests/test_semantic_index.py` 驗證分批、等待傳遞、參數範圍與第二批失敗時零寫入；`tests/test_embeddings.py` 驗證傳輸等待傳遞。2026-11-25 全套 57 passed、3 skipped；獨立 PostgreSQL 套件另 3 passed。第一次全套測試因 Windows 共用 pytest 暫存目錄存取遭拒，48 passed、3 skipped、4 errors；指定新的唯一 `--basetemp` 後重跑通過。保留一則既有 Starlette 棄用警告。

本機隔離模型使用固定 Ollama 映像、既有唯讀模型卷、2 CPU 與 4 GiB，未配置 GPU。兩段長 DEMO 文本（1000／960 字）產生 2 個 1024 維向量耗時 21.45 秒。官方 `202639611` XML 雜湊 `0537aedd633f9c63e7fe06790732cb0bf06e240e0bebf360c725abf9bc98d70a` 核對後解析為 19 請求項／122 段；取前兩段請求項（163／78 字）耗時 2.01 秒。此處未執行全量 CPU 索引、遠端 GitHub 官方 E2E 或新增瀏覽器回歸，不能外推為完整驗收。
