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
