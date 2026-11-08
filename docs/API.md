# API 契約

開發環境提供 [Swagger UI](http://127.0.0.1:8000/docs) 與 [OpenAPI JSON](http://127.0.0.1:8000/openapi.json)。

| 方法 | 路徑 | 結果 |
| --- | --- | --- |
| GET | `/api/v1/health` | HTTP 200，`{"status":"ok"}`。獨立於資料庫。 |
| GET | `/api/v1/ready` | 成功執行 PostgreSQL 向量距離查詢時回傳 HTTP 200，`{"status":"ready"}`。連線或查詢失敗時回傳 HTTP 503。 |

HTTP 503 回應使用 `error.code`（`DATABASE_UNAVAILABLE`）、`error.message`（繁體中文）及 `error.request_id`（UUID）。就緒回應設為 `Cache-Control: no-store`。API 日誌僅記錄失敗類型與請求識別碼。

## 專利精確查詢與文件版本

| 方法 | 路徑 | 結果 |
| --- | --- | --- |
| GET | `/api/v1/patents?number=114106690&number_type=application` | 依指定號碼類型精確查詢。回傳 `items`、`limit`、`offset`、`has_more`。 |
| GET | `/api/v1/patents/{document_id}` | 指定文件版本的書目、摘要、申請人、發明人、IPC、說明書段落與來源。 |
| GET | `/api/v1/patents/{document_id}/claims` | 同一文件版本的請求項，依編號排序，包含可取得的獨立項標記及原文定位。 |

`number_type` 必填，支援 `application`（9 位數申請號）、`publication`（9 位數發明公開號）及 `grant`（目前語料支援 I 開頭的發明公告號）。輸入做全半形與大小寫正規化，保留前導零。分頁預設 `limit=20`、`offset=0`，上限分別為 100 與 10,000。同一號碼的不同文件版本可並存，全文版本排在同一文件的書目版本之前。

來源包含資料集、提供機關、授權、批次、匯入時間、原始 XML 雜湊與 XPath。已保存且通過官方來源檢查的原檔 URL 才會回傳。缺少日期、kind code 或原檔 URL 時回傳 `null`。`content_scope` 區分 `metadata_and_abstract`、`claims_only` 和 `fulltext`。請求項的從屬關係與可下載附件留待後續階段。

查無相符號碼時回傳 HTTP 200 與空清單；未知文件版本回傳 404。格式或參數錯誤為 422，資料庫不可查詢為 503。錯誤均使用 `error.code`、`error.message` 和 `error.request_id`。

## 詞彙檢索

`POST /api/v1/patents/search` 接受 JSON，例如 `{"query":"動態導通電阻","ipc":"G01R","limit":20,"offset":0}`。查詢為 1–160 字元。`ipc` 可省略，四碼子類採前綴比對，完整分類符號採精確比對，支援全半形正規化。回傳 `items`、`tokenizer_version`、`limit`、`offset`、`has_more`。

每個結果包含文件版本欄位及詞彙排序分數 `score`。分數用於同一查詢的排序。搜尋以正文片段為單位，查詢詞須出現在同一標題、摘要、請求項或說明書段落中。重複匹配片段彙整至同一文件版本。查詢正文不寫入資料庫。語料匯入後需執行詞彙索引更新，見 [SETUP.md](SETUP.md)。

## 語意檢索

`POST /api/v1/patents/search/semantic` 使用與詞彙檢索相同的請求欄位。回傳文件版本、模型名稱、權重 SHA-256、處理流程版本及分頁。先依正式語料與 IPC 篩選，再以各文件片段的最高餘弦相似度排序。分數用於檢索排序。

語意查詢正文只傳送到管理者設定的本機 Ollama，應用程式不保存正文。模型服務未設定或不可用時回傳 503 `EMBEDDING_UNAVAILABLE`，設定模型尚無索引時回傳 503 `SEMANTIC_INDEX_UNAVAILABLE`。
