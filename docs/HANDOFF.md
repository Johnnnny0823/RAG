# Agent Handoff

## M3 私人搜尋紀錄驗收

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `a5e98c7`。
- Current milestone and status: M3 DONE。M4 研究介面待開始。
- Goal of this session: 讓使用者主動保存混合搜尋、候選順位及可回溯證據，驗證帳號隔離。
- Files changed (with purpose): `accounts.py`、`identity.py` 建立本機帳號及驗證，`search_runs.py` 保存及讀取結果，`main.py` 掛載路由，`patents.py` 重用混合查詢與錯誤處理，`scripts/smoke_search_runs.py` 驗證隔離與保存。
- Database migrations added/applied: `0005_search_runs` 已在含 TIPO 樣本的 `patentscope-m1-proof` 套用，亦在新建的 `patentscope-m3-check` 空資料卷遷移並查得 head。
- API/Schema changes: 帳號、Bearer 驗證、搜尋歷史與候選比對保存，見 [API.md](API.md)。
- Commands actually run and results: Ruff 格式及 lint 通過。預設 pytest 暫存目錄遇到 WinError 5（41 通過、3 個 setup error），改用 `pytest -q --basetemp <新建的獨立路徑>` 後 44 通過，1 則既有 Starlette 警告。以 `--api http://127.0.0.1:18010` 執行 `smoke_search_runs.py`、`smoke_hybrid.py`、`smoke_comparison.py` 均通過，涵蓋兩帳號隔離、排名快照、真實文件引文及缺少證據的結果。
- Tests NOT run and reason: 遠端 CI 未觸發。本次無 UI 變更，瀏覽器工作流程留待 M4，檢索品質評估留待 M5。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 已記錄官方樣本](DATA_SOURCES.md)，本次無新增擷取。
- Known bugs / risks / blockers: 搜尋與比對同步執行。紀錄屬於帳號，研究專案、登出、刪除流程、正式部署限流及完整語料重跑尚待後續實作。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄保存與帳號隔離的設計。
- Uncommitted changes / file ownership warnings: 本機驗收 API 綁定 `127.0.0.1:18010`，驗收資料庫含測試帳號及公開查詢。
- Next 1–3 concrete actions: 串接 M4 查詢輸入與特徵編輯、候選詳情及證據顯示，再接研究專案、收藏及筆記並跑瀏覽器驗收。
- Exact reproduction steps: 見 [M3 私人搜尋紀錄驗收](SETUP.md#m3-私人搜尋紀錄驗收)。

## M3 候選重排

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `c786db2`。
- Current milestone and status: M3 IN_PROGRESS。
- Goal of this session: 接上本機模型重排並保留原始融合順位。
- Files changed (with purpose): `patents.py` 接入重排，`rerank.py` 驗證候選排列，新增重排測試及真實語料驗收。
- Database migrations added/applied: 無。
- API/Schema changes: 混合查詢新增 `rerank` 選項與排序來源欄位，見 [API.md](API.md)。
- Commands actually run and results: Ruff 格式、lint 與 pytest 44 項通過。真實語料三筆的融合順位由 `[1,2,3]` 重排為 `[2,1,3]`，保留版本及原分數。
- Tests NOT run and reason: 遠端 CI 與相關性改善評估未執行。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 官方樣本](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 重排最多讀取八筆標題及摘要，模型排序仍需人工評估。此端點不保存執行紀錄。
- Decisions made (ADR links): 見 [DECISIONS.md](DECISIONS.md)。
- Uncommitted changes / file ownership warnings: 驗收 API 綁定 `127.0.0.1:18009`。
- Next 1–3 concrete actions: 建立有存取隔離的搜尋執行紀錄，保存候選順位、模型版本及已驗證證據。
- Exact reproduction steps: 沿用本機嵌入及分析模型設定，重建 API 並映射到 18009，執行 `python scripts/smoke_rerank.py`。

## M3 文件版本比對預覽

- Date/time (timezone): 2026-11-09（Asia/Taipei）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `7cb46b0`。
- Current milestone and status: M3 IN_PROGRESS。
- Goal of this session: 用本機模型判定已確認技術特徵，逐字核對版本內的原文證據。
- Files changed (with purpose): `comparisons.py` 提供比對 API，`evidence.py` 負責片段選取及模型結果驗證，新增單元和真實語料冒煙測試。
- Database migrations added/applied: 無。沿用 `0004_semantic`。
- API/Schema changes: `POST /api/v1/patents/{document_id}/compare`，詳見 [API.md](API.md)。
- Commands actually run and results: Ruff 格式與 lint、pytest 39 項通過（既有警告一則）。`python scripts/smoke_comparison.py` 用真實文件 `202640162` 得到 supported，核對引文、偏移、XPath、雜湊、書目版無證據及無詞命中。精確查詢冒煙測試通過。
- Tests NOT run and reason: 遠端 CI、整體比對品質及召回率未驗。
- Data sources checked (exact URL/date) and license/access notes: 沿用 [M1 官方樣本](DATA_SOURCES.md)，本次無新增擷取。
- Known bugs / risks / blockers: 只選一段字詞命中的片段。原文依資料庫中已保存的版本與檔案雜湊追溯，請求時未重新讀取 XML。結果暫未持久化。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄版本與選段限制。
- Uncommitted changes / file ownership warnings: 隔離 API 為 `127.0.0.1:18008`，只使用公開樣本與測試特徵。
- Next 1–3 concrete actions: 加入候選重排和可重現搜尋紀錄，再串接已驗證證據。
- Exact reproduction steps: 沿用上一節模型設定與資料庫，重新建置 API 並映射到 `127.0.0.1:18008`，執行 `python scripts/smoke_comparison.py`。

## M3 技術特徵與查詢展開

- Date/time (timezone): 2026-11-09（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `05647fb`。
- Current milestone and status: M3 IN_PROGRESS。M2 DONE。
- Goal of this session: 以本機模型拆解技術特徵，驗證經使用者編輯的中英文檢索詞實際改變混合檢索。
- Files changed (with purpose): `services/api/queries.py` 提供拆解 API；`query_features.py` 驗證模型草稿與展開；`ollama.py` 共用本機模型傳輸；混合 API 接受已確認的特徵；Compose 範例加入可選分析模型設定。
- Database migrations added/applied: 無新遷移。沿用 `0004_semantic` 與隔離語料。
- API/Schema changes: 新增 `POST /api/v1/queries/analyze`，混合端點新增可選 `features` 及回傳 `applied_feature_ids`。見 [API.md](API.md)。
- Commands actually run and results:
  - `python scripts/smoke_query_features.py` 通過，Qwen2.5 1.5B 提取一項有效雙語特徵。編輯後，原本詞彙分支未命中的公開案 `202637274` 同時出現在詞彙與向量分支。
  - Ruff 格式、lint、`pytest -q --basetemp=<new-directory>` 38 項通過，1 則既有 Starlette 棄用警告。混合、語意、精確、詞彙與 M0 冒煙測試已通過。
- Tests NOT run and reason: 遠端 CI 及廣泛模型品質評估未執行。重排、持久化搜尋與引文比對仍待實作。
- Data sources checked (exact URL/date) and license/access notes: 重用 [M1 官方語料](DATA_SOURCES.md)，未新增擷取。核對 [Ollama 結構化輸出](https://docs.ollama.com/capabilities/structured-outputs)。
- Known bugs / risks / blockers: Ollama 0.13.5 的 schema-to-grammar 轉換在 7B 與 1.5B 測試中曾引發程序重啟。改用 JSON 模式、格式範例及 Pydantic 驗證。1.5B 模型可能省略次要特徵或加入多餘欄位，故結果保留草稿性質，多餘欄位不回傳。只用公開測試查詢驗收。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄 JSON 模式、展開及 IPC 候選的處理。
- Uncommitted changes / file ownership warnings: 驗收 API 綁定 `127.0.0.1:18007`。預設開發環境未配置分析模型。
- Next 1–3 concrete actions:
  1. 實作按文件版本的證據選取、逐字引用驗證與技術特徵判定。
  2. 加入重排與搜尋執行紀錄，保存模型、候選排名及已驗證證據。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「M3 本機技術特徵驗收」。

## M3 混合檢索檢查點

- Date/time (timezone): 2026-11-09 02:23（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點為 `1beaef0`。
- Current milestone and status: M3 IN_PROGRESS。M2 DONE。
- Goal of this session: 以真實詞彙與向量結果驗證 RRF 融合、可查核的分支排名和版本去重。
- Files changed (with purpose): `services/retrieval/fusion.py` 負責融合與去重，`services/api/patents.py` 共用候選查詢並提供混合端點。`tests/test_fusion.py` 和 `scripts/smoke_hybrid.py` 驗證單分支、分數與真實語料。
- Database migrations added/applied: 無新遷移。沿用 `0004_semantic` 與既有索引。
- API/Schema changes: 新增 `POST /api/v1/patents/search/hybrid`。見 [API.md](API.md)。
- Commands actually run and results:
  - Ruff 格式和 lint 通過，`pytest -q --basetemp=<new-directory>` 34 項通過，1 則既有 Starlette 棄用警告。
  - `python scripts/smoke_hybrid.py` 使用 18006 埠、真實 TIPO 語料與 Ollama，核對單分支排名、RRF 數值、IPC、分頁及同案公開與公告各自保留。語意、詞彙、精確查詢及 M0 冒煙測試均通過。
- Tests NOT run and reason: 未執行遠端 CI 或相關性評估。未測功能包括模型重排、特徵拆解及證據驗證。
- Data sources checked (exact URL/date) and license/access notes: 本次重用 [M1 官方資料](DATA_SOURCES.md)，無新增擷取。融合公式參考 [RRF 原論文](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)。
- Known bugs / risks / blockers: 每分支限前 100 筆，低排名候選可能被截斷。混合查詢尚未持久化，也未提供模型重排、查詢特徵與證據驗證。現有模型設定僅使用公開資料驗收。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄 RRF、快照與去重規則。
- Uncommitted changes / file ownership warnings: 真實語料保留在原隔離資料庫，驗收 API 綁定 `127.0.0.1:18006`。
- Next 1–3 concrete actions:
  1. 接入本機模型輸出的可編輯中英文檢索特徵，並將特徵接到混合候選。
  2. 加入重排、結果與模型版本的搜尋紀錄，以及按文件版本與原文位置的證據驗證。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「M3 混合檢索驗收」。

## M2 語意檢索驗收

- Date/time (timezone): 2026-11-09 02:18（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點為 `d266abb`。
- Current milestone and status: M2 DONE。M3 NOT_STARTED。
- Goal of this session: 用本機嵌入模型與 PostgreSQL pgvector 驗證真實 TIPO 語料的語意查詢。
- Files changed (with purpose): `services/retrieval/embeddings.py` 驗證本機模型，`index_semantic.py` 產生分段向量。API 加入語意路由與 IPC 共用條件。Compose／環境範本加入可選模型設定。新增測試與語意冒煙驗收。
- Database migrations added/applied: `0004_semantic` 建立模型版本及片段向量表。驗收資料庫由 `0003_lexical` 升級，另從全新資料卷遷移至 head 成功。
- API/Schema changes: `POST /api/v1/patents/search/semantic` 提供模型識別、IPC、排序及分頁。見 [API.md](API.md)。
- Commands actually run and results:
  - 本機 Ollama 0.13.5 搭配已安裝的 `qwen3-embedding:0.6b`，實測 1,024 維。 `python -m services.retrieval.index_semantic` 產生 143 個文件版本的 1,724 筆向量，重跑新增零筆。
  - `python scripts/smoke_semantic.py` 兩個已知目標中英文改寫皆第一名，IPC、分頁和模型欄位通過。精確、詞彙與 M0 冒煙測試通過。
  - 最終 SQL `EXPLAIN (ANALYZE, BUFFERS)` 英文加 IPC 案例使用向量複合主鍵定位候選。一次本機執行 1.316 ms，未含模型推論。
  - Ruff 格式、lint、`pytest -q --basetemp=<new-directory>` 通過，31 項測試及 1 則既有 Starlette 棄用警告。
- Tests NOT run and reason: 遠端 CI 未執行。語意驗收屬小規模已知目標冒煙，ANN 和人工相關性評估尚未執行。
- Data sources checked (exact URL/date) and license/access notes: 重用 [M1 官方語料](DATA_SOURCES.md)，無新增擷取。2026-11-09 核對 [Qwen 模型卡](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) 與 [Ollama 嵌入 API](https://docs.ollama.com/api/embed)。
- Known bugs / risks / blockers: 向量維度固定為 1,024。模型與向量索引須同 digest 和 pipeline。共享 Ollama 僅用公開資料驗收；敏感查詢需私有模型服務。現採精確距離搜尋，未上 ANN。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄版本、分段與排序。
- Uncommitted changes / file ownership warnings: 驗收 API 綁定 `127.0.0.1:18005`，資料在隔離資料卷。預設開發環境未設定嵌入模型。
- Next 1–3 concrete actions:
  1. M3 將詞彙與向量候選以 RRF 合併，區分版本並保存可重現的排序資訊。
  2. 實作可編輯的查詢特徵、重排及按文件版本與原文位置驗證的證據。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「M2 本機語意索引」。

## M2 詞彙檢索檢查點

- Date/time (timezone): 2026-11-09 02:12（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點為 `a9b446d`。
- Current milestone and status: M2 IN_PROGRESS。M1 DONE。
- Goal of this session: 用真實語料驗證繁中／英文詞彙檢索、IPC 篩選和增量索引。
- Files changed (with purpose): `services/retrieval/` 提供分詞和增量索引，`services/api/patents.py` 提供詞彙端點。`tests/test_lexical.py` 和 `scripts/smoke_lexical.py` 驗收分詞、錯誤與真實語料。
- Database migrations added/applied: `0003_lexical` 建立衍生詞彙片段和 GIN 索引。已從 M1 資料庫升級及從空資料庫遷移，預設開發資料庫未套用。
- API/Schema changes: `POST /api/v1/patents/search` 接受詞彙查詢、IPC 與分頁。見 [API.md](API.md)。
- Commands actually run and results:
  - `python -m services.retrieval.index_lexical` 建立 143 個真實文件版本的 1,654 個片段，重跑新增零筆。乾淨隔離庫依次匯入兩期各 5 筆後，索引分別新增 5 筆和 5 筆，第三次新增零筆。
  - `python scripts/smoke_lexical.py`、`python scripts/smoke_patents.py --api http://127.0.0.1:18004` 和 `python scripts/smoke.py` 通過。四個已知目標的詞彙案例均第 1 名，IPC 排除與分頁通過。
  - `EXPLAIN (ANALYZE, BUFFERS)` 確認英詞加 IPC 案例使用 GIN，單次 SQL 執行 0.555 ms。
  - Ruff 格式和 lint 通過，`pytest -q --basetemp=<new-directory>` 27 項通過，1 則既有 Starlette 棄用警告。
- Tests NOT run and reason: 遠端 CI 未執行。詞彙驗收屬已知目標冒煙，尚無人工相關性標註與向量驗收。
- Data sources checked (exact URL/date) and license/access notes: 重用 [M1 的 TIPO 正式語料](DATA_SOURCES.md)，無新增擷取。
- Known bugs / risks / blockers: 漢字雙字基線需同一片段出現全部查詢詞，不處理同義詞、簡繁轉換或跨段比對。詞彙索引在匯入後需明確執行更新命令。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄分詞、排序與實測查詢計畫。
- Uncommitted changes / file ownership warnings: 真實資料留在隔離資料庫及配對原始檔。驗收 API 綁定 `127.0.0.1:18004`。
- Next 1–3 concrete actions:
  1. 加入可替換嵌入模型、模型版本記錄和 pgvector 索引，實測真實語料的語意端點。
  2. 完成 M2 驗收後，M3 接查詢特徵、混合檢索、重排及證據驗證。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「M2 詞彙索引與驗收」。

## M2 精確號碼與詳情 API 檢查點

- Date/time (timezone): 2026-11-09 02:07（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點為 `a8ae20f`。
- Current milestone and status: M2 IN_PROGRESS。M1 DONE。
- Goal of this session: 用真實臺灣專利語料驗證精確申請、公開、公告號查詢及版本隔離。
- Files changed (with purpose): `services/api/patents.py` 提供查詢、詳情、請求項與來源契約，`main.py` 掛載路由。測試覆蓋輸入、錯誤和 URL 篩選，`scripts/smoke_patents.py` 驗收真實語料。
- Database migrations added/applied: 無新遷移。使用既有 `0002_ingestion` 的隔離資料庫。
- API/Schema changes: 新增 `GET /api/v1/patents`、`GET /api/v1/patents/{document_id}` 及 `GET /api/v1/patents/{document_id}/claims`。詳見 [API.md](API.md)。
- Commands actually run and results:
  - Ruff 格式及 lint、`pytest -q --basetemp=<new-directory>` 通過，25 項通過及 1 則既有 Starlette 棄用警告。
  - 建置隔離 API 並在 18003 埠以 `python scripts/smoke_patents.py` 驗證真實查詢。驗收涵蓋分頁、空結果、404、同案公告與公開版本各 13 項請求項、書目版本空請求項及原檔雜湊定位。第二期資料的 FTPS URL 正常回傳。
  - 三種精確查詢皆執行 `EXPLAIN (ANALYZE, BUFFERS)`，結果見 [DECISIONS.md](DECISIONS.md)。`python scripts/smoke.py` 通過。
- Tests NOT run and reason: 未在遠端執行 CI。尚無詞彙及向量檢索可驗收。
- Data sources checked (exact URL/date) and license/access notes: 本次重用 [M1 已驗證的官方資料](DATA_SOURCES.md)，無新增擷取。
- Known bugs / risks / blockers: 詳情只回傳語料實際保存的欄位。請求項依賴、附件、法律狀態、詞彙及向量搜尋待接入。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄指定號碼類型、可見來源及版本選擇。
- Uncommitted changes / file ownership warnings: 真實語料留在隔離資料庫及配對的原始檔目錄。隔離 API 綁定 `127.0.0.1:18003`。
- Next 1–3 concrete actions:
  1. 實作可評估的繁中詞彙檢索、IPC 篩選和索引更新，記錄實際查詢計畫。
  2. 增加可替換的嵌入模型、模型版本紀錄與 pgvector 語意檢索。用真實語料驗收 M2 後再進 M3。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「M2 精確專利號查詢驗收」。

## M1 跨期增量驗收

- Date/time (timezone): 2026-11-09 02:02（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點 `c498b07`。
- Current milestone and status: M1 DONE，M2 NOT_STARTED。
- Goal of this session: 驗證第二個官方公開卷期的增量匯入，確認先前文件版本與證據仍可追溯。
- Files changed (with purpose): `services/ingestion/import_issue.py` 驗證並保存索引的官方 URL，`verify_document.py` 以文件定位查找公告來源；新增來源 URL 回歸測試並更新開發文件。
- Database migrations added/applied: 無新遷移。沿用隔離驗收資料庫 `patentscope-m1-proof` 的 `0002_ingestion`。
- API/Schema changes: REST 與 Schema 無變更。匯入 CLI 新增可選的 `--index-source-url`。
- Commands actually run and results:
  - `python -m services.ingestion.download` 從官方 FTPS 取得第 24 卷第 18 期索引；XML 宣告與實際皆為 1,984 筆。
  - `import_issue --verified-tipo --batch 024018 --limit 25 --index-source-url <official-url>` 第一次新增 25 個書目版本，第二次 `reused: true`。比較 SQL 快照確認原有 118 個文件 ID 和內容雜湊全數保留，既有 256 項請求項數量相同，批次只增加一筆。資料庫可查到第二期官方 URL 和相符的 SHA-256。
  - `verify_document` 再次逐項核對同一申請案的公開與公告版本，各 13 項請求項；公開版另核對 41 段說明書。
  - Ruff 格式及 lint、`pytest -q --basetemp=<new-directory>` 的 18 項測試、本機冒煙測試皆通過。保留一則既有 Starlette 棄用警告。
- Tests NOT run and reason: 未在遠端執行 CI。此次完成的是已驗證來源的匯入 PoC，尚未測量生產資料庫索引、全量下載或檢索品質。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-09 核對 [政府目錄 15996](https://data.gov.tw/dataset/15996)，並從 [官方 FTPS 第二期索引](ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024018/index.xml) 取得樣本。完整雜湊與授權見 [DATA_SOURCES.md](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 125 個公開號中有 17 份公開全文；另有 1 份公告請求項，未取得該公告的說明書全文。3 份原始公開 XML 缺請求項編號而隔離。尚未整合更廣的資料來源、法律狀態或排程更新。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄來源 URL 與卷期約束。
- Uncommitted changes / file ownership warnings: 真實 XML 保存在本機暫存路徑，驗收資料卷保留。樣本未併入預設開發資料卷。
- Next 1–3 concrete actions:
  1. M2 建立精確申請號、公開號、公告號查詢及文件詳情 API。證據和本文以文件版本 ID 查詢。
  2. 為繁體中文設計可測的詞彙檢索基線，記錄查詢計畫並加上 pgvector 索引與可替換的嵌入模型。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「第二期增量匯入」。

## M1 批次全文與公告版本檢查點

- Date/time (timezone): 2026-11-09 01:58（Asia/Taipei，UTC+8）。
- Agent: Codex。
- Branch / commit SHA: `main`，本文件所在提交，起點為 `adb612c`。
- Current milestone and status: M1 IN_PROGRESS。M0 DONE。
- Goal of this session: 由 TIPO 清單下載批次全文，並以同一申請案核對公開與公告版本。
- Files changed (with purpose): `services/ingestion/` 增加清單核對、主機快取、公告索引解析及來源回溯。 `tests/` 新增清單、離線快取、重試及公告驗證。更新來源、決策、設定與進度文件。
- Database migrations added/applied: 沿用隔離資料庫 `patentscope-m1-proof` 的 `0002_ingestion`。無新遷移。
- API/Schema changes: REST 無變更。公告文件以 `grant` 階段及 `claims_only` 範圍保存。
- Commands actually run and results:
  - Windows 主機 `import_issue --fetch-only --limit 20` 成功取得 20 份官方 XML。容器預設信任存放區未通過官方 FTPS 憑證鏈驗證，已確認下載失敗會記錄原因。透過 `--cache-only` 匯入 17 份全文，另 3 份因來源缺少請求項編號隔離，重跑回傳 `reused: true`。
  - 匯入 S01 公告 `I941082` 並重跑，第二次回傳 `reused: true`。SQL 確認同一申請號 `114106690` 保留公告、公開全文及公開書目三筆版本。逐項核對兩版各 13 項請求項與公開版 41 段說明書。
  - Ruff 格式、lint、`pytest -q --basetemp=<new-directory>` 的 17 項測試及 `python scripts/smoke.py` 通過。仍有 1 則既有 Starlette 棄用警告。
- Tests NOT run and reason: 同一來源跨卷期增量尚缺第二期公開樣本。遠端 CI 尚未執行。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-09 核對並實取 [官方 S01 公告索引](https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S01)，由 [目錄 15987](https://data.gov.tw/dataset/15987) 連結，適用政府資料開放授權第 1 版。公開卷期與 FTPS 證據見 [DATA_SOURCES.md](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 3 份公開 XML 缺請求項編號，需比對官方公報再決定映射。容器直接 FTPS 需另有可信憑證鏈，現可由主機驗證後快取。尚未驗證跨期發現、更新和公告全文。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄逐筆限速、來源配對及缺號隔離。
- Uncommitted changes / file ownership warnings: 真實 XML 不進 Git。隔離資料卷與 `%TEMP%/patentscope-m1-run/objects` 保留配對。
- Next 1–3 concrete actions:
  1. 取得第二個公開卷期的官方索引，驗證只新增該期的資料及同一期重跑去重。
  2. 核對缺號來源是否有可驗證的正式編號，以及公告全文來源。記錄涵蓋率後完成 M1 驗收。
  3. M1 驗收後進入 M2，從專利編號精確查找及文件詳情 API 開始。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的「以官方清單補入全文」及「公告版本比對」。

## M1 初次官方資料匯入紀錄

- Date/time (timezone): 2026-11-09 01:50（Asia/Taipei，UTC+8）。
- Agent: Codex，官方來源研究代理負責 [DATA_SOURCES.md](DATA_SOURCES.md)。
- Branch / commit SHA: `main`，本文件所在的 M1 檢查點提交，起點為 `cb55380`。
- Current milestone and status: M1 IN_PROGRESS。M0 DONE。
- Goal of this session: 取得真正的 TIPO XML 並驗證從原始檔、PostgreSQL 到原文定位的匯入流程。
- Files changed (with purpose): `services/ingestion/` 提供下載、原檔雜湊保存、解析、匯入及回溯驗證。Dockerfile 包含匯入模組。測試涵蓋原始物件校驗、錯誤 XML 隔離、文件定位與卷期檢查。SETUP、PROGRESS、DECISIONS 與 DATA_SOURCES 記錄操作、證據與決策。
- Database migrations added/applied: `0002_ingestion` 建立來源、批次、原始物件關聯、申請案、文件版本、IPC、說明書段落和請求項。新建隔離資料卷從 base 遷移到 `0002_ingestion`，降版在會丟失資料的情況下拒絕。預設開發資料卷未套用本次遷移。
- API/Schema changes: REST 契約無變更。資料表以文件階段及來源雜湊保留版本；此次只驗證發明公開文件。
- Commands actually run and results:
  - `python -m services.ingestion.download` 成功取得官方 HTTPS 卷期索引、相同卷期的 FTPS 索引及個案 XML。兩份索引的 SHA-256 一致，個案雜湊符合來源紀錄。
  - `docker compose -p patentscope-m1-proof run --rm --build migrate` 在新資料卷成功。以 `import_issue --verified-tipo --batch 024019 --limit 100` 匯入 99 筆書目與 1 筆全文，0 筆無效紀錄，0 筆個案隔離。再次匯入回傳 `reused: true`，SQL 確認共 100 筆申請案、100 筆文件、1 個批次。
  - `python -m services.ingestion.verify_document 202639611` 核對原始 SHA-256、19 項請求項與 122 段說明書文字和 XPath。
  - `python -m ruff format --check .` 與 `python -m ruff check .` 通過。`python -m pytest -q --basetemp=<new-directory>` 14 項通過，1 則既有 Starlette 棄用警告。首次使用既有 Windows pytest 暫存路徑時有 2 個測試設定權限錯誤，改用新路徑後通過。`python scripts/smoke.py` 通過。
- Tests NOT run and reason: GitHub Actions 遠端工作未執行。跨卷期增量、公告樣本與批次全文尚未接入。
- Data sources checked (exact URL/date) and license/access notes: 2026-11-09 核對 [政府目錄 15996](https://data.gov.tw/dataset/15996) 與 [政府資料開放授權](https://data.gov.tw/license)，測試 HTTPS 及 FTPS。FTPS 期別 `index_all.xml` 含 2,384 個不需 API 金鑰的個案路徑；實際批次成功率與請求頻率限制待確認。完整路徑、雜湊和限制見 [DATA_SOURCES.md](DATA_SOURCES.md)。
- Known bugs / risks / blockers: 匯入全文暫由操作者以公開號指定個案檔，程式檢查 XML 申請號一致；仍需從官方清單自動綁定每個來源 URL 與公開號。說明書資料限已驗證的 A103.1.0 格式。來源索引不提供日期或 kind code 時保留空值。尚無真實公告樣本及目前法律狀態。
- Decisions made (ADR links): [DECISIONS.md](DECISIONS.md) 記錄 M1 的原始檔與文件版本策略。
- Uncommitted changes / file ownership warnings: 真實 XML 不進 Git。隔離驗收資料卷 `patentscope-m1-proof_postgres-data` 保留，容器已停止，原始物件位於本機 `%TEMP%/patentscope-m1-run/objects`。重新啟動前保留資料卷與物件目錄的配對。
- Next 1–3 concrete actions:
  1. 接上已驗證的 FTPS `index_all.xml`，以清單綁定來源 URL 和公開號，限速分批取得全文並保存實際下載狀態及可重試錯誤。
  2. 取得並驗證官方公告樣本，確認申請案、公開及公告版本可共存，並測試同一文件的新版本不覆寫既有原文。
  3. 實測跨卷期增量匯入，記錄全文覆蓋率與失敗原因，完成 M1 驗收後再進 M2。
- Exact reproduction steps: 見 [SETUP.md](SETUP.md) 的 M1 官方樣本指令；如要重用已驗證資料庫，先執行 `docker compose -p patentscope-m1-proof up -d --wait db`，以保留的物件目錄執行回溯驗證。

## M0 歷史交接

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


- 本次 Codex 負責 M3 混合候選與驗收。
