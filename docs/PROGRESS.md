# 開發進度

| 里程碑 | 狀態 | 證據 |
| --- | --- | --- |
| M0 專案與基礎契約 | DONE | 2026-11-09，全新暫存工作副本與獨立資料卷通過 Compose 建置、Alembic 遷移和 [HTTP 冒煙測試](../scripts/smoke.py)。[API 測試](../tests/test_health.py) 4 項通過。 |
| M1 TIPO 資料匯入 PoC | NOT_STARTED | 待核對官方資料集、授權、樣本與欄位。 |
| M2 基礎檢索 | NOT_STARTED | 依賴 M1 建立真實語料。 |
| M3 混合檢索與可解釋性 | NOT_STARTED | 依賴基礎檢索及來源定位。 |
| M4 研究介面 | NOT_STARTED | M0 的狀態頁只顯示本機服務狀態。 |
| M5 評估、隱私與報告 | NOT_STARTED | 待建立人工相關性標註與可重現評估。 |
| M6 延伸功能 | NOT_STARTED | MVP 之後再評估。 |

## M0 驗收紀錄

- PostgreSQL 16.14、pgvector 0.8.2、Alembic head `0001_enable_vector` 已在本機查證。
- Ruff 格式及 lint 通過。前端 TypeScript 型別檢查、Vite 編譯和 npm audit 通過。
- 實際停止本機 DB 後，存活端點仍回應 HTTP 200，就緒端點透過 Web 代理回應 HTTP 503。瀏覽器確認載入中、資料庫無法使用及重試後就緒三種狀態。
- GitHub Actions 工作流程已建立，遠端執行紀錄待首次推送。工具警告、重現方式與 M1 待辦見 [交接紀錄](HANDOFF.md)。
