# API 契約

開發環境提供 [Swagger UI](http://127.0.0.1:8000/docs) 與 [OpenAPI JSON](http://127.0.0.1:8000/openapi.json)。

| 方法 | 路徑 | 結果 |
| --- | --- | --- |
| GET | `/api/v1/health` | HTTP 200，`{"status":"ok"}`。獨立於資料庫。 |
| GET | `/api/v1/ready` | 成功執行 PostgreSQL 向量距離查詢時回傳 HTTP 200，`{"status":"ready"}`。連線或查詢失敗時回傳 HTTP 503。 |

HTTP 503 回應使用 `error.code`（`DATABASE_UNAVAILABLE`）、`error.message`（繁體中文）及 `error.request_id`（UUID）。就緒回應設為 `Cache-Control: no-store`。API 日誌僅記錄失敗類型與請求識別碼。
