
### 1. 個人資料頁（My Profile）
**功能分析：**
- 編輯個人基本資料（姓名、Email、電話、國家、城市、時區）
- 語言設定（教練語言與通知語言）
- 溝通工具設定（Skype, WhatsApp, WeChat, Zoom, Google Meet, MS Teams）
- 密碼變更區塊
- Stripe 連結（收款設定）
- 教練經驗與認證選項、網站與 LinkedIn 連結
- 教練方案設定（單次與套裝）

**Replit Prompt：**
```text
read memory bank ，開始實作 my profile = 個人設定，把位置移到儀表板下面，逐字稿轉換上面，另外右手邊 menu 用戶的個人資料可以移除，只需要保留帳戶設定

Create a responsive user profile management dashboard in React. The UI should include:
- Profile photo with edit button
- Fields for name, email, phone (with country code selector), country, city, timezone
- Language selection for coaching and notifications
- Input fields for communication tools: Skype, WhatsApp, WeChat, toggle buttons for Zoom, Google Meet, MS Teams
- Section for password change with confirmation field
- Stripe connect button for payout setup
- Coaching experience dropdown, training institution, certification, LinkedIn, and website
- Coaching session inputs: title, duration, price
- Package session inputs: number of sessions, duration, price
```

---

### 2. 預約頁（My Bookings）
**功能分析：**
- 分頁顯示「我的預約」與「我的客戶」
- 可搜尋名稱或 Email
- 預約紀錄表格（Booking ID、Name、Date & Time、Type、Duration、Link、Location、Comments、Status）
- 月曆檢視切換（Prev/Today/Next）

**Replit Prompt：**
```text
Design a bookings page with two tabs: "My Bookings" and "My Clients". Include:
- Search bar with name/email input
- Bookings table with headers: Booking ID, Name, Date & Time, Type of Session, Duration, Meeting Link, Location, Comments, Type, Status, Action
- Pagination and calendar view for session navigation
```

---

### 3. 儀表板頁（My Dashboard）
**功能分析：**
- 顯示教練場次統計：總場次（本月與上月）、P2P 教練狀態、評分、平均場次／客戶
- 場次圖表（Active、Completed、Cancelled）
- 地理分佈圖（Top Client Location）
- 區塊：My Feedback、My Pricing、Conversion Rate（尚無資料）

**Replit Prompt：**
```text
Build a dashboard overview for coaches, including:
- Stat boxes: Total Sessions (with month-on-month delta), P2P Coaching (as coach/client), My Rating, Avg Sessions/Client
- Line or bar chart showing session trends over time (Active, Completed, Cancelled)
- World map heatmap showing top client locations
- Reserved sections: My Feedback, My Pricing, Conversion Rate
```

---

### 4. 財務頁（My Financials）
**功能分析：**
- 搜尋與篩選條件（名稱、Email、起始與結束日期）
- 表格顯示收款紀錄（Booking ID、Client、Email、Amount、Duration、Date、Received、Status、View）

**Replit Prompt：**
```text
Create a financial overview page with:
- Filters: name/email input, date range selectors
- Payment records table with headers: Booking ID, Client, Email, Amount, Duration, Session Date, Received Amount, Status, View
```

---

### 5. 教練方案設定（Coaching Sessions & Packages）
**功能分析：**
- 可設定免費初談方案
- 可設定付費教練單次方案
- 可設定多次套裝方案（Session 數量、每次分鐘數、總價）

**Replit Prompt：**
```text
Design a coaching service setup form:
- Section for free intro session (title, duration)
- Section to add multiple paid coaching sessions (title, duration, price)
- Section to define coaching packages (number of sessions, duration per session, total price)
- Each input section should allow dynamic addition
```

---

### 6. 行事曆與時段設定頁（Availability）
**功能分析：**
- 每日可預約時段（預設為 10:00 - 20:00）
- 全月月曆檢視與時間區段標記

**Replit Prompt：**
```text
Build an availability calendar for coaches:
- Monthly calendar view
- Each day shows editable available time range (default 10:00–20:00)
- Allow user to modify availability per day
- Support previous/next month navigation
```

---

### 7. Coach 搜尋頁面
**功能分析：**
- 顯示教練卡片（姓名、年資、城市／時區、認證等）
- 服務標籤（Executive, Career, Life Coaching）
- 個人介紹文字、標示「Known For」
- 每小時費用，顯示「Book Now」按鈕
- 可搭配簡介影片

**Replit Prompt：**
```text
Create a coach listing/search result page with cards for each coach. Each card should include:
- Coach name, years of experience, certification level, location, timezone
- Tags for coaching specializations (e.g. Executive, Career, Life Coaching)
- Profile photo, hourly rate, introduction text, "Known For" tags
- "Book Now" button
- Optional profile video preview
```