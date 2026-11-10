# 系統架構

PatentScope AI 是模組化單體：一個 React 前端、一個 FastAPI 行程、一個 PostgreSQL，加上部署者自管的 Ollama 模型服務。全部由 Docker Compose 啟動。規格以 [AGENTS.md](../AGENTS.md) 為準，本文件描述目前實作的樣子。

```mermaid
flowchart LR
    U[瀏覽器] --> W[Web：Vite 開發伺服器或 Nginx 靜態檔]
    W -->|/api/v1 同源代理| A[FastAPI]
    A --> D[(PostgreSQL + pgvector)]
    A -->|嵌入、拆解、比對、重排| O[Ollama 本機模型]
    T[TIPO 官方 FTPS／HTTPS] -->|下載並核對雜湊| I[匯入指令]
    I --> S[原始物件目錄]
    I --> D
    X[索引指令] --> D
    X --> O
```

## 模組

| 路徑 | 職責 |
| --- | --- |
| `apps/web` | React、TypeScript、Tailwind。單頁研究工作台，所有資料來自 API。`e2e/` 是 Playwright TypeScript 測試。 |
| `services/api` | REST 路由、Pydantic 結構、帳號驗證與統一錯誤格式。 |
| `services/ingestion` | TIPO 下載、XML 解析、原始物件保存、批次匯入與回溯驗證。 |
| `services/retrieval` | 繁中斷詞、詞彙與向量索引、RRF 融合、重排、技術特徵與證據處理。 |
| `database/migrations` | Alembic 遷移。資料表見 [資料庫設計](DATABASE.md)。 |
| `scripts` | 冒煙測試、評估與測試語料種子。 |
| `evaluation` | 檢索評估的查詢與待人工複核的候選池。 |

## 離線匯入

1. `services.ingestion.download` 以驗證憑證的 FTPS 取得期別索引與個案 XML。
2. `import_issue` 把原始檔依 SHA-256 存入物件目錄，解析後在單一交易寫入申請案、文件版本、請求項、段落與來源關聯。相同輸入重跑會重用既有批次。解析失敗的檔案隔離並保留錯誤。
3. `verify_document` 從資料庫連回原始檔重新解析，逐項比對請求項與段落。
4. `index_lexical` 與 `index_semantic` 為尚未處理的文件版本建立索引，可重複執行。

匯入與索引是命令列工作，由操作者執行。API 沒有管理端匯入介面，也沒有背景工作佇列。

## 線上檢索

1. `POST /queries/analyze` 用本機模型草擬技術特徵，使用者可以編輯。
2. `POST /patents/search/hybrid` 以原始查詢和已確認的特徵詞分別跑詞彙與向量檢索，各取前 100 筆，以 RRF（k=60）融合，再依公開號與文件階段去重。可選擇用本機模型重排前幾筆，原始融合名次會保留。
3. `POST /patents/{id}/compare` 為每項特徵選一段字詞命中的原文交給模型判定。引文由伺服器依原文位置擷取並核對，模型不能自行提供引文。
4. 登入後可保存搜尋快照與比對結果，並匯出 PDF。

搜尋、比對與 PDF 產生都是同步請求。前端有 180 秒的用戶端逾時。

## 資料邊界

- 公開專利資料：`patent_*` 與 `ingestion_*` 資料表，所有人可查。只回傳來源為正式資料集且解析成功的文件。
- 私人研究資料：專案、搜尋、收藏、Session。每次查詢以帳號 UUID 限定，跨帳號存取回傳 404。
- 模型服務：查詢文字和被比對的專利原文會送到設定的 Ollama 位址。處理未公開構想前，部署者須把模型服務限制在受控的網路內。

## 部署

- 開發：`docker-compose.yml`，含 Vite 開發伺服器與本機連接埠。
- 靜態部署：加上 `docker-compose.deploy.yml`，由 Nginx 提供編譯後的前端並代理 API，只有 Web 綁定回環位址。
- 測試：加上 `docker-compose.test.yml`，使用獨立資料庫 `patentscope_test`。

對外開放所需的 TLS、反向代理、一般速率限制與備份由部署端負責，尚未實測。步驟見 [環境設定](SETUP.md)。

## 目前沒有的部分

- 管理端的匯入監控介面與背景工作佇列。
- 登入以外的速率限制。
- 結構化日誌與操作稽核紀錄。
- 語料快照版本化：保存的搜尋保留當時的候選與分數，但無法以舊語料重跑。
- 經人工標註的檢索品質評估，見 [檢索評估](EVALUATION.md)。
