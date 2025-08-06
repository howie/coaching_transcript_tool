
## 教練會談紀錄頁面

變更範圍：新增頁面，資料庫欄位和後端 api

Dashboard menu 新增一個教練記錄

頁面使用 table view 記錄教練會談的紀錄，包含日期，客戶，客戶來源，會談時長，收費，後面有編輯和刪除的按鈕

這頁有一個新增記錄的按鈕，按下去產生新增記錄頁面 包含日期（日曆)，客戶(下拉選單 or 新增)，客戶來源(下拉選單：客戶，朋友，同學，部屬)，會談時長(min)，收費 (ntd)。

新增記錄的按鈕還兩個功能，上傳逐字稿(逐字稿轉換頁面主功能)，上傳錄音檔 (錄音檔轉檔主功能頁面)

Dashboard 上的教練總時數，和本月時數，轉換的逐字稿都是從資料庫撈出來
# Design Document｜教練會談紀錄 + 客戶管理（v3）

**狀態**：Confirmed spec  
**更新日期**：2025-08-05  
**本版重點**：
- 金額一律 **整數、無小數點**（顯示與儲存皆為整數單位）。  
- **GDPR／去個資**：客戶可申請刪除個資；改採 **匿名化（去識別化）**，例如「王小明」→「已刪除客戶 1」。  
- 多人使用（每個登入者＝教練），每位教練擁有多個客戶。  
- 新增 **客戶管理頁**；會談收費支援 **多幣別**（NTD／USD…）。  
- 會談紀錄 **硬刪除**；客戶刪除受限（若與會談關聯，需改走「匿名化」流程）。  
- Dashboard 新增 **本月收入（依幣別彙總）**、**累積會談客戶總數**。

---

## 1. 範圍（Scope）
- 新增前端頁面：
  - **教練紀錄** `/sessions`（清單／新增／編輯）
  - **客戶管理** `/clients`（清單／新增／編輯）
- 後端 API：Clients、Sessions、Summary、GDPR **匿名化**。
- 資料庫：`clients`、`coaching_sessions`（含多幣別欄位）。
- Dashboard 聚合：總時數／本月時數／逐字稿數量／**本月收入（依幣別）**／**累積會談客戶數**。

---

## 2. 使用者故事（User Stories）與驗收（AC）

### US-S1｜會談清單（Table View）
- 欄位：日期、客戶、客戶來源、時長（分鐘）、**幣別**、**收費（整數）**、操作（編輯／刪除）。
- 預設排序：日期 **新到舊**。
- 支援排序：日期、**收費**（以同幣別比較；跨幣別排序時先依幣別、再依收費）。
- 篩選：日期區間、客戶、來源。
- 分頁：預設 20 筆（10/20/50）。
- 顯示格式：
  - 日期 `YYYY-MM-DD`
  - 時長：`{n} 分鐘`
  - 收費：`{CURRENCY} {AMOUNT}`（例：`NTD 2500`；**無小數點**）

### US-S2｜新增會談
- 表單欄位：
  - 日期（日曆）【必填】
  - 客戶（下拉；可「新增客戶」）【必填】
  - 來源（客戶／朋友／同學／部屬）
  - 會談時長（分鐘，>0）【必填】
  - **幣別**（ISO 4217，預設 `NTD`）【必填】
  - **收費**（整數、>=0，**無小數點**）【必填】
  - 備註（僅詳情可見）
- 提交鈕：
  - 儲存
  - 儲存並上傳逐字稿 → `/transcript-converter?session_id={id}`
  - 儲存並上傳錄音檔 → `/audio-upload?session_id={id}`
- 成功後返回清單並提示。

### US-S3｜編輯會談
- 與新增同版型；提交後返回清單。

### US-S4｜刪除會談（硬刪除）
- 二次確認後，直接自資料庫刪除該筆會談。

### US-C1｜客戶管理清單
- 欄位：姓名、Email、Phone、備註、狀態（是否已匿名化）、操作。
- 搜尋：姓名／Email；分頁與排序（姓名）。

### US-C2｜新增／編輯／刪除客戶
- 欄位：`name`【必填】、`email`、`phone`、`memo`。
- **刪除**：
  - 若該客戶 **無** 任何關聯會談 → 允許硬刪除。
  - 若該客戶 **已有** 會談 → 禁止硬刪除，提示改走 **匿名化**（GDPR）。

### US-GDPR｜客戶匿名化（去個資）
- 需求：當客戶依 GDPR 要求刪除個資時，系統對客戶資料 **去識別化**，但保留關聯會談供營運／統計。
- 行為：
  - 將客戶名稱改為「**已刪除客戶 N**」（N 為本教練底下匿名化遞增序號）。
  - 清空（設為 `NULL`）Email、Phone、Memo。
  - 標記 `is_anonymized = true`、記錄 `anonymized_at` 時間。
  - 保留 `id` 與關聯會談（sessions）。
- UI 顯示：
  - 客戶欄位顯示灰字斜體「已刪除客戶 N」。
  - 不允許再編輯匿名化客戶（除非管理員復原機制，預設不提供）。

### US-D1｜Dashboard 聚合
- 顯示：
  - 教練總時數（分鐘）
  - 本月時數（分鐘）
  - 轉換的逐字稿數量
  - **本月收入（依幣別彙總；整數、無小數點）**
  - **累積會談客戶總數**（有至少一筆會談的 distinct 客戶數，含匿名化客戶）
- 全由 DB 聚合（非前端計算）。

---

## 3. 資料模型（PostgreSQL）

> 多人使用：每位登入者＝教練（`users`）。

### 3.1 `users`（略，假設既有）
- `id` (uuid, PK), `email` (unique), `name`, `created_at`, `updated_at`。

### 3.2 `clients`
| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | 客戶 ID |
| coach_id | uuid FK → users(id) | 所屬教練 |
| name | text not null | 客戶姓名（若匿名化 → 「已刪除客戶 N」）|
| email | text null | 客戶 email（匿名化時設 NULL）|
| phone | text null | 客戶電話（匿名化時設 NULL）|
| memo | text null | 備註（匿名化時設 NULL）|
| is_anonymized | boolean not null default false | 是否已匿名化 |
| anonymized_at | timestamptz null | 匿名化時間 |
| created_at / updated_at | timestamptz | 伺服器時間 |

**唯一性建議**：`unique (coach_id, lower(email)) where email is not null`，避免重複客戶。允許同名不同人。

### 3.3 `coaching_sessions`
| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid PK | 會談 ID |
| coach_id | uuid FK → users(id) | 所屬教練 |
| session_date | date not null | 會談日期 |
| client_id | uuid FK → clients(id) | 客戶 |
| source | text check | `client`/`friend`/`classmate`/`subordinate` |
| duration_min | integer not null check (>0) | 時長（分鐘）|
| **fee_currency** | char(3) not null | 幣別（ISO 4217，如 `NTD`、`USD`）|
| **fee_amount** | integer not null check (>=0) | **金額整數，無小數點**（單位＝幣別之「元」）|
| transcript_timeseq_id | uuid null | 逐字稿 timeseq 關聯 |
| audio_timeseq_id | uuid null | 錄音檔 timeseq 關聯 |
| notes | text null | 備註（僅詳情顯示）|
| created_at / updated_at | timestamptz | 伺服器時間 |

> **金額規則**：本版明確採用 **整數元** 儲存與顯示，不處理小數（無四捨五入）。

### 3.4 索引
- `clients (coach_id, name)`
- `clients unique (coach_id, lower(email)) where email is not null`
- `coaching_sessions (coach_id, session_date desc)`
- `coaching_sessions (coach_id, client_id)`
- `coaching_sessions (coach_id, fee_currency, session_date)`

---

## 4. DB Migration（SQL 範例）

```sql
-- clients
CREATE TABLE IF NOT EXISTS clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  coach_id UUID NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  memo TEXT,
  is_anonymized BOOLEAN NOT NULL DEFAULT FALSE,
  anonymized_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_clients_coach_name ON clients (coach_id, name);
CREATE UNIQUE INDEX IF NOT EXISTS uq_clients_coach_email
  ON clients (coach_id, lower(email))
  WHERE email IS NOT NULL;

-- coaching_sessions
CREATE TABLE IF NOT EXISTS coaching_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  coach_id UUID NOT NULL REFERENCES users(id),
  session_date DATE NOT NULL,
  client_id UUID NOT NULL REFERENCES clients(id),
  source TEXT NOT NULL CHECK (source IN ('client','friend','classmate','subordinate')),
  duration_min INTEGER NOT NULL CHECK (duration_min > 0),
  fee_currency CHAR(3) NOT NULL,
  fee_amount INTEGER NOT NULL CHECK (fee_amount >= 0),
  transcript_timeseq_id UUID,
  audio_timeseq_id UUID,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sessions_coach_date ON coaching_sessions (coach_id, session_date DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_coach_client ON coaching_sessions (coach_id, client_id);
CREATE INDEX IF NOT EXISTS idx_sessions_coach_currency_date ON coaching_sessions (coach_id, fee_currency, session_date);
```

---

## 5. 後端 API（FastAPI）

> 前綴 `/api/v1`；所有端點需登入驗證，服務端以登入身分注入 `coach_id`。

### 5.1 客戶（Clients）
- **GET** `/clients?query=&page=1&page_size=20`
- **GET** `/clients/{id}`
- **POST** `/clients`
  ```json
  { "name": "王小明", "email": "a@b.com", "phone": "0900...", "memo": "VIP" }
  ```
- **PATCH** `/clients/{id}`
- **DELETE** `/clients/{id}`
  - 僅在 **無會談關聯** 時允許；否則回 `409` 並指引使用匿名化。
- **POST** `/clients/{id}/anonymize`  ← **GDPR 去個資**
  - 行為：改名為「已刪除客戶 N」、清空 email/phone/memo、設 `is_anonymized=true`、寫入 `anonymized_at`。
  - `N` 產生方式（單交易）：
    ```sql
    WITH num AS (
      SELECT COALESCE(COUNT(*),0) + 1 AS n
      FROM clients WHERE coach_id = $1 AND is_anonymized = TRUE
    )
    UPDATE clients
    SET name = '已刪除客戶 ' || (SELECT n FROM num),
        email = NULL,
        phone = NULL,
        memo = NULL,
        is_anonymized = TRUE,
        anonymized_at = now(),
        updated_at = now()
    WHERE id = $2 AND coach_id = $1 AND is_anonymized = FALSE;
    ```

### 5.2 會談（Sessions）
- **GET** `/sessions?from=2025-08-01&to=2025-08-31&client_id=&source=&currency=&sort=-session_date&page=1&page_size=20`
  - `sort` 支援：`session_date`, `-session_date`, `fee`, `-fee`。
  - 若跨幣別排序，以 `fee_currency`、`fee_amount` 組合排序。
- **GET** `/sessions/{id}`
- **POST** `/sessions`
  ```json
  {
    "session_date": "2025-08-05",
    "client_id": "uuid",
    "source": "client",
    "duration_min": 90,
    "fee_currency": "NTD",
    "fee_amount": 2500,
    "notes": ""
  }
  ```
- **PATCH** `/sessions/{id}`
- **DELETE** `/sessions/{id}`  → 硬刪除

### 5.3 辦別／設定
- **GET** `/session-sources`
  ```json
  [
    {"value":"client","label":"客戶"},
    {"value":"friend","label":"朋友"},
    {"value":"classmate","label":"同學"},
    {"value":"subordinate","label":"部屬"}
  ]
  ```
- **GET** `/currencies`  （可擴充，預設回傳 `NTD`, `USD`）
  ```json
  ["NTD", "USD"]
  ```

### 5.4 Dashboard 聚合
- **GET** `/sessions/summary?month=2025-08`
  ```json
  {
    "total_minutes": 12345,
    "current_month_minutes": 900,
    "transcripts_converted_count": 12,
    "current_month_revenue_by_currency": { "NTD": 15000, "USD": 300 },
    "unique_clients_total": 42
  }
  ```
- 月份範圍依 Asia/Taipei 計算。

---

## 6. 前端規格（Next.js）

### 6.1 導覽與路由
- Sidebar：
  - **教練紀錄** → `/sessions`（清單）／`/sessions/new`／`/sessions/[id]/edit`
  - **客戶管理** → `/clients`（清單）／`/clients/new`／`/clients/[id]/edit`

### 6.2 會談清單 `/sessions`
- 欄位：日期｜客戶（匿名化時灰字斜體）｜來源｜時長（分鐘）｜幣別｜收費（整數）｜操作。
- 篩選：日期區間、客戶、來源、幣別（可選）。
- 排序：日期（desc 預設）、收費（同幣別內排序）。
- 刪除：二次確認。
- 新增：右上角主要按鈕。

### 6.3 會談表單 `/sessions/new`、`/sessions/[id]/edit`
- 欄位：日期、客戶（含「新增客戶」彈窗）、來源、時長、**幣別 Select（預設 NTD）**、**收費（整數 Input，無小數）**、備註。
- 提交鈕：儲存／儲存並上傳逐字稿／儲存並上傳錄音檔。

### 6.4 客戶管理 `/clients`
- 清單：姓名｜Email｜Phone｜備註｜狀態（是否已匿名化）｜操作。
- 匿名化：行動列提供「匿名化」按鈕（需二次確認）。成功後改為「已刪除客戶 N」。
- 刪除：僅在無關聯會談時顯示；否則提示走匿名化。

---

## 7. 權限與安全
- 所有查詢均以 `coach_id = current_user.id` 限制，嚴格隔離多租戶資料。
- 會談／客戶皆預設 **硬刪除**（但客戶在有會談時不可刪，需匿名化）。
- 匿名化不可逆；匿名化客戶不可再編輯。

---

## 8. 錯誤處理
- 400 欄位驗證失敗（含幣別不在清單、收費非整數等）
- 401 未登入；403 非擁有者；404 資源不存在
- 409 刪除衝突（客戶有會談關聯而嘗試刪除）

---

## 9. 測試計畫
- 後端：
  - 會談金額為整數、無小數；排序與過濾正確。
  - 匿名化交易原子性（名稱遞增、清空敏感欄位）。
  - Summary 聚合（跨月、跨幣、匿名化後仍納入客戶計數）。
- 前端：
  - 表單（整數金額驗證）、匿名化按鈕流程、刪除條件限制。
  - 清單顯示匿名化樣式、收費排序。

---

## 10. 與既有轉檔功能（timeseq）
- 新增／編輯會談後可直達轉檔頁並帶 `session_id`。
- 轉檔完成後（若有回呼）可回寫 `transcript_timeseq_id`／`audio_timeseq_id`。
- 不存逐字稿／音訊內容，僅保留 timeseq 連結。

---

## 11. 實作備忘（整數金額）
- 後端 Schema：`fee_amount: conint(ge=0)`；`fee_currency: constr(min_length=3, max_length=3)`。
- 前端 Input：限制為整數；顯示／輸出皆不含小數點。
- 跨幣別金額不比較大小（除非指定匯率），列表排序以（`fee_currency`, `fee_amount`）。
