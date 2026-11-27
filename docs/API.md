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

`number_type` 必填，支援 `application`（9 位數申請號，或設計號加 `D01` 至 `D99` 的衍生設計案號）、`publication`（9 位數發明公開號）及 `grant`（I 為發明、M 為新型、D 為設計）。輸入做全半形與大小寫正規化，保留前導零與衍生尾碼。申請號採完整精確比對，查原設計 `114302318` 及衍生設計 `114302318D01` 分別回傳各自版本。分頁預設 `limit=20`、`offset=0`，上限分別為 100 與 10,000。同一號碼的不同文件版本可並存，全文版本排在同一文件的書目版本之前。S01 設計書目仍回傳 `metadata_and_abstract`，來源無摘要時為 `null`，請求項回傳空陣列。

來源包含資料集、提供機關、授權、批次、匯入時間、原檔雜湊及檔內位置。已保存且通過官方來源檢查的原檔 URL 才會回傳。缺少日期、kind code 或原檔 URL 時回傳 `null`。`content_scope` 區分 `metadata_and_abstract`、`claims_only` 和 `fulltext`。已核對並附加的官方公報 PDF 可從其來源 URL 開啟，專利詳情亦提供同版本的頁面文字 API。[公報 PDF](#官方公報-pdf-頁面文字)

已驗證的新型個案摘要同時提供 `abstract_zh`／`abstract_en` 預覽，以及 `sections` 內帶 `abstract-zh`／`abstract-en` 類型的原文、XPath 與原檔雜湊。比對可引用該摘要段落。既有書目來源的摘要仍維持原有欄位。

同版官方圖式列於 `sources`，位置形如 `/specification/drawings/figure[3]/img[1]`，並提供官方 FTPS 位址及圖檔雜湊。`GET /api/v1/patents/{document_id}/drawings/{artifact_sha256}` 驗證版本和物件後回傳 `image/jpeg`。錯版或未知雜湊回傳 404，已登錄但物件缺失或毀損時回傳 503。[圖式來源與範圍](DATA_SOURCES.md#新型與設計個案圖式)

詳情的 `legal_events` 列出同一申請案已匯入的官方異動公報。事件支援發明、新型與設計。新型及設計須先有同一申請案及證書號的公告版本才能連結。所有公告版本仍須符合事件的證書號。事件種類目前有 `extinguishment`（消滅公告）與 `gazette_correction`（公報更正），並提供證書號、卷期、匯入時間、已知生效日、來源、雜湊及定位。`effective_on` 僅在來源提供時有值。空陣列表示已匯入語料沒有該案的事件，最新權利狀態仍應查智慧財產局。

查無相符號碼時回傳 HTTP 200 與空清單；未知文件版本回傳 404。格式或參數錯誤為 422，資料庫不可查詢為 503。錯誤均使用 `error.code`、`error.message` 和 `error.request_id`。

## 詞彙檢索

詞彙、語意與混合檢索可選填 `content_scope`。可用值為 `fulltext`（全文）、`claims_only`（書目與請求項）和 `metadata_and_abstract`（書目與摘要）。條件和 `document_stage` 可一同使用，例如查公告全文。混合結果的索引涵蓋筆數也使用同一篩選。已保存搜尋會記錄此欄位，PDF 將列出選用的內容範圍。

詞彙、語意與混合檢索共用選填欄位 `published_from`、`published_to`、`document_stage`、`applicant` 及 `ipc`。日期以 ISO 日曆日期表示，含起迄日，指定任何日期界線時排除日期未知的版本。文件階段接受 `publication` 或 `grant`。申請人以已匯入中英文名稱做不分大小寫的文字子字串比對，萬用字元視為一般文字。混合檢索先套用條件再產生分支順位，保存搜尋會一起保存條件。

`loc` 可選填設計專利的完整 Locarno 代碼（例如 `13-99`，接受全形字元正規化）。三種檢索套用相同的精確分類條件，混合候選以 `loc_codes` 顯示已取得的代碼。可與日期及其他條件併用，保存搜尋和 PDF 也會保留此條件。LOC 與 IPC 使用獨立資料分類。

`POST /api/v1/patents/search` 接受 JSON，例如 `{"query":"動態導通電阻","ipc":"G01R","limit":20,"offset":0}`。查詢為 1–160 字元。`ipc` 可省略，四碼子類採前綴比對，完整分類符號採精確比對，支援全半形正規化。回傳 `items`、`tokenizer_version`、`limit`、`offset`、`has_more`。

每個結果包含文件版本欄位及詞彙排序分數 `score`。分數用於同一查詢的排序。搜尋以正文片段為單位，查詢詞須出現在同一標題、摘要、請求項或說明書段落中。重複匹配片段彙整至同一文件版本。查詢正文不寫入資料庫。語料匯入後需執行詞彙索引更新，見 [SETUP.md](SETUP.md)。

## 語意檢索

`POST /api/v1/patents/search/semantic` 使用與詞彙檢索相同的請求欄位。回傳文件版本、模型名稱、權重 SHA-256、處理流程版本及分頁。先依正式語料與 IPC 篩選，再以各文件片段的最高餘弦相似度排序。分數用於檢索排序。

語意查詢正文只傳送到管理者設定的本機 Ollama，應用程式不保存正文。模型服務未設定或不可用時回傳 503 `EMBEDDING_UNAVAILABLE`，設定模型尚無索引時回傳 503 `SEMANTIC_INDEX_UNAVAILABLE`。

線上嵌入、特徵拆解、重排及技術比對共用推論名額，保存搜尋與 Session 等操作也適用。當模型工作已滿，新的推論立即回傳 HTTP 429 `MODEL_BUSY`、`Retry-After: 5` 與 `Cache-Control: no-store`。取得名額的操作結束或失敗後會釋出名額。純詞彙檢索及不需模型的比對不占名額。

透過正式 Nginx 時，超過來源 IP 配額的帳號及研究請求另回傳 HTTP 429 `RATE_LIMITED`、`Retry-After: 2` 及 `Cache-Control: no-store`。API 原有的 `LOGIN_THROTTLED` 和 `MODEL_BUSY` 仍會透過代理回傳。

## 混合檢索

`POST /api/v1/patents/search/hybrid` 沿用詞彙檢索的 JSON 欄位，構想描述上限為 1,200 字元。兩個檢索分支各取最多 100 個文件版本，在同一資料庫快照查詢。回傳 `rrf_k`、`candidate_limit`、`query_expansion_version`、分詞器與嵌入模型版本，以及每筆的 `lexical_rank`、`lexical_score`、`semantic_rank`、`semantic_score` 和 `rrf_score`。某版本未進入分支候選時，該分支欄位為 `null`。

`corpus_coverage` 在同一讀取交易記錄 `observed_at`、`lexical_versions`、`semantic_versions` 與 `latest_document_date`。計數涵蓋符合 IPC、日期、文件類型及申請人篩選的官方文件版本，於關鍵字比對、候選上限及分頁之前計算。詞彙計入目前分詞版本具可檢索詞的文件，向量計入目前模型及索引版本已有向量的文件。兩個計數可能包含相同版本。日期取兩種索引涵蓋文件中已知的最晚文件日期，缺日期時回傳 `null`。保存後可從 `settings.corpus_coverage` 重讀，既有紀錄可缺此欄位。

`sentence-expansion-v2` 將逾 160 字的描述依句段分組，各句段與使用者確認的檢索詞分別參與全文檢索。語意檢索保留完整原描述，並附上特徵描述。短查詢可繼續附帶展開詞；當短查詢的展開內容超過 1,600 字，改用完整原描述及特徵描述，展開詞仍參與全文檢索。保存搜尋時保留原描述及查詢展開版本。

按文件版本 UUID 融合，再依文件階段、公開或公告號及 kind code 去重。同一申請案的公開和公告可同時呈現。分頁套用在融合後的候選集合。模型服務或索引不可用時，錯誤行為與語意檢索一致。此端點不保存查詢或排名。

每筆混合候選附同一文件版本的 `abstract_excerpt`（最多 240 字元）、`applicants`、`ipc_codes`（最多四項）與 `official_source_url`（通過來源網址驗證的官方資料集頁）。缺少資料時回傳空值或空陣列。搜尋保存會保留當時的呈現資料；舊版保存紀錄仍可閱讀，並可開啟詳細資料。

`lexical_match_fields` 列出同一候選版本中符合詞彙查詢的索引欄位，例如 `title_en`、`abstract_zh`、`claim`、`section:disclosure`。前端依文字欄位與檢索順位說明候選的來源，重排理由只出現在有重排名次的候選。語意順位表達此版本在索引候選中的相對位置，技術特徵是否相符仍由證據比對判定。

### 官方公報 PDF 頁面文字

`GET /api/v1/patents/{document_id}/gazette-pdfs/{artifact_sha256}/pages` 回傳目前文件版本已附加的官方 PDF 文字層。回應帶版本 UUID、PDF 雜湊及依原始頁碼排序的 `pages`，各頁含 `page_number` 與 `extracted_text`。查詢其他版本的 PDF 回傳 404。既有附件尚未擷取文字時回傳空陣列，重跑原件匯入可補齊。詳情在瀏覽器內查找這些文字，原文對照可開啟同一份官方 PDF。

`POST /api/v1/patents/gazette-pdfs/search` 接受 `query`（最多 120 字）、選填 `document_stage`、`limit`（預設 20，上限 100）及 `offset`（預設 0，上限 10,000）。各斷詞必須出現在同一頁。結果依詞彙相關性排序，同分按文件與頁碼排序，並附分頁欄位及官方來源。工作台翻頁沿用上次成功送出的關鍵詞及階段。

混合請求可加 `"rerank":true`，由本機分析模型根據標題與摘要重排融合後的前 8 筆候選。回傳原 `fusion_rank`、`rerank_rank` 及重排模型資訊。未啟用、候選少於兩筆或在重排範圍外時，對應欄位為 `null`。重排版本 `ollama-listwise-v2` 會依候選數量限定模型輸出的編號與陣列長度。後端獨立驗證每個候選恰好出現一次，驗證失敗回傳 503。分頁在重排後套用，跨請求的排序尚無持久化快照。

## 技術特徵拆解與編輯

`POST /api/v1/queries/analyze` 接受 `{"query":"發明構想"}`（1–1,200 字元）。回傳至多 5 個技術特徵，以及模型名稱、權重 SHA-256 與分析版本。特徵包含 `feature_id`、繁中描述、繁中和英文檢索詞、必要條件標記、提取把握及 IPC 候選。

呼叫端可以編輯或刪除草稿特徵，再將已確認的 `features` 陣列連同原始 `query` 傳給混合檢索。每個特徵 ID 須唯一，回傳 `applied_feature_ids`。詞彙分支對原始查詢及已確認詞組取聯集，詞組內須全部命中。向量分支附加特徵描述與檢索詞，展開上限 1,600 字元。IPC 候選供檢視，真正的 IPC 篩選由獨立的 `ipc` 欄位控制。必要條件標記及提取把握供後續比對，目前不參與硬篩選或排序。

分析模型未設定、無法連線或回應未通過結構驗證時回傳 503 `ANALYSIS_UNAVAILABLE`。兩個端點目前均不保存正文。
## 文件版本技術比對預覽

`POST /api/v1/patents/{document_id}/compare` 接受 1–5 項已確認的 `features`。先在指定版本的請求項與說明書找出字詞命中，再對未命中的特徵查詢同版本的向量索引。每項特徵至多選一段原文供本機模型判定。預設啟用語意候選，直接呼叫可傳 `semantic_evidence: false` 進行純字詞基準測試。

回傳 `supported`、`partially_supported`、`uncertain` 或 `not_found_in_checked_content`，後者表示在指定範圍內未取得可提交判定的片段。只有書目的版本回傳不確定。若沒有相容索引或嵌入模型暫時無法使用，系統保留字詞比對並在判定依據中揭露語意候選狀態。

`GET /api/v1/patents/{document_id}/claims` 的 `referenced_claim_numbers` 列出正文中可核對的同版本援引項。支援明確的單項、列舉與區間表述。空陣列表示未擷取到符合規則的援引。`independent` 照錄來源 XML 標記，可能和正文中的援引並存。

引文由後端從保存的原文擷取，附原檔 SHA-256、XPath、段落或請求項序號，以及以 Unicode 字元計算的起訖位置（終點不包含）。`evidence_method` 標示候選來自字詞或語意檢索，`evidence_embedding_digest` 記錄用於語意候選的模型摘要。回傳也保留文件版本及判定模型識別。本預覽不保存構想或判定。

## 私人搜尋紀錄

| 方法 | 路徑 | 行為 |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | 以 `email` 及 12–128 字元的 `password` 建立帳號，回傳 201。重複帳號回傳 409。 |
| POST | `/api/v1/auth/login` | 以相同欄位取得有效期 24 小時的 Bearer token。帳密不符回傳 401。同一電子郵件在 15 分鐘內失敗 5 次後回傳 429 `LOGIN_THROTTLED` 與 `Retry-After` 秒數，期間正確密碼也會被拒；登入成功會清除該地址的失敗紀錄。 |
| POST | `/api/v1/auth/logout` | 撤銷請求提供的 Bearer token，回傳 204。重送同一憑證也回傳 204。 |
| GET | `/api/v1/me` | 回傳目前帳號。 |
| DELETE | `/api/v1/me` | 提供 Bearer token 與 JSON `{"password":"…"}`，重新核對密碼後刪除帳號及伺服器端私人研究資料，回傳 204。密碼不符回傳 403。 |
| POST | `/api/v1/search-runs` | 接受混合檢索的請求格式。同步執行並保存後回傳 201、紀錄 UUID 和建立時間。 |
| GET | `/api/v1/search-runs` | 分頁列出目前帳號的紀錄 UUID 與時間，接受 `limit`、`offset`。 |
| GET | `/api/v1/search-runs/{run_id}` | 回傳原始請求、排序設定、候選集合及已保存的比對。 |
| POST | `/api/v1/search-runs/{run_id}/comparisons/{document_id}` | 使用紀錄中的已確認特徵比對指定候選版本。重送回傳第一次保存的結果。 |

`/me` 與紀錄端點使用 `Authorization: Bearer <token>`。無效憑證為 401，跨帳號或未知紀錄及候選為 404，未保存特徵的比對為 422。保存端點存下有上限的完整候選集合，詳情可讀取原始分支、融合與重排順位。範圍涵蓋該次返回的結果，尚無完整語料快照及重跑機制。比對與檢索預覽仍可獨立使用。
## 研究專案與歸檔

`GET /api/v1/me/export` 需要 Bearer token。它會以 `patentscope-research.json` 附件下載同一時間點的帳號資料、專案、收藏及筆記、已保存搜尋與候選、技術比對、Session 及訊息。回應含 `format_version: 1`、`exported_at` 和 `Cache-Control: private, no-store`。登入 Token、密碼雜湊、暫存工作及 PDF 檔案不在匯出範圍內。PDF 可從原研究結果個別下載。

- `POST /api/v1/projects` 接受 `name`（1–120 字）及選填 `description`（最多 2,000 字），建立私人研究專案並回傳 201。
- `GET /api/v1/projects` 分頁列出目前帳號的專案，接受 `limit`、`offset`。
- `GET /api/v1/projects/{project_id}` 回傳自己的專案詳情。
- `PATCH /api/v1/projects/{project_id}` 更新 `name` 或 `description`。省略或傳入 `null` 的欄位保留原值，說明可用空字串清除。
- `DELETE /api/v1/projects/{project_id}` 刪除空白專案，回傳 204。仍有搜尋、收藏或 AI Session 時回傳 409 `PROJECT_NOT_EMPTY`。
- `PATCH /api/v1/search-runs/{run_id}/project` 接受 `{"project_id":"<UUID>"}`，將已保存搜尋歸檔至自己的專案。傳入 `null` 解除歸檔，候選與比對仍留在歷史。
- `GET /api/v1/search-runs?project_id=<UUID>` 篩選指定專案內的搜尋。搜尋紀錄列表與詳情新增可空的 `project_id`。舊紀錄預設未歸檔。

各端點需要 Bearer token。跨帳號或未知的紀錄及專案回傳 404。

### 專案收藏及私人筆記

以下路徑以 `/api/v1/projects/{project_id}/patents` 為前綴，需要 Bearer token。

| 方法 | 相對路徑 | 行為 |
| --- | --- | --- |
| GET | 空 | 以 `limit`、`offset` 分頁列出收藏的文件版本與筆記。 |
| PUT | `/{document_id}` | 收藏已索引的官方文件版本。重複操作保留既有筆記。 |
| PATCH | `/{document_id}` | 更新 `{"note":"…"}`，最多 4,000 字，空字串可清除筆記。 |
| DELETE | `/{document_id}` | 移除該專案的收藏與筆記。 |

跨帳號、未知專案或不存在的收藏回傳 404。移除收藏後，已保存的搜尋及比對仍可在歷史中讀取。

### AI Session

| 方法 | 路徑 | 行為 |
| --- | --- | --- |
| POST | `/api/v1/sessions` | 用 `project_id` 與 `title`（1–120 字）建立 Session。 |
| GET | `/api/v1/sessions` | 以 `project_id` 指定專案，支援 `limit`、`offset`。 |
| POST | `/api/v1/sessions/{session_id}/messages` | 接受 `{"query":"…"}`（1–1,200 字元）。本機拆解成功才一起保存並回傳 `user` 和 `assistant` 兩筆訊息。 |
| GET | `/api/v1/sessions/{session_id}/messages` | 回傳最近 `limit` 筆（預設 40）並按保存順序排列。可用 `before` 指定同一 Session 內的訊息 UUID 讀取更早的訊息。 |
| DELETE | `/api/v1/sessions/{session_id}` | 擁有者永久刪除 Session 與全部訊息，回傳 204。 |

需要 Bearer token。未知或跨帳號的專案與 Session 回傳 404。AI 草稿含結構化特徵及模型識別。每次拆解使用當次輸入，搜尋結果與證據由原有搜尋紀錄端點保存。
## 私人研究報告

`DELETE /api/v1/search-runs/{run_id}` 讓擁有者永久刪除已保存的搜尋、候選順位及比對。成功回傳 204。不存在或不屬於當前帳號的紀錄回傳 404。刪除完成後，新的紀錄讀取、比對及 PDF 匯出請求均回傳 404。

`GET /api/v1/search-runs/{run_id}/report.pdf` 用 Bearer token 驗證搜尋紀錄所有權，成功回傳 `application/pdf` 及附件檔名。未登入為 401，其他帳號的紀錄或不存在的紀錄為 404。回應標示 `private, no-store`。

工作台使用背景匯出。 `POST /api/v1/search-runs/{run_id}/reports` 回傳 HTTP 202、工作狀態及 `Location`；同一紀錄重複送出時會接回仍在活動的工作。輪詢 `GET /api/v1/search-runs/{run_id}/reports/{report_id}`，成功後在同一路徑加上 `/pdf` 下載。每次請求都需要原帳號的 Bearer token。工作或原搜尋紀錄不存在、過期或不屬於呼叫者時回傳 404。檔案尚無法下載時回傳 409。 背景程序接手前，若報告仍在建立後 10 分鐘內、且上次處理已逾 6 分鐘，會用同一報告 ID 重新認領。待處理或已逾處理期限的工作超出重試時間後標為失敗，原帳號可再送出新報告。

工作狀態為 `queued`、`running`、`succeeded` 或 `failed`。生成結果有 8 MiB 上限。完成一小時後，狀態及檔案不再提供，工作程序負責清理暫存。原同步下載端點仍可供既有客戶端使用。

同步端點直接產生報告供下載。報告涵蓋當次保存的構想、篩選、檢索設定、索引涵蓋範圍、候選順位及已保存比對。官方來源連結於匯出時讀取。背景端點的暫存行為見下方說明。
## 背景搜尋

已登入使用者可用下列端點把混合搜尋排入背景。成功後會取得一般研究歷史可用的搜尋紀錄 ID。

| 請求 | 行為 |
| --- | --- |
| `POST /api/v1/search-jobs` | 接受混合搜尋請求，回傳 HTTP 202、工作 ID 及狀態網址 `Location`。同一帳號已有活動工作時回傳 409。 |
| `GET /api/v1/search-jobs/active` | 取得目前的等待中或執行中工作，沒有時回傳 `null`。 |
| `GET /api/v1/search-jobs/{job_id}` | 回傳狀態、起訖時間、失敗代碼和成功時的 `run_id`。 |
| `POST /api/v1/search-jobs/{job_id}/cancel` | 取消等待中或執行中工作。完成後呼叫會取得既有的完成狀態。 |

狀態為 `queued`、`running`、`succeeded`、`failed` 或 `cancelled`。跨帳號存取回傳 404。成功時以 `GET /api/v1/search-runs/{run_id}` 讀取保存的候選。取消會阻止工作寫入新的研究紀錄。已送出的模型請求可能持續執行到回應或逾時。 建立後 10 分鐘內，已執行超過 6 分鐘的搜尋可由工作程序以原 ID 重新認領。較早處理程序的遲到結果無法寫入或建立研究紀錄。逾期工作的狀態為 `failed`，錯誤碼為 `SEARCH_JOB_EXPIRED`。
## 官方匯入監控

`GET /api/v1/admin/ingestion/jobs?limit=20&offset=0` 回傳期別、匯入／詞彙／向量階段、執行狀態、時間與筆數。由部署者以 `INGESTION_ADMIN_USER_IDS` 授權既有帳號 UUID；`GET /api/v1/me` 的 `can_monitor_ingestion` 供工作台顯示權限。未登入回傳 401，未授權回傳 403，所有工作紀錄均依權限保護。此 API 提供查詢，匯入由部署者從命令列啟動。

## 語料狀態與操作歷程補充

`GET /api/v1/corpus/status` 為公開資料，回傳已驗證的文件版本、詞彙及所有模型的向量覆蓋筆數，以及最近 10 筆官方批次的安全計數。不回傳匯入失敗文字、工作日誌或私人研究資料。

`GET /api/v1/audit-logs` 需要 Bearer token。透過 `limit` 與 `offset` 查詢登入者的註冊、研究資料匯出及背景搜尋送出紀錄。結果禁止快取，事件不含構想內容或登入憑證。帳號刪除時同步清理。

混合搜尋與使用相同查詢結構的背景研究接受 `sort_by`，值為 `relevance`（預設）、`date_desc` 或 `date_asc`。日期只調整已選出的候選順序，在分頁前套用。同日維持相關性順序，未知日期放在最後。
