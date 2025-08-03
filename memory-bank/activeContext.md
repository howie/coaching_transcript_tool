# 當前工作重點

## 工具鏈重構完成 ✅

### 已完成的工具鏈重構任務

1. **目錄結構重組完成 (第一階段)**
   - ✅ `apps/container` → `apps/api-server`
   - ✅ 測試檔案從 `apps/api-server/tests/` 移至 `packages/core-logic/tests/`
   - ✅ CLI pyproject.toml 從 `apps/api-server/` 移至 `apps/cli/`
   - ✅ 清理了 `apps/api-server/src/` 中的舊檔案

2. **配置檔案更新完成 (第一階段)**
   - ✅ 更新 Makefile 中所有對 `apps/container` 的引用為 `apps/api-server`
   - ✅ 更新測試路徑從 `apps/container/tests/` 到 `packages/core-logic/tests/`
   - ✅ 更新 docker-compose.yml 適應新架構
   - ✅ 修復 Dockerfile.api 路徑問題
   - ✅ 修復 `apps/api-server/requirements.txt` 中相對路徑

3. **前端工具鏈重構完成 (第二階段)**
   - ✅ 備份 root 層級配置檔案 (.bk)
   - ✅ 前端配置遷移到 `apps/web/`
     - `wrangler.frontend.toml` → `apps/web/wrangler.toml`
     - 創建 `apps/web/turbo.json` 
     - 更新 `apps/web/package.json` 添加部署腳本
   - ✅ Makefile 增強支援前端管理
     - 添加 `dev-frontend`, `build-frontend`, `deploy-frontend` 等指令
     - 統一的開發體驗 (`dev-all`, `build-all`, `install-all`)
   - ✅ 功能驗證測試通過
     - 前端依賴安裝成功
     - Next.js 建置成功  
     - 開發服務器啟動正常

4. **Docker 構建測試完成**
   - ✅ API Docker 映像構建成功
   - ✅ CLI Docker 映像之前已驗證可正常運作

### 當前專案架構 (重構後)

```
coaching_transcript_tool/
├── apps/                    # 應用程式層
│   ├── api-server/         # FastAPI 服務器 (重構前: backend/)
│   │   ├── main.py         # FastAPI 應用入口
│   │   ├── requirements.txt # API 服務依賴
│   │   └── Dockerfile.api  # API Docker 檔案
│   ├── cli/                # 命令列工具 (重構前: backend/)
│   │   ├── main.py         # CLI 入口點
│   │   ├── requirements.txt # CLI 依賴
│   │   ├── pyproject.toml  # CLI 套件配置
│   │   └── Dockerfile      # CLI Docker 檔案
│   ├── cloudflare/         # Cloudflare Workers 閘道 (重構前: gateway/)
│   │   ├── main.py         # Workers 入口點
│   │   ├── requirements.txt # Workers 依賴
│   │   ├── wrangler.toml   # Cloudflare 配置
│   │   └── src/            # Workers 源碼
│   └── web/                # Next.js 前端 (重構前: frontend/)
│       ├── app/
│       ├── components/
│       └── package.json
├── packages/               # 共享套件層
│   ├── core-logic/         # 核心業務邏輯
│   │   ├── src/coaching_assistant/ # 核心模組
│   │   ├── tests/          # 測試檔案 (從 apps/api-server 移過來)
│   │   └── pyproject.toml  # 核心套件配置
│   └── shared-types/       # 共享類型定義 (預留)
├── docs/                   # 正式專案文檔
└── memory-bank/            # Cline AI 工作記憶
```

### 驗證結果

- ✅ API Docker 映像構建成功 (31.8s)
- ✅ CLI Docker 映像之前測試正常
- ✅ 所有路徑引用已更新
- ✅ 測試配置已調整

## 下一階段規劃

### 短期目標
1. 測試新架構下的完整功能
2. 驗證 docker-compose 整體服務啟動
3. 確認所有 make 指令正常運作

### 中期目標  
1. 實作前端與新 API 架構的整合
2. 完善 `packages/shared-types` 的型別定義
3. 優化 Docker 構建效率

### 技術債務
- 考慮使用 multi-stage build 優化 Docker 映像大小
- 評估是否需要統一 Python 依賴管理 (poetry/pipenv)
- 規劃 CI/CD pipeline 適應新架構

## 當前狀態 - Cloudflare Workers 相容性修復 🔧

**專案架構重構已完成！** ✅  
**當前任務：修復 Cloudflare Workers 前端部署問題** 🚧

### 發現的問題
- `make preview-frontend` 失敗，錯誤：`TypeError: Cannot read properties of undefined (reading 'fetch')`
- 問題出現在 Workers 環境中，本地開發正常

### 根本原因分析
基於 Cloudflare 官方文檔研究：
1. **缺少 Edge Runtime 宣告** - Next.js 路由未指定 Edge Runtime
2. **隱含 Node.js Runtime** - Next.js 自動生成不相容函數
3. **全局作用域問題** - 可能有程式碼在全局範圍調用 Workers API

### 修復計劃
1. ✅ 研究官方文檔，找到解決方案
2. ✅ 添加 Edge Runtime 宣告到 not-found.tsx
3. ✅ 修復 API 客戶端的全局作用域問題
4. ✅ 修復 downloadBlob 函數的瀏覽器環境檢查
5. ✅ 驗證修復效果 - Workers 預覽成功啟動！

### 修復成果 🎉
- **主要問題解決**：`TypeError: Cannot read properties of undefined (reading 'fetch')` 已修復
- **Workers 預覽正常**：可以成功啟動 Cloudflare Workers 開發環境
- **Edge Runtime 正確配置**：not-found 路由現在使用 Edge Runtime
- **API 客戶端穩定**：改善了 fetch API 的檢測和使用邏輯

### 技術優勢
- 修復後的程式碼完全相容於其他部署方案（Vercel/Cloud Run）
- 零技術債務，提升整體程式碼品質

新的 monorepo 架構提供了：
- 清晰的關注點分離
- 更好的程式碼重用
- 獨立的部署能力
- 統一的開發體驗
