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

### 同期新型與設計公告

2026-11-27 重新查核 [TIPO 發布的資料集 15987](https://data.gov.tw/dataset/15987)，目錄列免費、每月更新及政府資料開放授權條款第 1 版。重讀第 053028 期先前由官方 FTPS 取得的 `PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053028/index.xml`。原檔為 15,597,462 bytes，SHA-256 `60936a7ab763fbb8bd79b8a3071aa89d43da3ffe4ef65928734a9ddc70827a4a`，含 1,095 筆發明、349 筆新型及 196 筆設計公告。這些數字是完整來源索引筆數。

隔離驗收選入新型 `M687984`（申請號 `114206949`，16 項請求項及 IPC `A63B59/00`）及設計 `D246917`（申請號 `112306158`）。設計樣本在此索引只有書目，請求項、摘要、說明書及分類欄位皆缺，系統保留空值。這一流程使用 15987 的 S01 索引，支援指定公告號匯入及詞彙索引。[設計說明書與圖式審查基準](https://www.tipo.gov.tw/tw/patents/999-60597.html)

### 新型與設計個案說明書

2026-11-27 按同年 [053030 期清單](ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053030/index_all.xml)取到兩份個案。另重新下載[同期封存索引](ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053030/index.xml)，16,606,541 bytes，SHA-256 `9bb410efd13450866eaa0bc34523fce8785c46d11ce7237efee4cd0c3b3727f0`。資料集 15987 的更新與授權條件見上節。

| 版別 | 原檔、格式及驗收 |
| --- | --- |
| `M688679`，申請號 `114206535` | [個案 XML](ftps://ftp.tipo.gov.tw/PatentPubXML/115/PatentPubXML_053030/5330M688679/114206535-A0305.xml)，72,760 bytes，SHA-256 `adef492f39db89c809115dd68d028cbff178a3634fbcf11f38de3ab0739c3093`，DTD `1.0.0`。核對 208 段說明書及 10 項請求項。 |
| `D247328`，申請號 `113306657` | [個案 XML](ftps://ftp.tipo.gov.tw/PatentPubXML/115/PatentPubXML_053030/5330D247328/113306657-A0305.xml)，4,689 bytes，SHA-256 `f8c18dc5cb114fc70bd54b38a4cd8ea97b57772adac3568603e88c36c3e83d18`，DTD `2.0.1`。核對 7 段說明書，原檔沒有請求項。 |

兩案都保留獨立的 S01 版本及個案文字版本。`fulltext` 涵蓋本次驗證的個案說明書及來源提供的請求項。個案摘要欄位、圖式內容、新型與設計法律異動及自動補期尚待整合，圖式的實際下載可用性仍待驗證。

## 公告期別的固定封存檔

2026-11-10 以匿名 FTPS 列出官方目錄，確認 `專利說明書(1案1XML檔)` 的各期封存位於 `/PatentIsuRegSpecXMLA/<民國年>/PatentIsuRegSpecXMLA_<卷期>/`，115 年目錄當日有第 53 卷第 1 至 31 期。[第 53 卷第 28 期封存索引](ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053028/index.xml) 回傳 `226`，15,597,462 bytes 符合 `SIZE`，SHA-256 `60936a7ab763fbb8bd79b8a3071aa89d43da3ffe4ef65928734a9ddc70827a4a`。

這份封存檔與 2026-11-09 由 S01 最新期端點取得的副本（15,590,834 bytes，`f8268c23…`）不是同一個檔案。兩者解析出的公告 `I941082` 都是申請號 `114106690`、13 項請求項，請求項文字逐字相同，該筆紀錄的其他 XML 內容有差異。可重建的測試語料固定使用封存檔及其雜湊。同目錄另有 `index_all.xml` 和以申請號命名的個案 XML，本次未下載或解析。`PatentIsuRegSpecXMLB` 目錄的同期 `index.xml` 大小相同，未比對內容。

可重建語料另固定第 24 卷第 19 期 `index_all.xml` 及索引前 20 筆的個案說明書，各檔雜湊列於 [種子腳本](../scripts/seed_tipo_e2e.py)。這些雜湊來自 2026-11-09 驗收資料庫保存的原始物件紀錄。

2026-11-10 重新以匿名 FTPS 取得第 24 卷第 19 期索引與公開案 `202639611` 個案 XML，兩者 SHA-256 均符合上列固定值。獨立 E2E 卷只匯入這一案，核對資料庫的 19 項請求項和 122 段說明書與封存 XML 一致。政府目錄當日仍標示每月更新、免費與政府資料開放授權條款第 1 版。[政府資料開放平臺](https://data.gov.tw/dataset/15996)

## 在瀏覽器查閱官方文件

2026-11-27 核對[專利公開資訊查詢](https://tiponet.tipo.gov.tw/S092_OUT/2022/out)。該頁可接受申請案號、公開號或公告號，[官方網站導覽](https://tiponet.tipo.gov.tw/S092_OUT/2022/sitemap)說明結果由查詢產生且未提供固定網址列表。專利詳情顯示應輸入的同版本文件號，使用者可自行到官方頁面查詢。此入口只導向官方網站，個案與可閱文件依智慧財產局的公開範圍而異。

[TIPO 下載說明](https://cloud.tipo.gov.tw/S220/opdata/information/ftp)說明多數瀏覽器已停止支援 FTP。專利詳情可展開來源批次以取得完整 FTPS 位址、檔案 SHA-256 與原文位置。智慧財產局的發明網路公報及專利網路公報另有近半年卷期的 PDF 入口。[發明網路公報](https://cloud.tipo.gov.tw/S220/gazette/invention/sundry) · [專利網路公報](https://cloud.tipo.gov.tw/S220/gazette/patent)

### 發明公開公報個案 PDF

2026-11-27 實測發明網路公報個案請求。官方回應列出民國 115 年第 24 卷第 19 期、公開號 `202639611`、申請號 `113133932` 及 PDF 網址。直連回應為 `application/pdf`，5,824 bytes、1 頁，SHA-256 為 `cf6992639675e797291b4024b86b28c05550f1827d0af30993d0c67c010a7d1a`。用 pypdf 核對首頁欄標下的號碼。這是公報書目頁，可補充原件回溯，原本的請求項及說明書仍以個案 XML 為來源。[公報個案資料](https://cloud.tipo.gov.tw/S220/gazette/api/patents/laid-opens/cases/pubsud01/113133932) · [官方 PDF](https://cloud.tipo.gov.tw/S220/downloads/invention/pub024019/pdfdata/113133932.pdf)

採用單案、人工指定版本的匯入方式。公報站按近期卷期開放，個案網址的保存期限、下載配額與長期批次介接待確認。公開前端連結直接指向 TIPO。使用時應依智財局政府網站資料開放宣告查核出處標註、例外與個資條件。[智財局政府網站資料開放宣告](https://www.tipo.gov.tw/tw/tipo1/36-17871.html)

### 發明公告公報個案 PDF

2026-11-27 核對同一申請案 `114106690` 的公開和公告兩份官方個案。公開 `202640162` 為第 24 卷第 19 期、2 頁、22,539 bytes、SHA-256 `20df47fe2d746383732d7d4878537c153919338c5735a267cf797bcce09f4dee`。公告 `I941082` 為第 53 卷第 28 期、9 頁、1,349,889 bytes、SHA-256 `7b9fd5dcb190a7108770a812999e556b5126f2d0333dcf3a914ed20c91f1a615`。公告首頁另外帶有公開編號，匯入時以公報類型及證書號欄標判定。此驗收實測發明公告，掃描辨識、其他專利種類及後續全文檢索仍待。[公開 PDF](https://cloud.tipo.gov.tw/S220/downloads/invention/pub024019/pdfdata/114106690.pdf) · [公告個案資料](https://cloud.tipo.gov.tw/S220/gazette/api/patents/grants/cases/sud00_1/114106690) · [公告 PDF](https://cloud.tipo.gov.tw/S220/downloads/patent/isu053028/pdfdata/114106690.pdf)

## 公報書目的申請日、公開日與公告日

2026-11-26 核對政府目錄與匿名 FTPS 封存檔。兩項資料由智慧財產局提供，政府目錄列免費、每月更新、政府資料開放授權條款第 1 版。FTPS 每秒與每日配額未確認。

| 資料集 | 固定卷期與格式 | 下載驗證 | 可核對的範例 |
| --- | --- | --- | --- |
| [發明公開公報書目](https://data.gov.tw/dataset/9683) | [第 24 卷第 19 期 pubinvention.xml](ftps://ftp.tipo.gov.tw/PatentPubRegXMLB/115/PatentPubRegXMLB_024019/pubinvention.xml)，2,384 筆 | 17,322,532 bytes，`5eb3c531a3795e685f802289195da4f1779b8ca9eefef3e2f13ea8a85e634558` | `202639611`／`113133932`，公開 2026-10-01，申請 2024-09-06 |
| [專利公告公報書目](https://data.gov.tw/dataset/15972) | [第 53 卷第 28 期 patent.xml](ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLB/115/PatentIsuRegSpecXMLB_053028/patent.xml)，1,640 筆，含 1,095 筆發明公告 | 23,778,073 bytes，`836c3c9db01099dfe38fa1d15e9e1d3116180126c02f5179ebcf17542c7bd5c8` | `I941082`／`114106690`，公告 2026-10-01，申請 2025-02-24 |

`tipo-gazette-dates-1` 按同卷期、申請號及文件種類與編號對應已匯入版本。日期取 `application-reference/document-id/date` 與 `publication-reference/document-id/date`，把來源民國日曆轉成 PostgreSQL `date`。保留原始 XML、SHA-256 及書目 XPath。此來源用於日期補齊，缺少公報書目的既有版本仍可能無日期。

## 最新發明公開卷期

2026-11-26 透過 [TIPO S10 最新期索引](https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S10) 實際取得第 24 卷第 20 期，10,551,304 bytes、1,639 筆，SHA-256 `2f9a9744eb52eb8be24a79af4f106623e36432470f20afea45c3e0bff3cc70f0`。新版更新指令從所有書目核對 `volno` 及 `isuno`，拒絕卷期混合、筆數不符及空清單。實測匯入前 5 筆，在來源快照記錄原檔位置及雜湊。此次內容範圍為書目及摘要，公開全文另依個案來源處理。[政府目錄 15996](https://data.gov.tw/dataset/15996)

同日經匿名 FTPS 取得[民國 115 年第 024020 期全文封存清單](ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024020/index_all.xml)，11,388,480 bytes，SHA-256 `82982e0f31582bc8cfc17916aa0d3acb68d601e0fd8802389aaa9e4825e51283`。以 S10 送出順序前兩案核對公開號、申請號與個案路徑，匯入 `202642194`（申請號 `114108947`，9 項請求項、62 段）及 `202642585`（申請號 `114112229`，10 項請求項、54 段）。保留原有書目版，另存全文版。此結果只驗證選取的兩案。兩份原檔雜湊分別為 `bfa7ea9f7b45b69b7bb6cb2d7d80420f317db5c3e37f3f4e82cf4bdb41f564c1`、`4e9822c0fca6678c634e54998f4f08b353f37539911ff9b0ae0452ce3aec51fe`。

## 最新發明公告卷期

2026-11-26 從 [TIPO S01 最新公告索引](https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S01) 實際取得第 53 卷第 30 期，16,606,166 bytes，共 1,680 筆，其中 1,162 筆證書號有發明前綴 `I`。SHA-256 為 `fbfc4c7903e0b08fefaed6bad94240b8e7f4e680c9be80ead5ae31a6782b1d28`。驗收所選公告 `I942697`（申請號 `108112538`）有 38 項請求項，`I942698`（申請號 `108125866`）有 24 項，均核對索引原文及位置。驗收的公告內容範圍為書目及請求項。[政府目錄 15987](https://data.gov.tw/dataset/15987)

同日核對 [第 053030 期公告全文清單](ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053030/index_all.xml)，17,429,839 bytes，共 1,680 筆，SHA-256 `d6814fd1679b4cc41ada290bad698b33d85498bcab815d7b2bc90c0cb43e4fea`。檔內的 `specification-files/@xml-file` 路徑可配合 `PatentPubXML/115` 取得個案。抽查 `PatentIsuRegSpecXMLA` 目錄自身以申請號命名的 XML，包含書目、附圖及請求項。以官方清單取得的 `PatentPubXML` 個案則含摘要、說明書與請求項。本次用 `I942741` 和 `I942850` 驗證，原檔雜湊分別為 `715c5d69af4386d4f2509c1a8d84176ede723dbffc2f1ea6023ee3a1dcc7fa65` 與 `5cfd8244f675f12a984c2f5a227700104ef833299cb245dda088ea5d42e3efee`。兩種來源的部分請求項文字有異，系統分版本保存並在全文版引用同一個個案來源。

## 最新卷期的日期公報

2026-11-26 以匿名 FTPS 取得以下同期書目，沿用[日期公報資料集](#公報書目的申請日公開日與公告日)所載政府資料開放授權。完整解析時逐筆核對卷期、申請號、文件號與民國日期。來源年份以公報所載的公開或公告日期驗證。

| 來源 | 檔案資訊 | 首筆發明 |
| --- | --- | --- |
| [發明公開 024020](ftps://ftp.tipo.gov.tw/PatentPubRegXMLB/115/PatentPubRegXMLB_024020/pubinvention.xml) | 11,975,072 bytes，1,639 筆發明，SHA-256 `32fe19989646714d2dad592cf6344d237f6bab990792d1972bfdc854c1ee3682` | `202642194`，申請日 2025-03-11，公開日 2026-10-16。 |
| [發明公告 053030](ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLB/115/PatentIsuRegSpecXMLB_053030/patent.xml) | 25,347,635 bytes，1,162 筆發明，SHA-256 `d2ac1042f7cbcf7917065009626b6eccd868c55410a3f055472ea3e3146ae2c8` | `I942697`，申請日 2019-04-10，公告日 2026-10-21。 |

## 封存卷期目錄

2026-11-26 以匿名 FTPS 進入民國 115 年的 `/InventionPubXML/115`、`/PatentIsuRegSpecXMLA/115` 與 `/PatentIsuModXML/115`。在目錄內執行 `LIST` 均取得 `226`，分別列出 20 個公開期別（`024001`～`024020`）、33 個公告期別（`053001`～`053033`）以及 33 個異動期別（`053001`～`053033`）。同一檢查使用 `NLST` 回傳空清單。目錄可供確認封存範圍，卷期及檔案內容仍以下載後的 XML 驗證為準。S01 同日回傳 `053030`，低於公告封存目錄的最大期別 `053033`。目錄修改時間不作專利公告日期。

| 實際取得的索引 | 檔案與發明筆數 | 驗收樣本 |
| --- | --- | --- |
| [公開 024018](ftps://ftp.tipo.gov.tw/InventionPubXML/115/InventionPubXML_024018/index.xml) | 12,667,509 bytes，1,984 筆，SHA-256 `96c0ac33d8ece8da926dec02432d54ff1dca46678c90adb4d84cbf822df2be3c` | `202637274` 書目與摘要。 |
| [公告 053031](ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053031/index.xml) | 17,400,928 bytes，1,256 筆，SHA-256 `c0abbd28f7635ad326bf1f5391c2b3033e1dc0629df4757ea59fb99afa024176` | `I943859` 的 20 項請求項。 |
| [公告 053032](ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/115/PatentIsuRegSpecXMLA_053032/index.xml) | 17,656,938 bytes，1,242 筆，SHA-256 `242b4fa3b5408a5c8cd06434a7e01e2c64a4d28479975081e1f617622c75aa30` | `I945115` 的 20 項請求項。 |

## 專利權異動公報

2026-11-26 查核[專利權異動公報（15974）](https://data.gov.tw/dataset/15974)。提供者經濟部智慧財產局，目錄列每月更新、免費及政府資料開放授權條款第 1 版。[最新期索引 P10](https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/P10) 實得 1,662 筆、214,092 bytes，SHA-256 `3945c07fd8f2b286e00dac8d46c67faf849c998f3c89009b3eec75ebc2226299`。索引列申請號、證書號及異動種類，日期及更正欄位須讀該卷期的類別 XML。FTPS 速率限制未確認。

同日重抓 P10 的雜湊一致。根元素 `SundryData` 與 `Sundry` 記錄缺少卷期欄位，須核對封存索引才能定位卷期。

同日另以 `LIST` 找到[第 053033 期封存索引](ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053033/index.xml)。用匿名 FTPS 取得後與 P10 回應逐位元相同，大小與 SHA-256 均為上列值。定期更新用此方法核對卷期，再以申請號及證書號的出現次數核對類別 XML。實測 `sud08` 的 838 筆及 `sud24` 的 31 筆發明異動均與 P10 一致。

第 53 卷第 33 期的匿名 FTPS 封存實測如下。

| 類別 | 原檔大小與 SHA-256 | 可取得欄位 |
| --- | --- | --- |
| [消滅公告 sud08](ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053033/sud08.xml) | 469,608 bytes，`213b98e7337a0f99b74b9eff59ce0d92f0f27ccecf665892f8ee48b8423bd964` | 1,482 筆，含 838 筆發明。申請號、證書號、卷期、消滅日與原因。 |
| [公報更正 sud24](ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053033/sud24.xml) | 41,156 bytes，`97993734e1cd87b54537069ded8593a02615d7aa09442779a47a688ccffc16a3` | 35 筆，含 31 筆發明。申請號、證書號、卷期與更正欄位。公開 API 只使用欄位名稱。 |

`tipo-sundry-events-1` 保留原檔、雜湊及 XML 位置，解析時移除完全符合官方樣本的外部 DTD 宣告，其他 DTD 一律拒絕。僅將可核對申請號的發明事件關聯至已匯入的臺灣案件。事件表示公報記載的歷史事項，來源涵蓋範圍以已匯入期別為限。

2026-11-26 交叉核對 [第 52 卷第 6 期公告索引](ftps://ftp.tipo.gov.tw/PatentIsuRegSpecXMLA/114/PatentIsuRegSpecXMLA_052006/index.xml) 與第 53 卷第 33 期消滅公告。公告索引有 1,780 筆，16,989,536 bytes，SHA-256 `99cde994594aa622cf9469ecb6541403b3567b4597342a6915c35ce5dab526f8`。證書 `I874215` 和申請號 `113117471` 在兩個原檔一致。公告索引提供 9 項請求項，消滅公報的第 1447 筆記載消滅日 2026-02-21，原因為「未依限繳費」。公告索引屬官方卷期彙整 XML，匯入器允許 32 MiB 上限。個案說明書維持 16 MiB 上限。

[專利權狀態異動資料（發明，30126）](https://data.gov.tw/dataset/30126) 是另一資料來源，官方 [OpenAPI 文件](https://cloud.tipo.gov.tw/S220/opdata/api/file/oas) 列 `/PatentRights` 及 `tk` 欄位。任意案件的最新狀態查詢與授權憑證仍待驗證。此階段使用匿名可取得、可保留原文的固定卷期事件。

### 第 053032 期異動封存

2026-11-26 實測民國 115 年第 053032 期的匿名 FTPS 封存。[索引](ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053032/index.xml) 大小為 250,333 bytes，SHA-256 `864b6d1837000ba92354018bc6ea647e9e5050cbe86cdbfda0cb10475ba4575b`。[消滅公告 `sud08`](ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053032/sud08.xml) 有 982 筆發明事件，SHA-256 `6b9ccbdcf7d4966247c5de51b5bc2c60371c3badb58f7b6ec93e64801a7cff1a`。[更正公報 `sud24`](ftps://ftp.tipo.gov.tw/PatentIsuModXML/115/PatentIsuModXML_053032/sud24.xml) 有 33 筆發明事件，SHA-256 `624e09e1e2b820778f52722ba3589c9f653ae2423c6e181b0a4c033fb4eafa16`。兩類原檔的發明事件身分及次數均與封存索引一致。
