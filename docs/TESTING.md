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

現有 CI 已設定 Python 檢查、前端型別與建置、Compose 及 HTTP 冒煙。正式 Playwright TypeScript 測試套件、CI 瀏覽器除錯產物、前端 lint、Firefox 和 WebKit 尚待驗證或補齊。
