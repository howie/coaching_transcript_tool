# 架構決策記錄 (Architecture Decision Records)

本文件記錄 Coaching Transcript Tool 專案的重要架構決策，以供未來參考和理解決策背景。

## ADR-001: 前後端分離架構

**日期：** 2025-07-31  
**狀態：** 已採用  
**決策者：** 開發團隊  

### 背景
原本專案採用 Flask + FastAPI 混合架構，前端模板與 API 耦合度高，難以維護和擴展。

### 決策
採用完全分離的前後端架構：
- 前端：Next.js 14 + TypeScript
- 後端：FastAPI (純化，移除 Flask)
- API Gateway：Cloudflare Workers

### 原因
1. **可維護性提升**：清晰的職責分離
2. **可擴展性**：前後端可獨立擴展
3. **開發效率**：現代化工具鏈支援
4. **部署靈活性**：可選擇最適合的部署平台

### 後果
- **正面**：開發效率提升、更好的 SEO、現代化 UX
- **負面**：初期複雜度增加、需要額外的認證機制

---

## ADR-002: Monorepo 架構選擇

**日期：** 2025-07-31  
**狀態：** 已採用  
**決策者：** 開發團隊  

### 背景
專案包含前端、後端、共用型別等多個組件，需要統一管理。

### 決策
採用 Turborepo 實現 Monorepo 架構：
```
apps/
├── frontend/     # Next.js 應用
├── backend/      # FastAPI 應用
└── gateway/      # CF Workers (未來)
packages/
├── shared-types/ # 共用型別定義
└── eslint-config/# 共用配置
```

### 原因
1. **代碼重用**：共用型別和配置
2. **統一工具**：統一的建置、測試、部署流程
3. **版本一致性**：所有套件版本同步
4. **開發效率**：單一 repository 簡化協作

### 後果
- **正面**：提升開發效率、減少重複代碼
- **負面**：初期設定複雜度較高

---

## ADR-003: 技術棧選擇

**日期：** 2025-07-31  
**狀態：** 已採用  
**決策者：** 開發團隊  

### 背景
需要選擇適合的技術棧來實現現代化的 SaaS 服務。

### 決策

**前端技術棧：**
- **框架**：Next.js 14 (App Router)
- **語言**：TypeScript
- **樣式**：Tailwind CSS
- **認證**：NextAuth.js v4
- **狀態管理**：Zustand

**後端技術棧：**
- **框架**：FastAPI
- **語言**：Python 3.11+
- **資料處理**：pandas, openpyxl (保持現有)
- **認證**：Google Identity Platform

**API Gateway：**
- **平台**：Cloudflare Workers
- **框架**：Hono.js
- **語言**：TypeScript

### 原因

**Next.js 14：**
- 優秀的 SSR/SSG 支援
- App Router 提供現代化路由
- 豐富的生態系統
- 優秀的開發體驗

**FastAPI：**
- 保持現有業務邏輯
- 優秀的 API 文檔生成
- 高效能和異步支援
- Python 生態系統優勢

**Cloudflare Workers：**
- 全球邊緣運算
- 優秀的效能
- 成本效益高
- 與前端部署平台整合

### 後果
- **正面**：現代化開發體驗、優秀效能、可擴展性
- **負面**：學習曲線、初期開發成本

---

## ADR-004: 部署策略選擇

**日期：** 2025-07-31  
**狀態：** 已採用  
**決策者：** 開發團隊  

### 背景
需要選擇合適的部署策略以實現全球化服務和成本優化。

### 決策
採用混合部署策略：

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js       │    │  CF Workers      │    │   FastAPI       │
│ (CF Pages)      │ -> │  (API Gateway)   │ -> │ (GCP Cloud Run) │
│ - SSR/SSG       │    │ - 認證中間件      │    │ - 核心業務邏輯   │
│ - 響應式 UI     │    │ - Rate Limiting  │    │ - 檔案處理      │
│ - NextAuth      │    │ - 快取層        │    │ - 資料庫存取    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 原因

**Cloudflare Pages (前端)：**
- 全球 CDN 分發
- 優秀的靜態資源快取
- 與 Workers 整合良好
- 成本效益高

**Cloudflare Workers (Gateway)：**
- 邊緣運算降低延遲
- 內建快取和 Rate Limiting
- 靈活的中間件系統
- 與前端平台整合

**GCP Cloud Run (後端)：**
- 保持現有 Python 生態系統
- 按需擴展降低成本
- 豐富的 GCP 整合
- 容器化部署靈活性

### 後果
- **正面**：全球化部署、成本優化、高可用性
- **負面**：多平台管理複雜度增加

---

## ADR-005: 配色系統設計

**日期：** 2025-01-31  
**狀態：** 已採用  
**決策者：** UI/UX 團隊  

### 背景
需要建立一致且專業的視覺設計系統，支援不同使用場景。

### 決策
採用情境式雙主題設計系統：

**Landing Page 主題：**
- 主色調：天藍色 (#71c9f1)
- 導航背景：深藍色 (#2c3e50)
- 強調色：橙色 (#ff6b35) 用於 CTA 按鈕

**Dashboard 主題：**
- 主背景：深藍色 (#1C2E4A)
- Header/Sidebar：淺藍色 (#71c9f1)
- 強調色：黃色 (#F5C451)
- 統計數字：淺藍色 (#71c9f1)

### 原因
1. **情境適配**：不同場景使用不同色調
2. **品牌一致性**：保持核心色彩元素
3. **使用者體驗**：Landing Page 友好、Dashboard 專業
4. **可訪問性**：確保對比度符合標準

### 後果
- **正面**：專業視覺形象、優秀使用者體驗
- **負面**：需要維護兩套色彩系統

---

## ADR-006: Monorepo 架構重構實施

**日期：** 2025-08-02  
**狀態：** 已完成  
**決策者：** 開發團隊  

### 背景
專案初期採用扁平化結構（`backend/`, `frontend/`, `gateway/`），隨著專案成長，需要更清晰的 monorepo 架構來管理多個應用和共享套件。

### 決策
將專案重構為標準 monorepo 架構：

**重構前：**
```
coaching_transcript_tool/
├── backend/           # FastAPI + CLI 混合
├── frontend/          # Next.js 應用
├── gateway/           # Cloudflare Workers
└── packages/          # 共享套件
```

**重構後：**
```
coaching_transcript_tool/
├── apps/              # 應用程式層
│   ├── api-server/    # FastAPI 服務 (從 backend/ 分離)
│   ├── cli/           # CLI 工具 (從 backend/ 分離)
│   ├── web/           # Next.js 應用 (重命名自 frontend/)
│   └── cloudflare/    # Cloudflare Workers (重命名自 gateway/)
├── packages/          # 共享套件層
│   ├── core-logic/    # 核心業務邏輯 (從 backend/src 提取)
│   ├── shared-types/  # 共享型別定義
│   └── eslint-config/ # 共享 ESLint 配置
└── ...
```

### 實施細節

**1. 應用程式分離：**
- `backend/` 拆分為 `apps/api-server/` 和 `apps/cli/`
- 將共同的業務邏輯提取到 `packages/core-logic/`
- 測試檔案從 `apps/api-server/tests/` 移至 `packages/core-logic/tests/`

**2. 路徑和配置更新：**
- 更新 `Makefile` 中所有路徑引用
- 修改 `docker-compose.yml` 和 Dockerfile 路徑
- 調整 `requirements.txt` 中的相對路徑引用

**3. 套件依賴管理：**
- API 服務和 CLI 工具都依賴 `packages/core-logic/`
- 使用相對路徑 `-e ../packages/core-logic` 建立本地依賴

### 原因
1. **清晰的關注點分離**：API 服務和 CLI 工具各自獨立
2. **程式碼重用**：核心邏輯統一管理在 `packages/core-logic/`
3. **獨立部署**：每個應用可獨立打包和部署
4. **標準化架構**：符合現代 monorepo 最佳實踐
5. **擴展性**：未來可輕鬆添加新的應用或套件

### 後果
- **正面**：
  - 架構更清晰，職責分離明確
  - 程式碼重用性提升
  - 測試和部署流程更標準化
  - 新開發者更容易理解專案結構
- **負面**：
  - 初期路徑調整需要全面測試
  - Docker 構建需要重新驗證

### 驗證結果
- ✅ API Docker 映像構建成功
- ✅ CLI Docker 映像構建成功  
- ✅ 所有 Makefile 指令正常運作
- ✅ 測試套件在新位置正常執行

---

## 決策追蹤

| ADR | 決策 | 狀態 | 實施日期 | 備註 |
|-----|------|------|----------|------|
| ADR-001 | 前後端分離架構 | ✅ 已完成 | 2025-07-31 | 基礎架構已建立 |
| ADR-002 | Monorepo 架構 | ✅ 已完成 | 2025-07-31 | Turborepo 已配置 |
| ADR-003 | 技術棧選擇 | 🚧 進行中 | 2025-07-31 | 前端已完成，Gateway 待開發 |
| ADR-004 | 部署策略 | ⏳ 待開始 | 2025-07-31 | 前端已部署，後端待配置 |
| ADR-005 | 配色系統 | ✅ 已完成 | 2025-01-31 | 設計系統已實施 |
| ADR-006 | Monorepo 架構重構實施 | ✅ 已完成 | 2025-08-02 | 標準化 monorepo 架構 |

---

**最後更新：** 2025-08-02  
**版本：** 1.1
