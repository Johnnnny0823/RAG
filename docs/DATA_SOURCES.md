# TIPO 官方資料來源

核對日期為 2026-11-09（Asia/Taipei）。實測限於一個最新期索引、少量查詢樣本及個別檔案。主入口為 [智慧財產局專利商標開放資料下載網站](https://cloud.tipo.gov.tw/S220/opdata)。

| dataset_name | official_url | publisher | checked_at | coverage | format | update_frequency | license/terms | access_method | rate_limits | example_record | parser_version | known_gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 發明公開說明書(1案1XML檔) | [政府目錄 15996](https://data.gov.tw/dataset/15996)、[TIPO 資料集](https://cloud.tipo.gov.tw/S220/opdata/detail/InventionPubXML) | 經濟部智慧財產局 | 2026-11-09 | 臺灣發明公開說明書及其期別索引。本次索引為第 24 卷第 19 期，共 2,384 筆。 | UTF-8 XML。索引與個案說明書使用不同根元素。 | 政府目錄列每月。索引只反映下載時回傳的期別。 | [政府資料開放授權條款第 1 版](https://data.gov.tw/license) | [HTTPS 最新期索引](https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S10)、個案檔循 TIPO 指定 FTPS 連結。 | 未見可確認的 HTTP／FTPS 每秒或每日配額。 | 申請號 `113133932`、公開號 `202639611`。個案 XML 有 19 項請求項。 | 以匯入程式寫入的版本為準。官方樣本 DTD 版本為 `A103.1.0`。 | 索引含摘要與書目，請求項和說明書段落須另取個案檔。索引不直接給每筆完整日期或個案 FTPS 路徑，FTPS 舊連結可能失效。 |
| 發明公開案 | [政府目錄 41663](https://data.gov.tw/dataset/41663)、[TIPO API 目錄](https://cloud.tipo.gov.tw/S220/opdata/detail/API02) | 經濟部智慧財產局 | 2026-11-09 | 臺灣發明公開案書目。官方 API 說明以申請案號前三碼自 062 起及已公開案件界定範圍。 | UTF-8 XML、JSON 或計數，官方範例實測為 XML。 | 政府目錄列每月。官方 API 說明表 2 列每月 1 日、21 日；[TIPO 檔案資料集頁](https://cloud.tipo.gov.tw/S220/opdata/detail/PatentPub)列 6 日、21 日。先以實際發布的期別及擷取時間紀錄新鮮度。 | [政府資料開放授權條款第 1 版](https://data.gov.tw/license) | [官方 API 說明 PDF](https://cloud.tipo.gov.tw/S220/opdata/api/file/api/patent)、[Swagger 定義](https://cloud.tipo.gov.tw/S220/opdata/api/file/oas)。一般 API 需 TIPO 核發 `tk`；政府目錄提供公開前 10 筆範例連結。 | PDF 表 3 的 `top` 為 1–5,000，預設 25，這是單次回傳筆數。每秒與每日配額未確認。 | 2026-10-01 公開、2024-09-06 申請的 `202639611`／`113133932`，回傳個案 FTPS 連結。 | 本次僅驗證原始 XML。 | 書目 API 未提供請求項原文或可直接採用的 kind code。前 10 筆歷史案的個案連結皆空，近期案也可能回傳無法下載的路徑。範例憑證僅供本次小量驗證，不寫入 Git。 |

## 實測樣本與欄位

- [HTTPS 最新期索引 S10](https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S10) 回傳 HTTP 200，附件名稱 `index.xml`，15,253,438 bytes，SHA-256 `7befed78be2cc6067266f13afd4a34f6feca4730b9a717f3f99890d551da9b69`。該網址會隨期別更新，重抓時須計算實際檔案雜湊。[第 24 卷第 19 期 FTPS 索引](ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/index.xml) 回傳 `226`，檔案與 HTTPS 版本逐位元相同。`tw-patent-applications` 的宣告及實際筆數均為 2,384，公開號各異。案號在 `application-reference/document-id/doc-number`，公開號在 `publication-reference/document-id/doc-number`，另外有 `publication-number` 屬性。其餘欄位含 `volno`／`isuno`、中英文標題、IPC（保留來源分類版次屬性）、申請人／發明人及 `description/isu-abst[@lang]` 摘要。掃描完整索引未發現日期或請求項元素。
- 發明公開案 API 回傳 HTTP 200，`API/status=ok`，前 10 筆範例位於 `API/tw-patent-pub/patentcontent`。精確查詢公開號 `202639611` 回傳 `notice-no=202639611`、`appl-no=113133932`、`notice-date=2026/10/01`、`appl-date=2024/09/06`，以及下方說明書路徑。日期來自書目 API；說明書根元素的 `filing-date=20250217135940` 與書目申請日不同，應獨立保存來源語義。
- [個案說明書 FTPS 檔](ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/2419202639611/113133932-A0304.xml) 經匿名 implicit FTPS（990，驗證 TLS 憑證，資料連線重用控制連線的 TLS session）回傳 `226 Transfer complete`。傳輸 118,139 bytes，符合 `SIZE`，SHA-256 為 `0537aedd633f9c63e7fe06790732cb0bf06e240e0bebf360c725abf9bc98d70a`。XML 可完整解析，根元素 `invention-specification` 的 `application-num` 為 `113133932`，與索引一致。`claims/claim` 有 `num`、`dependency` 及混合內容的 `claim-text`。說明書段落如 `description/technical-field/p[@general]` 可保存段落識別。原檔有外部 DTD 宣告，匯入程式須關閉外部資源載入與實體擴展。
- [同一期別的 FTPS `index_all.xml`](ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024019/index_all.xml) 回傳 `226`，檔案大小 16,470,926 bytes，SHA-256 為 `2b338d71f59e0de4d987bd3651f0b9044f64182fab6bcda664beae57467a728f`。2,384 個公開號及其順序與 S10 相同，每筆都有唯一的 `specification-files/@xml-file`，且皆屬該期目錄。首筆相對路徑與該資料集年份目錄 `/InventionPubXML/115` 組合後等於上方已成功下載的個案網址。這提供無須 API 憑證的個案連結探索方式。此清單的其他個案檔案可用性與其他期別的路徑規則仍待檢查。
- [官方 FTP 操作教學](https://cloud.tipo.gov.tw/S220/opdata/information/ftp)說明可使用工具下載期別目錄。本機 curl 對上述說明書兩次收到最後狀態 `426`，即使檔案雜湊相同也應視為失敗並改用能成功完成傳輸的客戶端。另一個 2026-10-16 近期案的說明書連結回傳 `550 No such file`；同案書目 XML 可成功下載。因此，個案連結和實際可用性須分開紀錄。

## 使用與歸屬

- 2026-11-09 另取得 [第 24 卷第 18 期 FTPS 索引](ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024018/index.xml)。傳輸完成且檔案大小符合官方 FTPS `SIZE`，共 12,667,509 bytes，SHA-256 `96c0ac33d8ece8da926dec02432d54ff1dca46678c90adb4d84cbf822df2be3c`，索引宣告及實際皆為 1,984 筆。匯入首 25 筆書目驗證跨期增量，並保存該官方 URL。

- 2026-11-09 核對 [專利說明書(1案1XML檔)目錄](https://data.gov.tw/dataset/15987)。提供者為經濟部智慧財產局，目錄列每月更新及政府資料開放授權第 1 版。官方 [最新期 S01 XML 索引](https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S01) 回傳第 53 卷第 28 期共 1,640 筆，15,590,834 bytes，SHA-256 `f8268c23fa3032d81841819135f3f3089c7b10d447ec00f83330a73459a0c84e`。解析器從 `tw-patent-grants/tw-patent-grant` 核對公告號、證書號、申請號及 `claims/claim[@num]`。已驗證公告號 `I941082` 有 13 項請求項，其申請號 `114106690` 與公開案 `202640162` 相同。此次匯入的公告來源範圍為書目和請求項。下載頻率限制未確認。
- 2026-11-09 由公開清單選取 20 筆個案，Windows 主機在驗證 TLS 憑證下全部成功下載。容器預設信任鏈驗證未通過，使用主機快取可離線匯入。2026-11-10 查明原因是伺服器未送出交叉憑證，下載程式已隨附，見 [決策](DECISIONS.md#m6-tipo-ftps-憑證鏈)。20 份有 17 份通過全文解析，3 份來源的 `claim` 缺 `num`，保存原檔與錯誤並保留書目。

保存提供機關、資料集名稱、釋出年份與期別、授權網址、擷取時間與原檔雜湊。後續在詳情及報告呈現政府資料授權所需的顯名聲明。授權範圍不包括專利權及商標權；書目與公開說明書不提供即時法律狀態結論。樣本原檔含公開個人資料欄位，留在未追蹤的資料目錄，正式顯示與索引僅選取產品需要的欄位。 [官方授權及顯名聲明格式](https://data.gov.tw/license)

## 公告期別的固定封存檔

2026-11-10 以匿名 FTPS 列出官方目錄，確認 `專利說明書(1案1XML檔)` 的各期封存位於 `/PatentIsuRegSpecXMLA/<民國年>/PatentIsuRegSpecXMLA_<卷期>/`，115 年目錄當日有第 53 卷第 1 至 31 期。[第 53 卷第 28 期封存索引](ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053028/index.xml) 回傳 `226`，15,597,462 bytes 符合 `SIZE`，SHA-256 `60936a7ab763fbb8bd79b8a3071aa89d43da3ffe4ef65928734a9ddc70827a4a`。

這份封存檔與 2026-11-09 由 S01 最新期端點取得的副本（15,590,834 bytes，`f8268c23…`）不是同一個檔案。兩者解析出的公告 `I941082` 都是申請號 `114106690`、13 項請求項，請求項文字逐字相同，該筆紀錄的其他 XML 內容有差異。可重建的測試語料固定使用封存檔及其雜湊。同目錄另有 `index_all.xml` 和以申請號命名的個案 XML，本次未下載或解析。`PatentIsuRegSpecXMLB` 目錄的同期 `index.xml` 大小相同，未比對內容。

可重建語料另固定第 24 卷第 19 期 `index_all.xml` 及索引前 20 筆的個案說明書，各檔雜湊列於 [種子腳本](../scripts/seed_tipo_e2e.py)。這些雜湊來自 2026-11-09 驗收資料庫保存的原始物件紀錄。

2026-11-10 重新以匿名 FTPS 取得第 24 卷第 19 期索引與公開案 `202639611` 個案 XML，兩者 SHA-256 均符合上列固定值。獨立 E2E 卷只匯入這一案，核對資料庫的 19 項請求項和 122 段說明書與封存 XML 一致。政府目錄當日仍標示每月更新、免費與政府資料開放授權條款第 1 版。[政府資料開放平臺](https://data.gov.tw/dataset/15996)

## 公報書目的申請日、公開日與公告日

2026-11-26 核對政府目錄與匿名 FTPS 封存檔。兩項資料由智慧財產局提供，政府目錄列免費、每月更新、政府資料開放授權條款第 1 版。FTPS 每秒與每日配額未確認。

| 資料集 | 固定卷期與格式 | 下載驗證 | 可核對的範例 |
| --- | --- | --- | --- |
| [發明公開公報書目](https://data.gov.tw/dataset/9683) | [第 24 卷第 19 期 pubinvention.xml](ftps://ftp.tipo.gov.tw/PatentPubRegXMLB/115/PatentPubRegXMLB_024019/pubinvention.xml)，2,384 筆 | 17,322,532 bytes，`5eb3c531a3795e685f802289195da4f1779b8ca9eefef3e2f13ea8a85e634558` | `202639611`／`113133932`，公開 2026-10-01，申請 2024-09-06 |
| [專利公告公報書目](https://data.gov.tw/dataset/15972) | [第 53 卷第 28 期 patent.xml](ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLB/115/PatentIsuRegSpecXMLB_053028/patent.xml)，1,640 筆，含 1,095 筆發明公告 | 23,778,073 bytes，`836c3c9db01099dfe38fa1d15e9e1d3116180126c02f5179ebcf17542c7bd5c8` | `I941082`／`114106690`，公告 2026-10-01，申請 2025-02-24 |

`tipo-gazette-dates-1` 按同卷期、申請號及文件種類與編號對應已匯入版本。日期取 `application-reference/document-id/date` 與 `publication-reference/document-id/date`，把來源民國日曆轉成 PostgreSQL `date`。保留原始 XML、SHA-256 及書目 XPath。此來源用於日期補齊，缺少公報書目的既有版本仍可能無日期。

## 專利權異動公報

2026-11-26 查核[專利權異動公報（15974）](https://data.gov.tw/dataset/15974)。提供者經濟部智慧財產局，目錄列每月更新、免費及政府資料開放授權條款第 1 版。[最新期索引 P10](https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/P10) 實得 1,662 筆、214,092 bytes，SHA-256 `3945c07fd8f2b286e00dac8d46c67faf849c998f3c89009b3eec75ebc2226299`。索引列申請號、證書號及異動種類，日期及更正欄位須讀該卷期的類別 XML。FTPS 速率限制未確認。

第 53 卷第 33 期的匿名 FTPS 封存實測如下。

| 類別 | 原檔大小與 SHA-256 | 可取得欄位 |
| --- | --- | --- |
| [消滅公告 sud08](ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053033/sud08.xml) | 469,608 bytes，`213b98e7337a0f99b74b9eff59ce0d92f0f27ccecf665892f8ee48b8423bd964` | 1,482 筆，含 838 筆發明。申請號、證書號、卷期、消滅日與原因。 |
| [公報更正 sud24](ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053033/sud24.xml) | 41,156 bytes，`97993734e1cd87b54537069ded8593a02615d7aa09442779a47a688ccffc16a3` | 35 筆，含 31 筆發明。申請號、證書號、卷期與更正欄位。公開 API 只使用欄位名稱。 |

`tipo-sundry-events-1` 保留原檔、雜湊及 XML 位置，解析時移除完全符合官方樣本的外部 DTD 宣告，其他 DTD 一律拒絕。僅將可核對申請號的發明事件關聯至已匯入的臺灣案件。事件表示公報記載的歷史事項，來源涵蓋範圍以已匯入期別為限。

2026-11-26 交叉核對 [第 52 卷第 6 期公告索引](ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/114/PatentIsuRegSpecXMLA_052006/index.xml) 與第 53 卷第 33 期消滅公告。公告索引有 1,780 筆，16,989,536 bytes，SHA-256 `99cde994594aa622cf9469ecb6541403b3567b4597342a6915c35ce5dab526f8`。證書 `I874215` 和申請號 `113117471` 在兩個原檔一致。公告索引提供 9 項請求項，消滅公報的第 1447 筆記載消滅日 2026-02-21，原因為「未依限繳費」。公告索引屬官方卷期彙整 XML，匯入器允許 32 MiB 上限。個案說明書維持 16 MiB 上限。

[專利權狀態異動資料（發明，30126）](https://data.gov.tw/dataset/30126) 是另一資料來源，官方 [OpenAPI 文件](https://cloud.tipo.gov.tw/S220/opdata/api/file/oas) 列 `/PatentRights` 及 `tk` 欄位。任意案件的最新狀態查詢與授權憑證仍待驗證。此階段使用匿名可取得、可保留原文的固定卷期事件。
