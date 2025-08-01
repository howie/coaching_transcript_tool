# 進度追蹤

## 2025-08-01

### 已完成
- **修復 Dark Mode 顏色問題**
  - `dashboard-header.tsx`: 將 `bg-dashboard-header-bg` 替換為 `bg-dashboard-header`
  - `dashboard-sidebar.tsx`: 將 `bg-dashboard-header-bg` 替換為 `bg-dashboard-sidebar`
  - `globals.css`: 新增 `dark-mode` 下 `bg-dashboard-header` 和 `bg-dashboard-sidebar` 的樣式
  - `tailwind.config.ts`: 將 `dashboard-header-bg` 替換為 `dashboard-header` 和 `dashboard-sidebar`

- **修復圖片載入問題**
  - `dashboard-header.tsx`: 將圖片路徑從 `Coachly-logo-transparent-300px.png` 更新為 `Coachly-logo-white.png`

- **重大架構決策 (2025-08-01 22:00)**
  - **確認 Cloudflare Workers 全棧部署策略**
    - 前端：Next.js 靜態建置 → CF Workers 託管
    - 後端：FastAPI 直接在 CF Workers Python Runtime 運行
    - 優勢：零基礎設施成本、全球邊緣部署、無運維負擔
  - **更新 Memory Bank 文件**
    - `activeContext.md`: 新增 CF Workers 部署為極高優先級任務
    - `systemPatterns.md`: 架構從三層改為單一 Serverless 服務
    - 架構版本更新：v2.1 → v2.2 (Serverless 優先)

### 待辦
- 完成 Docker 整合驗證 (本地開發環境)
- 建立 CF Workers 項目結構
- 實作 CF Workers 部署配置
