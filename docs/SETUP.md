# 開發環境與部署

## 本機安裝

1. 安裝 Git、Docker Desktop 或 Docker Engine 與 Docker Compose v2。使用 Linux 容器。
2. 安裝 Python 3.12 與 Node.js 22.12+，供容器外測試及編譯。
3. 在專案根目錄複製環境範本為 `.env`，依需要調整 Web/API 連接埠與本機 DB 初始帳密。
4. 依 [README](../README.md) 啟動 Compose 與執行檢查。變更初始 DB 帳密環境變數只影響新資料卷。

Linux/macOS 可用 `cp .env.example .env`，虛擬環境的 Python 路徑為 `.venv/bin/python`。可用 `docker compose logs db migrate api web` 排查啟動問題。`migrate` 容器正常狀態是執行完畢並以代碼 0 結束。

## Windows 排查

如果 Docker Compose v2.40 的 Bake 顯示 `failed to execute bake: exit status 100`，可在目前 PowerShell 暫時設定 `$env:COMPOSE_BAKE = 'false'` 再執行建置。Compose 已將此設定標示為棄用，若使用不支援這個設定的版本，可在純 ASCII 路徑的工作副本重試。

若 Git 在未記錄檔案擁有權的磁碟上顯示 `dubious ownership`，可用 `git -c safe.directory=D:/專利RAG status` 只對該次指令指定可信目錄。

## 部署狀態

M0 的 Compose 設定用於本機開發，包含 Vite 開發伺服器、開發用帳密和本機連接埠。正式部署的環境及帳密管理方式待後續里程碑決定。

## M1 官方樣本重現

下列 PowerShell 指令使用獨立的 Compose 專案與資料卷。先依 README 建立 `.env`。第 24 卷第 19 期索引和個案說明書的授權、雜湊及格式見 [資料來源](DATA_SOURCES.md)。從空的資料目錄下載，下載器會拒絕覆寫既有檔案。

```powershell
$data = New-Item -ItemType Directory -Force .patent-data
$index = 'ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/index.xml'
$spec = 'ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/2419202639611/113133932-A0304.xml'
python -m services.ingestion.download --index-url $index --index-out (Join-Path $data.FullName 'index.xml') --spec-url $spec --spec-out (Join-Path $data.FullName 'spec.xml')
$project = 'patentscope-m1'
docker compose -p $project up -d --wait db
docker compose -p $project run --rm --build migrate
docker compose -p $project run --rm --no-deps -v "$($data.FullName):/inputs" migrate python -m services.ingestion.import_issue --verified-tipo --index /inputs/index.xml --spec 202639611=/inputs/spec.xml --batch 024019 --limit 100 --objects /inputs/objects
docker compose -p $project run --rm --no-deps -v "$($data.FullName):/inputs:ro" migrate python -m services.ingestion.verify_document 202639611 --objects /inputs/objects
```

重跑匯入應回傳 `reused: true`。預期批次為 `partial`，其中 99 筆只有書目與可取得的摘要，1 筆包含全文。驗證命令會從 DB 連回原始物件、重新解析，並比對所有已保存的請求項和說明書段落。原始資料與資料庫須一起保存。Windows 若遇到 Bake 錯誤，沿用上方的排查方式。

### 以官方清單補入全文

用同一個資料目錄、Compose 專案及已安裝依賴的主機 Python。主機使用系統信任存放區驗證 FTPS，容器使用已下載快取。每次對 TIPO 的個案傳輸依序執行，間隔至少一秒。

```powershell
$manifest = 'ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/index_all.xml'
python -m services.ingestion.download --index-url $manifest --index-out (Join-Path $data.FullName 'index_all.xml')
python -m services.ingestion.import_issue --verified-tipo --index (Join-Path $data.FullName 'index.xml') --manifest (Join-Path $data.FullName 'index_all.xml') --manifest-url $manifest --batch 024019 --limit 20 --objects (Join-Path $data.FullName 'objects') --fetch-only
docker compose -p $project build migrate
docker compose -p $project run --rm --no-deps -v "$($data.FullName):/inputs" migrate python -m services.ingestion.import_issue --verified-tipo --index /inputs/index.xml --manifest /inputs/index_all.xml --manifest-url $manifest --batch 024019 --limit 20 --objects /inputs/objects --cache-only
```

若主機下載部分失敗，可重跑 `--fetch-only`。匯入會保留已取得的檔案及未取得的個案資訊。此清單驗收樣本的 20 份 XML 有 17 份可解析為全文，3 份缺請求項編號而隔離。

### 公告版本比對

官方 [S01 最新期索引](https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S01) 會更新，使用以下指令前先核對 [來源紀錄](DATA_SOURCES.md) 的期別與檔案雜湊。驗收檔案為第 53 卷第 28 期，放在同一資料目錄的 `grant-s01.xml`。

```powershell
docker compose -p $project run --rm --no-deps -v "$($data.FullName):/inputs" migrate python -m services.ingestion.import_issue --verified-tipo --index /inputs/grant-s01.xml --grant-number I941082 --batch 053028 --objects /inputs/objects
docker compose -p $project run --rm --no-deps -v "$($data.FullName):/inputs:ro" migrate python -m services.ingestion.verify_document I941082 --grant-issue 053028 --objects /inputs/objects
```

### 第二期增量匯入

在原本的資料卷和原始檔目錄追加第二期。使用下列指令可將該期 URL 與索引雜湊寫入資料庫。第一次應新增 25 筆書目，重跑同一匯入命令應回傳 `reused: true`。

```powershell
$second = 'ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024018/index.xml'
python -m services.ingestion.download --index-url $second --index-out (Join-Path $data.FullName 'issue-024018.xml')
docker compose -p $project build migrate
docker compose -p $project run --rm --no-deps -v "$($data.FullName):/inputs" migrate python -m services.ingestion.import_issue --verified-tipo --index /inputs/issue-024018.xml --index-source-url $second --batch 024018 --limit 25 --objects /inputs/objects
```

## M2 精確專利號查詢驗收

完成上方三批匯入後，對同一個有資料的 Compose 專案啟動 API，另開終端執行真實語料冒煙測試。

```powershell
docker compose -p $project build api
docker compose -p $project run --rm --no-deps -p 127.0.0.1:18003:8000 api
python scripts/smoke_patents.py
```

本機 [OpenAPI](http://127.0.0.1:18003/docs) 可試查公開號 `202640162` 與公告號 `I941082`。重現需要上述 M1 樣本，空資料庫會回傳空清單。

## M2 詞彙索引與驗收

在同一個含 M1 語料的專案套用 `0003_lexical`。每次匯入後執行索引命令，會新增尚未處理的文件版本。

```powershell
docker compose -p $project run --rm --build migrate
docker compose -p $project run --rm --no-deps migrate python -m services.retrieval.index_lexical
docker compose -p $project build api
docker compose -p $project run --rm --no-deps -p 127.0.0.1:18004:8000 api
```

另開終端執行 `python scripts/smoke_lexical.py` 與 `python scripts/smoke_patents.py --api http://127.0.0.1:18004`。重跑索引命令預期新增零筆。

## M2 本機語意索引

準備一個由本機管理的 Ollama，並載入 `qwen3-embedding:0.6b`。驗收使用 Ollama 0.13.5，模型 digest 為 `ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d`。用 `GET http://127.0.0.1:11434/api/tags` 確認實際值。若更換模型，需以相容的 1,024 維模型另建索引。

Docker Desktop 可從容器以 `host.docker.internal` 連到主機管理的模型服務。處理未公開發明前，應將模型服務限制在受控的本機或私有網路。此次共享環境只以公開語料及測試查詢驗收。

```powershell
$env:EMBEDDING_URL = 'http://host.docker.internal:11434'
$env:EMBEDDING_MODEL = 'qwen3-embedding:0.6b'
$env:EMBEDDING_DIGEST = 'ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d'
docker compose -p $project run --rm --build migrate
docker compose -p $project run --rm --no-deps migrate python -m services.retrieval.index_lexical
docker compose -p $project run --rm --no-deps migrate python -m services.retrieval.index_semantic
docker compose -p $project build api
docker compose -p $project run --rm --no-deps -p 127.0.0.1:18005:8000 api
```

另開終端執行 `python scripts/smoke_semantic.py`。模型未設定時，精確查詢與詞彙檢索仍可使用。

## M3 混合檢索驗收

保留上方語意索引的專案和模型設定，重新建置 API，再於另一個終端執行冒煙測試。

```powershell
docker compose -p $project build api
docker compose -p $project run --rm --no-deps -p 127.0.0.1:18006:8000 api
python scripts/smoke_hybrid.py
```

## M3 本機技術特徵驗收

保留嵌入模型設定，另外配置本機 Ollama 分析模型。以 `ollama pull qwen2.5:1.5b` 取得模型，並從本機 `/api/tags` 核對 digest。分析請求使用 CPU。共用模型服務僅用公開測試查詢驗收。

```powershell
$env:ANALYSIS_URL = 'http://host.docker.internal:11434'
$env:ANALYSIS_MODEL = 'qwen2.5:1.5b'
$env:ANALYSIS_DIGEST = '65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b'
docker compose -p $project build api
docker compose -p $project run --rm --no-deps -p 127.0.0.1:18007:8000 api
python scripts/smoke_query_features.py
```

API 啟動後在另一終端跑冒煙測試。測試以同一個原始查詢比較編輯前後的分支排名。

## M3 私人搜尋紀錄驗收

沿用已匯入官方樣本的隔離專案及上方嵌入、分析模型設定。執行遷移並啟動 API。

```powershell
docker compose -p $project run --rm --build migrate
docker compose -p $project build api
docker compose -p $project run --rm --no-deps -p 127.0.0.1:18010:8000 api
```

另開終端執行 `python scripts/smoke_search_runs.py`。腳本會在資料庫留下測試帳號、公開測試查詢與比對紀錄，請使用隔離資料庫。

## M4 瀏覽器驗收

保持上方的 API 運行。從 `apps/web` 執行下列指令，開啟 `http://127.0.0.1:18110`。

```powershell
npm ci
$env:API_PROXY_TARGET = 'http://127.0.0.1:18010'
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 18110 --strictPort
```

輸入「動態導通電阻」並執行 AI 拆解。將特徵描述改為「動態導通電阻量測電路」，保留同名繁中檢索詞，並設定 IPC 為 `G01R`。搜尋並開啟公開文件 `202640162` 的全文版本，確認請求項、說明書與來源，再比對並展開原文定位。改用 `A01B` 驗證空結果，輸入 `INVALID` 驗證錯誤訊息。結果取決於當前語料、模型與已確認特徵。

私人歷史、專案歸檔與管理、收藏、筆記及 AI Session 可用 Playwright CLI 驗收。啟動前先對同一個隔離專案執行 `docker compose -p $project run --rm --build migrate`，並重建 API，使資料庫與 API 都包含 `0008_research_sessions`。以下命令由專案根目錄執行，會建立兩個測試帳號並留下公開測試查詢、比對、專案與 Session。腳本只會刪除本次建立的空白測試專案。

```powershell
npx --yes --package @playwright/cli@0.1.23 playwright-cli -s=patent-private open http://127.0.0.1:18110
npx --yes --package @playwright/cli@0.1.23 playwright-cli -s=patent-private run-code --filename scripts/smoke_private_browser.js
npx --yes --package @playwright/cli@0.1.23 playwright-cli -s=patent-private close
```
