# 測試與驗收

每次功能變更先跑相關單元及 API 測試，再用隔離 Compose 專案與測試帳號驗證瀏覽器流程。不得將測試資料匯入正式索引。官方樣本的來源和重建方式見 [資料來源](DATA_SOURCES.md) 與 [環境設定](SETUP.md)。

```powershell
.venv/Scripts/python -m ruff format --check .
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m pytest -q
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

CI 已加入 Chromium 測試步驟，失敗時保存 HTML 報告、截圖、Trace 與瀏覽器錯誤附件七天。Trace 可能包含合成測試憑證，僅允許對獨立測試環境執行。GitHub Actions 遠端執行、Firefox、WebKit、平板與前端 lint 尚待驗證或補齊。真實專利檢索、證據和 PDF 可另行執行下節的 TypeScript 測試。

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

這個案例尚未納入遠端 Actions，該環境目前未準備官方樣本與本機模型。以 Poppler 渲染桌面案例的兩頁並目視核對，繁中可讀，長雜湊有換行，證據延續到第二頁。Windows 若無法寫入 HTML 報告目錄，可先將 `PLAYWRIGHT_HTML_OUTPUT_DIR` 設為本次專用的可寫目錄。既有 CLI 驗收保留跨版本、Session、收藏、歷史與跨帳號隔離流程。
