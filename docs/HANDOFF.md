# Agent Handoff

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
