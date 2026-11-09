# PatentScope AI

台灣專利研究平台的本機開發專案。M0 提供 React 狀態頁、FastAPI、PostgreSQL 16 與 pgvector；目前尚無已索引的專利語料。

## 啟動

需要 Docker Engine 或 Docker Desktop（Linux 容器模式）及 Docker Compose v2。在專案根目錄執行以下 PowerShell 指令。

```powershell
Copy-Item .env.example .env
docker compose up -d --build --wait --wait-timeout 180
python scripts/smoke.py
```

- [繁體中文狀態頁](http://127.0.0.1:5173)
- [OpenAPI 文件](http://127.0.0.1:8000/docs)

啟動順序為 PostgreSQL、Alembic、API、Web。Web 透過 Vite 代理存取同源 API。設定檔內的範例密碼僅供本機開發，請將實際值放在未追蹤的 `.env`。Compose 僅將 Web、API 綁定至本機，資料庫使用內部網路與命名卷。若修改連接埠，請將對應網址傳給 `scripts/smoke.py --api ... --web ...`。

```powershell
docker compose ps -a
docker compose run --rm migrate python -m alembic current
docker compose stop
```

要執行遷移，使用 `docker compose run --rm migrate`。第一個修訂只啟用 pgvector，降版保留擴充功能以保護可能已存在的物件。

## 本機檢查

建議使用 Python 3.12 與 Node.js 22.12+。

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m ruff format --check .
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m pytest -q
npm ci --prefix apps/web
npm run build --prefix apps/web
```

`npm run typecheck --prefix apps/web` 可單獨執行型別檢查。`pytest` 使用測試替身驗證 API 契約，`scripts/smoke.py` 驗證 Compose 網路上的 API、pgvector 和 Web 代理。GitHub Actions 設定包含這兩種檢查。

- [API 契約](docs/API.md)
- [環境安裝與排查](docs/SETUP.md)
- [架構決策](docs/DECISIONS.md)
- [里程碑進度](docs/PROGRESS.md)
- [交接紀錄](docs/HANDOFF.md)

## 檢索評估

在已匯入官方樣本、完成詞彙與向量索引並啟用本機重排序的 API 上執行。依 [環境安裝與排查](docs/SETUP.md) 啟動隔離語料服務，並將 `--api` 指向該服務。

```powershell
python scripts/evaluate_search.py --api http://127.0.0.1:18017 --repeats 2
python scripts/smoke_comparison.py --api http://127.0.0.1:18017
python scripts/evaluate_citations.py --api http://127.0.0.1:18017
```

種子集與分數解讀見 [檢索評估紀錄](docs/EVALUATION.md)。
