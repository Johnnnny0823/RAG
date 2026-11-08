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
