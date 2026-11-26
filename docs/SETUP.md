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

## 靜態前端部署

使用支援 `!reset` 的 Docker Compose。先將 `.env.example` 複製到 `.env`，為新資料卷設定專用的 PostgreSQL 密碼，並設定需要的本機 Ollama 模型與摘要。相同資料卷的資料庫帳密須和初始化時一致。

```powershell
$env:WEB_PORT = '18123'
$deployArgs = @('-f', 'docker-compose.yml', '-f', 'docker-compose.deploy.yml', '-p', 'patentscope-deploy')
docker compose @deployArgs up -d --build --wait --wait-timeout 180
python scripts/smoke.py --api http://127.0.0.1:18123 --web http://127.0.0.1:18123 --deployment
```

瀏覽器使用 `http://127.0.0.1:18123`。Nginx 提供已編譯的靜態檔，API 透過同源 `/api/v1/` 代理。API、背景工作與 PostgreSQL 沒有主機連接埠。全新資料卷會先遷移。依下節使用同一 Compose 專案匯入官方資料，再建立詞彙與向量索引。匯入可沿用同一組 `$deployArgs` 呼叫 `run`。

部署冒煙驗收會核對網頁的安全標頭。內容安全政策限制前端資源來源、內嵌物件與框架載入。套件內容新增外部資源前需更新政策並重跑瀏覽器測試。

正式 Nginx 依直接連線來源 IP 套用兩組速率限制。登入、註冊及以密碼確認的帳號刪除合計每分鐘 30 次，可額外突發 6 次。技術分析、搜尋、比對、Session 訊息及產生 PDF 合計每分鐘 120 次，可額外突發 12 次。健康檢查、工作進度及一般文件讀取照常由 API 處理。入口拒絕會回傳 JSON `RATE_LIMITED` 和 HTTP 429。

如果前面再加反向代理，同一代理的使用者會共用來源配額。實際外部部署應依可信代理拓樸配置來源識別並重新驗收，勿直接信任客戶端提供的轉送位址。

匯入公開文件 `202639611` 的全文並索引後，建立測試帳號，輸入「光硬化性樹脂組成物」。執行 AI 拆解後保留該技術特徵，選擇「搜尋並保存」，再開啟該文件的全文版本執行「比對並保存證據」及「匯出 PDF 報告」。在瀏覽器網路面板可核對回應的 `application/pdf` 與 `Cache-Control: private, no-store`。

此設定綁定回環位址。跨裝置使用時可啟用下列 HTTPS 覆蓋檔，並依主機拓樸管理防火牆、存取及備份。

### 使用自備憑證啟用 HTTPS

準備與部署網域相符的 PEM 憑證鏈和私鑰，放在版本庫之外。使用支援 `!override` 的 Docker Compose，將 HTTPS 覆蓋檔放在靜態部署覆蓋檔之後。

```powershell
$env:TLS_CERTIFICATE_FILE = 'C:/secure/patentscope/fullchain.pem'
$env:TLS_KEY_FILE = 'C:/secure/patentscope/privkey.pem'
$tlsArgs = $deployArgs + @('-f', 'docker-compose.tls.yml')
docker compose @tlsArgs up -d --build --wait --wait-timeout 180
```

預設只將 HTTPS 發布在 `127.0.0.1:18443`。對外部署時設定 `TLS_BIND_ADDRESS` 為指定對外介面、`TLS_PORT` 為對外連接埠，並依憑證網域及連接埠執行 `scripts/smoke.py --deployment`。如果由內部 CA 簽發，可加 `--ca-file <CA 憑證>` 進行憑證及主機名稱驗證。API、資料庫和工作程序沒有主機連接埠，API 僅信任隔離容器網路上的代理標頭。憑證續期後以相同參數執行 `docker compose @tlsArgs up -d --no-deps --force-recreate web`，再重跑 HTTPS 冒煙。外部網域、公開 CA 續期與防火牆仍須在目標主機驗證。

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

## 從官方公報書目補齊日期

先匯入指定卷期的官方公開或公告文件，再執行日期補齊。操作員需使用具有匯入權限的 Compose `migrate` 服務。下列指令以固定驗收語料的兩個卷期為例，可用同一 Compose 專案重跑。

```powershell
docker compose run --rm migrate python -m services.ingestion.gazette_dates --stage publication --year 115 --issue 024019
docker compose run --rm migrate python -m services.ingestion.gazette_dates --stage grant --year 115 --issue 053028
```

程式下載官方固定卷期 XML，核對階段、卷期、申請號及文件號，將缺少的日期與其來源在同一資料庫交易保存。若同案已有不同日期，該交易會回滾，需核對來源。再次執行相同檔案不會新增版本或重複來源連結。既有檢索索引可繼續使用，日期篩選從 PostgreSQL 欄位讀取。公開及公告的來源見 [資料來源](DATA_SOURCES.md#公報書目的申請日公開日與公告日)。

## 匯入官方異動公報

先匯入要關聯的官方發明案件，再對相同 Compose 專案執行。下列第 53 卷第 33 期用於驗證消滅與更正 XML。操作員可依實際取得的官方卷期重跑。事件只會關聯已存在的同申請號案件，重跑同一檔案不會重複新增。

```powershell
docker compose run --rm migrate python -m services.ingestion.legal_events --year 115 --issue 053033 --type sud08
docker compose run --rm migrate python -m services.ingestion.legal_events --year 115 --issue 053033 --type sud24
```

輸出含該公報發明事件數、配對數、新增數與原檔雜湊。舉例來說，對隔離索引前 500 筆公開書目執行第 53 卷第 33 期更正匯入，可核對公開案 `202639186` 和 `202639081`。 [原始資料](DATA_SOURCES.md#專利權異動公報)

要驗證具日期的消滅紀錄，先從官方固定卷期下載並校驗第 52 卷第 6 期索引，再將公告案 `I874215` 匯入相同隔離環境。以 Windows PowerShell 為例，使用一個尚未存在的 `index-052006.xml` 檔名。

```powershell
$grantUrl = 'ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/114/PatentIsuRegSpecXMLA_052006/index.xml'
$rawDir = Join-Path (Get-Location).Path '.patent-data/gazette-check'
New-Item -ItemType Directory -Path $rawDir -Force | Out-Null
$grantFile = Join-Path $rawDir 'index-052006.xml'
python -m services.ingestion.download --index-url $grantUrl --index-out $grantFile
if ((Get-FileHash -LiteralPath $grantFile).Hash.ToLowerInvariant() -ne '99cde994594aa622cf9469ecb6541403b3567b4597342a6915c35ce5dab526f8') {
    throw 'Unexpected official grant index checksum'
}
docker compose run --rm -v "${rawDir}:/inputs:ro" migrate python -m services.ingestion.import_issue --verified-tipo --index /inputs/index-052006.xml --index-source-url $grantUrl --batch 052006 --grant-number I874215
docker compose run --rm migrate python -m services.ingestion.legal_events --year 115 --issue 053033 --type sud08
docker compose run --rm migrate python -m services.retrieval.index_lexical
docker compose run --rm migrate python -m services.retrieval.index_semantic
```

上述命令請在已有 `.env` 的隔離 Compose 專案執行，依嵌入設定準備本機模型。原始 XML 應放在未追蹤的資料目錄。讀取前會依來源類別套用 XML 上限。

同一資料庫和嵌入模型版本同時只接受一個向量索引程序。若指令回報 `This embedding model is already being indexed`，待既有工作結束後重跑。已完成的文件版本會被略過。

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

可用「動態導通電阻」、IPC `G01R`、文件種類「公開」及申請人「陽明交通」驗證篩選，應可找到公開 `202640162`，不會出現公告 `I941082`。當前期別樣本未匯入官方公開／公告日期，日期篩選會排除未知值。起日大於迄日時應顯示錯誤。後端可用 `python scripts/smoke_hybrid.py --api http://127.0.0.1:18010` 驗證三種檢索模式的篩選。

要並排核對原文，先從同一次搜尋開啟公開 `202640162` 的全文版本，執行比對，再開啟公告 `I941082` 的請求項版本並比對。矩陣應出現兩個文件版本欄，展開儲存格可檢查引文與原文定位。以「搜尋並保存」開始的流程可在重新登入後從歷史重開矩陣。

保持上方的 API 運行。從 `apps/web` 執行下列指令，開啟 `http://127.0.0.1:18110`。

```powershell
npm ci
$env:API_PROXY_TARGET = 'http://127.0.0.1:18010'
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 18110 --strictPort
```

輸入「動態導通電阻」並執行 AI 拆解。將特徵描述改為「動態導通電阻量測電路」，保留同名繁中檢索詞，並設定 IPC 為 `G01R`。搜尋並開啟公開文件 `202640162` 的全文版本，確認請求項、說明書與來源，再比對並展開原文定位。改用 `A01B` 驗證空結果，輸入 `INVALID` 驗證錯誤訊息。結果取決於當前語料、模型與已確認特徵。

私人歷史、專案歸檔與管理、收藏、筆記及 AI Session 可用 Playwright CLI 驗收。啟動前先對同一個隔離專案執行 `docker compose -p $project run --rm --build migrate`，並重建 API，使資料庫與 API 都包含 `0009_session_message_cascade`。以下命令由專案根目錄執行，會建立兩個測試帳號，並驗證刪除本次建立的搜尋、Session、收藏及空白專案。

```powershell
npx --yes --package @playwright/cli@0.1.23 playwright-cli -s=patent-private open http://127.0.0.1:18110
npx --yes --package @playwright/cli@0.1.23 playwright-cli -s=patent-private run-code --filename scripts/smoke_private_browser.js
npx --yes --package @playwright/cli@0.1.23 playwright-cli -s=patent-private close
```
## M5 私人 PDF 驗收

### 私人內容的存放範圍

Compose 開發環境預設只把 Web 與 API 映射到本機回環位址。模型傳輸限制為設定的本機 Ollama 位址，拒絕重新導向及環境代理，並核對模型摘要。模型仍會收到執行所需的構想、檢索詞或比對片段。Ollama 程序與主機端的記錄、存取及備份由部署者管理。

`MODEL_MAX_CONCURRENT` 設定單一 API 工作程序可同時執行的模型操作，預設 2，可設為 1–32。修改後需重啟 API。每個工作程序各有自己的限制，多個執行個體應依模型主機容量設定。離線建索引、直接呼叫 Ollama 及跨程序的請求配額需由部署者獨立管理。

登入後可在研究頁選擇「匯出我的研究資料（JSON）」下載已保存的研究資料。匯出檔可能含未公開構想與筆記，請保存在本人可控的位置。

瀏覽器只在頁面記憶體保留憑證。登出撤銷當前憑證。已保存的搜尋、AI Session、收藏與筆記留在 PostgreSQL 資料卷，尚無自動保留期限。可在研究頁面逐筆移除，也可展開「刪除帳號與私人資料」，重新輸入密碼以清除帳號及其全部私人研究資料與登入憑證。已下載的 PDF 與部署者備份須在各自位置管理。

### Windows 全新資料卷啟動

若多服務同時建置在含非 ASCII 字元的路徑遇到 BuildKit gRPC header 錯誤，可分開建置後再啟動。以下使用獨立專案與連接埠驗證空資料卷，不會匯入專利語料。

```powershell
$env:API_PORT = '18019'
$env:WEB_PORT = '18119'
docker compose -p patentscope-m5-clean build migrate
docker compose -p patentscope-m5-clean build api
docker compose -p patentscope-m5-clean build web
docker compose -p patentscope-m5-clean up -d --no-build --wait
python scripts/smoke.py --api http://127.0.0.1:18019 --web http://127.0.0.1:18119
```

重建 API 映像以安裝 ReportLab 及 AR PL UMing 臺灣字型。從私人歷史開啟已保存搜尋，完成至少一份候選比對，點選「匯出 PDF 報告」。在 Windows 直接執行 API 時，將 `REPORT_FONT_PATH` 設為可嵌入的繁中字型 TTF 或 TTC 路徑。自訂 TTC 可用 `REPORT_FONT_INDEX` 選擇字型。

以隔離語料執行 `python scripts/smoke_search_runs.py --api http://127.0.0.1:18017 --pdf-output <驗收路徑.pdf>`，核對擁有者可下載，訪客及其他帳號無法取得。腳本會建立兩個測試帳號及公開測試紀錄。
## 原始 XML 持久保存、備份及還原

Compose 的 `migrate` 容器將原始物件儲存在專案自己的 `patent-objects` 資料卷。依前述步驟準備官方輸入檔，再把檔案目錄掛載至 `/inputs:ro`。匯入和驗證可以省略 `--objects`，容器會使用資料卷。既有流程若明確指定 `--objects`，仍使用指定目錄，適合獨立測試。請保留資料卷，避免使用 `docker compose down -v`。

以下 PowerShell 範例使用已套用遷移的 Compose 專案。將 `$backup` 設成備份裝置上已建立的絕對路徑。備份期間暫停匯入，先將 PostgreSQL 一併備份，再複製原始物件，讓兩份備份可配對。

```powershell
docker compose run --rm --no-deps migrate python -m services.ingestion.sync_objects
docker compose exec -T db pg_dump -U patentscope -Fc -f /tmp/patentscope-backup.dump patentscope
docker compose cp db:/tmp/patentscope-backup.dump (Join-Path $backup 'db.dump')
docker compose run --rm --no-deps -v "${backup}:/backup" migrate python -m services.ingestion.sync_objects --copy-to /backup
```

還原時，先把同一批 PostgreSQL 備份還原到獨立專案的新資料庫，然後將原始物件複製到該專案的資料卷。下列命令應在該獨立專案執行。

```powershell
docker compose up -d --wait db
docker compose build migrate
docker compose cp (Join-Path $backup 'db.dump') db:/tmp/patentscope-backup.dump
docker compose exec -T db pg_restore -U patentscope --exit-on-error --no-acl -d patentscope /tmp/patentscope-backup.dump
docker compose run --rm --no-deps migrate
docker compose run --rm --no-deps -v "${backup}:/backup:ro" migrate python -m services.ingestion.sync_objects --objects /backup --copy-to /var/lib/patentscope/objects
docker compose run --rm --no-deps migrate python -m services.ingestion.sync_objects
docker compose run --rm --no-deps migrate python -m services.ingestion.verify_document 202639611
```

最後一個指令適用於已匯入 `202639611` 全文的語料。校驗指令會依資料庫逐筆核對物件大小及 SHA-256，也包含已隔離、但留有原始檔記錄的物件。遇到遺失或損毀會以非零狀態退出，已成功複製的檔案可保留供重跑。舊物件目錄可按同樣方式掛在 `/backup:ro` 搬入；若缺少原始位元組，需從原來源找回與資料庫雜湊相符的檔案。未列入資料庫的下載快取不在備份範圍。

範例使用預設資料庫名稱和帳號 `patentscope`。若已自訂，請調整 `-U` 與資料庫名稱。每次備份使用新目錄，並將備份視同私有資料庫管理，因為其中也包含研究紀錄。
## 主要操作日誌

在隔離或正式部署中可執行 `docker compose logs api search-worker` 查看操作紀錄。API 的 `api_activity` 事件列出方法、路由樣板、HTTP 狀態與耗時。背景工作送入資料庫的最終狀態後，會輸出 `search_job_finished` 或 `report_job_finished`。請求內容、實際路徑參數、帳號、令牌與報告內容不會寫入這些事件。

API 容器已關閉原始 Uvicorn 存取日誌。Compose 的 API 日誌每檔最多 10 MiB，保留最多三檔。工作程序與代理的診斷日誌仍需由部署者配置留存、存取與傳輸。

## PostgreSQL 執行帳號

Compose 在遷移完成後建立 `patentscope_api` 並授權。API 使用這個帳號讀取專利與索引，並依功能存取研究資料。遷移與離線匯入則使用 `POSTGRES_USER`。API 的容器環境只取得自己的資料庫密碼。

既有環境須在 `.env` 新增獨立的 `API_DB_PASSWORD`，然後用原專案名稱執行 `docker compose up -d --build --wait`。沿用既有 PostgreSQL 磁碟卷及管理帳密。變更 API 密碼時，先更新設定並執行 `docker compose run --rm migrate`，再重建 API 容器。若宿主機直接啟動 API，`PGUSER` 與 `PGPASSWORD` 應改用對應的執行帳號與密碼。

使用 `patentscope_api` 作為本專案專用角色。若同一 PostgreSQL 叢集已存在同名帳號，先核對既有角色及授權再執行，因為重新配置會設定該角色的密碼。API 的各使用者資料仍依應用層的所有權檢查及資料庫約束隔離。
## 背景搜尋工作程序

一般 `docker compose up -d --build --wait` 會啟動 `search-worker`，並在資料庫遷移後開始取件。若只啟動 `api web`，也須執行 `docker compose up -d --build search-worker` 才會處理背景搜尋。工作程序使用與 API 相同的資料庫執行角色與模型設定。

`docker compose stop search-worker` 會讓工作程序完成手上的搜尋或 PDF 工作後退出。Compose 最長等待三分鐘。逾時、程序當機或主機斷電時，既有工作逾時機制會在工作程序再次運行後標記中斷的工作。

目前預設一個工作程序，每次處理一項搜尋。工作程序會將等待超過 10 分鐘或執行超過 6 分鐘的工作標為逾時，並於完成狀態保存一日後清理工作狀態。成功的研究紀錄有自己的生命週期，可以持續從歷史查看。

同一工作程序也處理私人 PDF 匯出，每輪各取一項搜尋與報告（若有）。自訂字型時，API 容器與工作程序需採用相同設定。PDF 在資料庫暫存一小時，刪除來源搜尋時會一併清除。
## 官方匯入與索引監控

### 更新最新發明公開書目

有網路時可先預覽官方 S10 回傳的卷期、筆數和雜湊。預覽不寫入資料庫。加上 `--apply` 後才會保存來源 XML、匯入書目並預設補建詞彙索引。此命令的 `--limit` 預設 100，允許 1–500 筆。

```powershell
docker compose run --rm --build migrate python -m services.ingestion.latest_publication --limit 5
docker compose run --rm migrate python -m services.ingestion.latest_publication --apply --limit 5
```

同一份來源和相同匯入上限可重跑，既有批次與索引會重用。追蹤工作會把只有書目摘要的批次列為部分完成。若已設定嵌入模型，可用 `--index-mode hybrid` 同時補建向量。

要匯入全文，按已查證的封存目錄指定三位數民國年。命令會取得同一卷期的 `index_all.xml`，核對所選公開號、申請號及個案路徑。以下是第 024020 期驗收用的民國年。使用前先確認 S10 當下的卷期仍在該年目錄。

```powershell
docker compose run --rm migrate python -m services.ingestion.latest_publication --archive-year 115 --limit 2
docker compose run --rm migrate python -m services.ingestion.latest_publication --archive-year 115 --apply --limit 2
```

預覽只確認清單與所選書目的對應。套用時才下載個案全文並建立索引。部分個案取得或解析失敗時，已驗證資料會保留並顯示部分完成，命令以非零代碼回報。若部署容器無法連到官方 FTPS，可先依 [以官方清單補入全文](#以官方清單補入全文) 在可連線的主機下載，再由既有匯入命令處理。

### 定期更新

在已設定的 Compose 部署中，可選用 `patent-refresh` profile。下例用開發 Compose 執行。在正式部署環境中請沿用該專案的 `-p`、`--env-file` 和部署覆蓋檔。

```powershell
docker compose --profile patent-refresh up -d --build patent-refresh
docker compose --profile patent-refresh logs --tail 30 patent-refresh
docker compose --profile patent-refresh stop patent-refresh
```

服務啟動先執行一次。預設成功後等 24 小時，失敗後等 15 分鐘再試。可用 `TIPO_REFRESH_INTERVAL`、`TIPO_REFRESH_RETRY_INTERVAL`（秒）、`TIPO_REFRESH_LIMIT` 和 `TIPO_REFRESH_INDEX_MODE` 設定，預設取 100 筆並補詞彙索引。要定期補全文，另設定已核對的 `TIPO_REFRESH_ARCHIVE_YEAR`。跨民國年度時請重新核對封存目錄並更新該值；錯誤年份會使該次全文更新失敗。設定變更後需重新建立容器。

排程輪詢 S10 當次提供的卷期。停機期間可能錯過中間期別，可用[封存卷期補匯](#封存卷期補匯)補齊。各次匯入可在管理員監控查閱，來源取得失敗也可在容器日誌查到。

若要在同一服務內另外更新公告，設定 `TIPO_REFRESH_INCLUDE_GRANTS=yes` 並重新建立容器。S01 及 S10 會各自驗證卷期與來源，各取設定上限。任一來源失敗時，另一來源仍可執行，下一輪使用重試間隔。公告預設保存書目與請求項；如有設定該年官方封存目錄，亦可補建全文。

可另設 `TIPO_REFRESH_GAZETTE_YEAR=115`，讓每期匯入後以同卷期官方公報補上申請、公開或公告日期。此設定預設留空，可獨立於全文封存年度設定。單次操作以 `latest_publication --gazette-year 115` 預覽公報網址與雜湊，加上 `--apply` 才寫入。下載及卷期驗證在書目寫入前執行。若後續日期與已存資料衝突，該次日期寫入會回滾，先前成功匯入的書目版本仍可查閱。跨年度須更新設定。

公告也可單次預覽及執行。省略證書號時，依 S01 順序取前幾件發明公告；可重複指定 `--grant-number` 選取實際案例。

```powershell
docker compose run --rm migrate python -m services.ingestion.latest_publication --grants --limit 3
docker compose run --rm migrate python -m services.ingestion.latest_publication --grants --apply --limit 3
```

### 封存卷期補匯

以官方 FTPS 目錄核對民國年、資料類型與指定範圍。預覽只列計畫卷期，範圍缺任一期會以錯誤退出。每次可指定同一卷內最多 20 個連續期別。以下兩期使用第 53 卷公告的封存資料。

```powershell
docker compose run --rm migrate python -m services.ingestion.archive_backfill --stage grant --year 115 --from-issue 053031 --through-issue 053032 --limit 1
docker compose run --rm migrate python -m services.ingestion.archive_backfill --stage grant --year 115 --from-issue 053031 --through-issue 053032 --limit 1 --apply
```

每期依官方索引順序取 `--limit` 筆，公告只選發明。預設補公開書目摘要或公告請求項並建立詞彙索引。`--fulltext` 使用同年的個案封存清單，`--dates` 使用同期日期公報，`--index-mode hybrid` 可另建向量。某期失敗時停止，已提交的期別保留，重跑相同選擇可重用既有批次。這項補匯以指定範圍和每期上限為準，涵蓋範圍不等於完整卷期。

#### 排程自動補期

啟用前先以 `archive_backfill` 預覽核對起始卷期。以民國 115 年發明公告為例，設 `TIPO_REFRESH_CATCH_UP_YEAR=115`、`TIPO_REFRESH_INCLUDE_GRANTS=yes`、`TIPO_REFRESH_GRANT_FROM=053031` 並重新建立 `patent-refresh` 容器。公開可獨立設定 `TIPO_REFRESH_PUBLICATION_FROM`。設有起始卷期的資料類型會依同年、同卷的官方 FTPS 封存目錄順序處理，其他資料類型沿用最新索引。

每輪每種資料預設最多補 2 期，可用 `TIPO_REFRESH_CATCH_UP_MAX_ISSUES` 調整。尚有待補、缺期或匯入失敗時採重試間隔。缺期之後的卷期會等該期恢復後再補。每期成功完成指定匯入、索引與日期步驟後，才寫入 PostgreSQL 進度。重啟會跳過同設定已完成的期別。變更案件上限、索引模式或模型版本等條件時，同一期會依新設定重新評估。這項設定預設關閉，跨年或換卷需設新起點。已完成期別如有修訂可手動重跑封存匯入。

#### 最新異動公報定期更新

設定 `TIPO_REFRESH_LEGAL_YEAR=115` 並重建 `patent-refresh` 容器，可在每輪更新中納入官方異動公報。也可先獨立執行預覽。

```powershell
docker compose run --rm migrate python -m services.ingestion.legal_refresh --year 115
docker compose run --rm migrate python -m services.ingestion.legal_refresh --year 115 --apply
```

服務將 P10 原檔與該年度最近 8 期的封存索引逐位元比對，再核對消滅公告及更正公報的發明案件清單和原文卷期。無法核對時以錯誤回報並按重試間隔重試。只有可對應既有申請案的事件會加入詳情，重跑可補上新匯入案件並避免重複。設定預設留空，跨年度須更新。歷史卷期仍可使用既有指定期別命令。來源只涵蓋這兩類公報及其已匯入案件，個案即時權利狀態須另外向官方查證。

#### 歷史異動公報補匯

可用封存索引與類別 XML 核對單一期別。同一指令拿掉 `--apply` 只預覽。

```powershell
docker compose run --rm migrate python -m services.ingestion.legal_refresh --year 115 --archive-issue 053032 --apply
```

若要定期補匯，另設 `TIPO_REFRESH_LEGAL_FROM=053032`。服務會從同年同卷的起始期依序核對封存，沿用 `TIPO_REFRESH_CATCH_UP_MAX_ISSUES` 限制每輪期數，並以 PostgreSQL 記錄成功期別。歷史補匯發生錯誤時，最新 P10 仍會繼續核對。歷史期別已完成後才匯入的案件，可用上列單期命令重新配對。

### 追蹤匯入及建立索引

同一卷期的發明公告可以在一個工作中匯入多件。先以 `python -m services.ingestion.download --latest-grants --index-out <本機輸出路徑>` 下載 S01。核對原檔記載的卷期及欲匯入的證書號後，把檔案目錄唯讀掛到 `/inputs`。以下以第 053030 期為例。

```powershell
docker compose run --rm -v "${inputs}:/inputs:ro" migrate python -m services.ingestion.run_pipeline --index-mode lexical -- --verified-tipo --index /inputs/s01.xml --index-source-url https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S01 --batch 053030 --grant-number I942697 --grant-number I942698
```

每件保留獨立的公告版本和原文請求項定位。選取的證書號必須全部出現在同份索引。對同一原檔、同一批證書號重跑會重用批次，證書號順序不影響判定。

若要補入公告個案全文，先下載同一期的官方 `index_all.xml` 並保留原檔。以下範例使用已核對的第 053030 期封存清單。

```powershell
python -m services.ingestion.download --index-out "${inputs}/grant-index_all.xml" --index-url ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053030/index_all.xml
docker compose run --rm -v "${inputs}:/inputs:ro" migrate python -m services.ingestion.run_pipeline --index-mode lexical -- --verified-tipo --index /inputs/s01.xml --index-source-url https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S01 --batch 053030 --grant-number I942741 --grant-number I942850 --manifest /inputs/grant-index_all.xml --manifest-url ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053030/index_all.xml
docker compose run --rm migrate python -m services.ingestion.verify_document I942741 --grant-issue 053030 --grant-fulltext
```

全文版的請求項與說明書來自同一份個案原檔。已保存的 S01 請求項版仍可獨立查閱。個案檔取得或解析失敗時仍可保存可用的 S01 請求項，管理員監控會顯示部分完成。驗證 S01 請求項版時省略 `--grant-fulltext`。

先依前述官方樣本流程取得檔案並核對來源與 SHA-256。以下 PowerShell 範例以 `$inputs` 指定已有 `index.xml` 與 `spec.xml` 的絕對路徑，用已配置模型的 Compose 專案在背景執行。

```powershell
docker compose run -d --name patentscope-024019-import --no-deps -v "${inputs}:/inputs:ro" migrate python -m services.ingestion.run_pipeline --index-mode hybrid --embedding-batch-size 2 --embedding-timeout 180 -- --verified-tipo --index /inputs/index.xml --index-source-url ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/index.xml --spec 202639611=/inputs/spec.xml --batch 024019 --limit 20
docker logs -f patentscope-024019-import
```

`--index-mode` 可選 `none`、`lexical` 或 `hybrid`，預設為 `lexical`。索引處理本資料庫缺少的文件版本，因此新增索引筆數可能包含前次匯入的文件。將管理者自己的 `GET /api/v1/me` 回傳的 `id` 填入 `INGESTION_ADMIN_USER_IDS`，多個 UUID 以逗號分隔，再重建 API 容器。登入該帳號後，工作台可手動刷新最近的工作狀態。環境變數留空時，不授予任何帳號監控權限。

每次執行使用不同的容器名稱。跟著日誌時，中止終端等待不會停止背景容器。每個資料庫一次允許一條受監控的匯入流程。若容器異常中斷，下一次取得同一資料庫鎖的流程會把未結束的舊工作標成已中斷。匯入部分成功時仍保存可用資料，請依隔離與下載失敗筆數處理。既有單獨匯入／索引指令可繼續使用，其執行不會出現在這個監控清單。
