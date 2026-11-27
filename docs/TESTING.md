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
| 靜態部署 | `python scripts/smoke.py --api <Web> --web <Web> --deployment` | Nginx 編譯頁、同源 API、內容安全政策及瀏覽器安全標頭。官方遠端工作使用部署覆蓋檔後執行。 |
| 入口速率限制 | 在隔離部署的冒煙命令加上 `--deployment-rate-limit` | 使用空請求驗證兩個分組的 HTTP 429 和 JSON 錯誤契約，也驗證就緒與工作進度請求仍抵達 API。需從配額尚未用完的本機來源執行。 |
| HTTPS 部署 | `python scripts/smoke.py --api <HTTPS> --web <HTTPS> --deployment --ca-file <測試 CA 憑證>` | 驗證憑證與主機名稱、首頁、同源 API 及尾斜線重新導向。公開 CA 已在本機信任時可省略 `--ca-file`。 |
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

Gemini 整合分支新增原文定位驗收。此套件會核對引文屬於指定文件版本，再按「定位並標記原文」，核對 `<mark>` 內的文字。若只驗收工作台、API 錯誤與安裝資訊，使用開發前端及隔離 API，於 `apps/web` 執行 `node node_modules/@playwright/test/cli.js test workspace.spec.ts search-errors.spec.ts`。將 `PATENTSCOPE_E2E_CROSS_BROWSER` 設為 `1` 可另跑 Firefox、WebKit。

離線驗收使用正式 Nginx 映像。透過 Chromium 開啟首頁，等待 `navigator.serviceWorker.controller` 出現，再用同源 `fetch` 查詢語料狀態。確認 `patentscope-static-v1` 快取含 `/offline.html` 且沒有 `/api/` 項目。使該瀏覽器的測試環境離線後重新整理首頁，畫面應顯示「目前離線」。正式入口的 IP 限流冒煙與 API 登入限流案例使用不同階段，避免同一來源 IP 互相影響。

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

GitHub Actions 可手動啟動 `Official patent E2E`。預設 `coverage=full` 先驗收官方資料，再啟動獨立網路內的 CPU Ollama，執行向量、混合搜尋、比較證據與 PDF 瀏覽器測試。選擇 `coverage=source` 可單獨驗收靜態部署、來源雜湊、精確號碼、詞彙檢索及三種裝置的 Chromium 號碼查詢。這個模式不啟動 Ollama，也不驗證模型功能。以 Poppler 渲染桌面案例的兩頁並目視核對，繁中可讀，長雜湊有換行，證據延續到第二頁。Windows 若無法寫入 HTML 報告目錄，可先將 `PLAYWRIGHT_HTML_OUTPUT_DIR` 設為本次專用的可寫目錄。

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

### 新型與設計公告回歸

先依固定官方樣本驗證取得 `grant-053028.xml`。對獨立 Compose 專案掛載含該原檔的目錄至 `/inputs`，使用 `migrate` 容器執行 `python -m services.ingestion.import_issue --index /inputs/grant-053028.xml --index-source-url ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053028/index.xml --batch 053028 --grant-number M687984 --grant-number D246917 --verified-tipo`。重跑應回報 `reused: true`。再於同一專案執行 `python -m services.ingestion.verify_document <公告號> --grant-issue 053028`，分別驗證新型 16 項與設計 0 項請求項。要驗證詞彙檢索，匯入後重跑 `services.retrieval.index_lexical`。

將 `PATENTSCOPE_E2E_TIPO` 設為 `grant-types`，並設定隔離站的 `PATENTSCOPE_E2E_URL`，執行 `npm run test:e2e --prefix apps/web -- patent-number.spec.ts`。官方 GitHub Actions 在固定語料測試後加入這組案件，以保留各既有檢索測試的語料範圍。[來源與限制](DATA_SOURCES.md#同期新型與設計公告)

要驗證個案說明書，另準備[第 053030 期索引與全文清單](DATA_SOURCES.md#新型與設計個案說明書)，選取 `M688679`、`D247328`。依 [公告個案全文流程](SETUP.md#追蹤匯入及建立索引) 先匯入 S01 書目，再用同樣選案加上 `--manifest` 及 `--manifest-url` 匯入個案；使用先前下載快取時加 `--cache-only`。用 `verify_document <公告號> --grant-issue 053030 --grant-fulltext` 核對個案原件，並重跑詞彙索引。另設 `PATENTSCOPE_E2E_GRANT_FULLTEXT=1` 後，前述 Playwright 測試會核對新型 208 段、10 項請求項及設計 7 段、0 項請求項。

新型 `M688679` 個案的中英文摘要使用解析版 `tipo-issue-2`，重新匯入會建立獨立版本。`verify_document M688679 --grant-issue 053030 --grant-fulltext` 預設核對新版；舊版使用 `--parser-version tipo-issue-1`。前述個案 Playwright 也會核對新版顯示兩種語言的摘要。

語意與比對驗收使用一個全新的隔離資料庫，只匯入第 053030 期的 `M688679`、`D247328`，各保留一份 S01 及一份個案版，共四個版本。依 [模型設定](SETUP.md#m3-本機技術特徵驗收)設定本機 Qwen 嵌入及分析模型，依序執行詞彙、語意索引，再從主機執行下列命令。腳本核對改寫查詢在限定個案全文範圍的語意與混合順位、程式回查原檔雜湊，以及比對引文的 XPath 和 Unicode 字元區間。

```powershell
python scripts/smoke_grant_types_semantic.py --api http://127.0.0.1:18180
```

### 官方公告圖式回歸

以名稱獨立的 Compose 專案匯入第 053030 期 `M688679`、`D247328` 的 S01 與個案版本。匯入時使用 Compose 的 `PATENT_OBJECTS_DIR`，若重用已核對的下載快取，先將 `download-cache` 放入同一物件資料卷。圖式指令需指定個案版本 UUID、個案說明書 SHA-256、圖式 XML 序號及預期 JPEG SHA-256。固定樣本的值見 [圖式來源](DATA_SOURCES.md#新型與設計個案圖式)。

```powershell
python -m scripts.smoke_grant_drawings --api http://127.0.0.1:18181 --compose-project patentscope-official-drawings
$env:PATENTSCOPE_E2E_URL = 'http://127.0.0.1:18181'
$env:PATENTSCOPE_E2E_TIPO = 'grant-types'
$env:PATENTSCOPE_E2E_GRANT_DRAWINGS = '1'
$env:PATENTSCOPE_E2E_CROSS_BROWSER = '1'
npm run test:e2e --prefix apps/web -- patent-number.spec.ts
```

API 冒煙覆蓋錯版附加拒絕、官方取件、重跑去重、JPEG 原始位元校驗及跨版 404。瀏覽器驗證圖像實際解碼及同版 XPath 顯示。

### 設計 LOC 篩選回歸

在隔離庫匯入 `D246917`、`M687984` 的第 053028 期 S01 書目，依 [SETUP](SETUP.md#從官方公報書目補齊日期) 用同一期完整書目補入日期和 LOC。建立詞彙及向量索引，再以 `PATENTSCOPE_E2E_TIPO=loc` 執行 `npm run test:e2e --prefix apps/web -- gazette-dates.spec.ts`。案例輸入全形 `１３－９９`，確認候選、日期與詳情 LOC 顯示，改用 `00-00` 則呈現空結果。

隔離 API 驗收另以 `{"query":"載具","loc":"13-99"}` 跑詞彙、語意及混合檢索，三種模式皆回傳同一設計。保存搜尋後，回查 `request.loc` 並下載 PDF，驗證報告保留代碼 `13-99`。

### 衍生設計申請號回歸

依 [第 053028 期原件](DATA_SOURCES.md#原設計及衍生設計的編號與來源) 準備獨立庫，匯入 `--grant-number D246928 --grant-number D246929` 各一個 S01 與個案版本，再以 `gazette_dates --stage grant --year 115 --issue 053028 --include-other-grants` 核對日期和 LOC。使用 `grant_drawing` 對 `D246929` 的個案版本附加 `--figure 1`，個案 XML 和 JPEG 的 SHA-256 見資料來源。設定 `PATENTSCOPE_E2E_TIPO=derived-design`，執行 `npm run test:e2e --prefix apps/web -- patent-number.spec.ts`。案例比較原號與全形衍生號，確認各回傳兩個自身文件版本，並可開啟衍生設計說明書及圖式。

### 官方公報 PDF 回歸

以獨立 Compose 專案匯入上述固定官方語料後，可驗證同案的公開及公告 PDF。此測試先驗證錯版的附件請求在連線前遭拒。兩份 PDF 各實取一次，後續透過 `--replay-stored` 重跑，再用 API 核對去重及 XML 請求項來源。若智財局拒絕下載，首次取件關卡會依實際 HTTP 狀態回報失敗。

```powershell
python -m scripts.smoke_gazette_pdfs --api http://127.0.0.1:5173 --compose-project patentscope-tipo-e2e
$env:PATENTSCOPE_E2E_URL = "http://127.0.0.1:5173"
$env:PATENTSCOPE_E2E_TIPO = "versions"
$env:PATENTSCOPE_E2E_GAZETTE_PDFS = "1"
npm run test:e2e --prefix apps/web -- patent-number.spec.ts
```

遠端可在 `Official patent E2E` 選擇 `gazette_pdf=true`。搭配 `coverage=source` 可在未啟動 Ollama 的情況下驗收兩筆固定 PDF。核對時在資料寫入前要求 SHA-256 相符。API 測試查驗版本、頁碼、首頁文字與跨版 404，瀏覽器測試以證書號定位公告首頁。個案若已下架或內容變更，選用的 PDF 測試會失敗並須重查官方來源。核心 XML 套件預設維持獨立執行。

2026-11-27 以 Windows Docker Desktop 的新 Compose 專案從空白資料庫遷移到 `0021_gazette_pdf_search`。`seed_tipo_e2e --offline --skip-semantic` 核對 24 件先前保存的官方 XML，再重建 117 個官方版本及 1,560 個詞彙索引片段。`smoke_gazette_pdfs` 隨後從智財局首次下載兩份 PDF、核對錯版與原始 XML，並實跑離線回填及 PDF 詞彙檢索。Chromium 桌面／平板／手機、Firefox 及 WebKit 共五項號碼查詢測試通過。要加跑 Firefox 與 WebKit，請設定 `PATENTSCOPE_E2E_CROSS_BROWSER=1`。

若 Docker Desktop 無法掛載 `D:` 的樣本目錄，可把固定 XML 快取複製到 `$env:TEMP` 內另一個資料夾，再以 `--offline --skip-semantic` 驗證及匯入。上述本機驗收與 GitHub runner 的 [HTTP 403](https://github.com/Johnnnny0823/RAG/actions/runs/45972249350)是不同環境的取件結果。

### 公報日期與增量索引

需要驗收日期時，另外執行 [公報書目日期補齊](SETUP.md#從官方公報書目補齊日期)。使用 `GET /api/v1/patents?number_type=publication&number=202639611` 與 `number_type=grant&number=I941082` 核對日期。混合檢索以 `ipc=C08F2/48`、查詢 `photocurable resin composition` 及起迄皆 `2026-10-01` 應可查到公開案。把起迄一起設為 `2026-10-02` 時，固定語料應回傳空清單。

第 024020 期的增量驗收先匯入 [最新卷期書目及兩份全文](SETUP.md#更新最新發明公開書目)，再用已設定的模型補建向量。以下指令使用該期的固定已知案件，與 S10 當下回傳的卷期無關。語意測試使用改寫查詢與 IPC 條件，並檢查混合檢索合併同公開號。引文評估核對版本、字元位置、原文及來源雜湊。

```powershell
python scripts/smoke_semantic.py --issue-024020 --api http://127.0.0.1:18152
python scripts/evaluate_citations.py --issue-024020 --api http://127.0.0.1:18152
```

第 053030 期的公告內容篩選驗收需同時匯入 `I942741`、`I942850` 的 S01 請求項版及官方個案全文版，並建立兩種索引。執行 `python scripts/smoke_grant_versions.py --api http://127.0.0.1:18152`，檢查兩種文件內容各自的詞彙、語意、混合檢索，以及全文版引文是否回到該版本原文。

```powershell
$env:PATENTSCOPE_E2E_URL = "http://127.0.0.1:18125"
$env:PATENTSCOPE_E2E_TIPO = "dates"
npm run test:e2e --prefix apps/web
```

日期套件會驗證搜尋結果摘要、申請人、公開日、IPC、官方資料集連結、相關原因、詳情申請日及日期原始檔。若同時要跑原先的全官方瀏覽器案例，使用尚未補齊日期的隔離語料執行該套件，以保留空日期欄位驗收。手動升級已存的測試庫後，須依 Compose 的 migrate 指令配置 API 角色權限。

異動公報套件使用擴充至前 500 筆書目的隔離語料。先依 [匯入官方異動公報](SETUP.md#匯入官方異動公報) 準備 `I874215` 公告及第 53 卷第 33 期的 `sud24`、`sud08`，將 `PATENTSCOPE_E2E_TIPO` 設為 `events` 再執行 Playwright。案例在公開案 `202639186` 核對更正公報，在公告案 `I874215` 核對消滅日期、原因、原檔定位及雜湊。

也可先匯入兩個案件，再用[異動公報排程](SETUP.md#最新異動公報定期更新)建立事件。模型未設定時，可從 `apps/web` 執行 `node node_modules/@playwright/test/cli.js test legal-events.spec.ts --grep 'identifier lookup'`，用專利號碼直接驗證兩件的日期或異動欄位、卷期、原檔連結及雜湊。其餘兩項測試透過自然語言搜尋，需要已設定嵌入模型與向量索引。

```powershell
$env:API_PORT = "18025"
$env:WEB_PORT = "18125"
docker compose --env-file .env.example -p patentscope-tipo-e2e up -d --build --wait
.venv/Scripts/python -m scripts.seed_tipo_e2e .patent-data/tipo-e2e
$env:PATENTSCOPE_E2E_URL = "http://127.0.0.1:18125"
```

已有已驗證快取時可加 `--offline` 重跑，不會重新連到 TIPO。檔案雜湊錯誤會在匯入前失敗，保留原檔供排查。Docker Desktop 若無法掛載快取所在的磁碟（曾在 D: 槽遇到 `mkdir /run/desktop/mnt/host/d: file exists`），把快取目錄放到 C: 槽再加 `--offline` 重跑。

官方遠端工作分開顯示固定資料準備、匯入和原文校驗、向量索引的結果。第一段 `--prepare-only` 逐檔列出進度並核對 24 項 SHA-256，完成後才保存快取。快取限公開 XML 與公開下載檔，不包含資料庫、帳號、構想、模型或測試產物。後續執行會再次核對每個檔案，接著用 `--offline --skip-semantic` 匯入、驗證原文及建立詞彙索引，最後由獨立步驟建立向量索引。

遠端官方工作 [45669425487](https://github.com/Johnnnny0823/RAG/actions/runs/45669425487) 在準備語料時收到 TIPO FTPS 暫時錯誤 425，未開始 API 和 Playwright 驗收。下載器現在遇到 425 時，分別等待 15、45 秒再開立新連線，合計最多三次。其他 FTP 錯誤及資料驗證錯誤維持原本的回報，成功下載的固定樣本仍須通過 SHA-256 核對。

2026-11-10 在全新資料卷實測：下載與匯入約 4 分鐘，本機 GPU 建立 1,677 個詞彙片段與 1,624 個向量約 100 秒。離線重跑三批皆 `reused`，各表筆數不變。Chromium 桌面、平板與手機的 `versions` 套件 12 項、`@tipo` 套件 3 項通過。

### 研究歷史與平板

真實資料案例保存比對後會登出、重新載入頁面並登入，從歷史開啟相同搜尋。測試比對 API 重新讀取的文件 ID、判定、引文及搜尋涵蓋範圍，展開原文定位，並驗證從重開的研究紀錄匯出的 PDF 含兩種索引的版本數。無符合篩選的官方案例同時核對兩種索引的計數為零。兩套 E2E 均使用桌面、Pixel 7 與 iPad 第七代的 Chromium 模擬。Firefox 與 WebKit 見下節。

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

`versions` 套件也包含 `patent-number.spec.ts`，可用 Playwright 的 `--grep=official.identifier.lookup` 單獨執行。以申請號 `114106690` 開啟同案公開全文、公開書目及公告請求項，並驗證全形公開號、小寫公告號、查無資料及無效格式。此案例只呼叫專利資料 API，可在沒有設定模型服務的隔離環境驗證。

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

### 部署版 PWA 離線驗收

啟動隔離的正式 Nginx 前端與 API 後，在 `apps/web` 執行下列命令。連接埠依隔離環境調整，Firefox 與 WebKit 需先安裝對應 Playwright 瀏覽器。

```powershell
$env:PATENTSCOPE_E2E_URL = "http://127.0.0.1:18166"
$env:PATENTSCOPE_E2E_DEPLOY = "1"
$env:PATENTSCOPE_E2E_CROSS_BROWSER = "1"
npx playwright test --reporter=list
```

2026-11-27 通過 5 項，涵蓋桌面、平板與手機 Chromium，以及桌面 Firefox 與 WebKit。測試連線時核對語料狀態 API 由網路回應，斷線時核對提示與 API 無法讀取，恢復後再次取得 200。官方來源工作流程在啟動正式映像後先跑桌面 Chromium，再匯入官方語料。

部署冒煙的 `--deployment` 也會驗證 manifest 的媒體類型與作用範圍、Service Worker 的腳本媒體類型與快取政策，以及離線頁。完整官方工作流程在向量索引及語意 API 驗收後，再以 `--require-official-index` 檢查公開語料狀態。測試站若同時驗收限流，會在觸發限流前查詢語料狀態。
