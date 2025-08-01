# 當前工作重點

## 專案重構完成 ✅

### 已完成的重構任務

1. **目錄結構重組完成**
   - ✅ `apps/container` → `apps/api-server`
   - ✅ 測試檔案從 `apps/api-server/tests/` 移至 `packages/core-logic/tests/`
   - ✅ CLI pyproject.toml 從 `apps/api-server/` 移至 `apps/cli/`
   - ✅ 清理了 `apps/api-server/src/` 中的舊檔案

2. **配置檔案更新完成**
   - ✅ 更新 Makefile 中所有對 `apps/container` 的引用為 `apps/api-server`
   - ✅ 更新測試路徑從 `apps/container/tests/` 到 `packages/core-logic/tests/`
   - ✅ 更新 docker-compose.yml 適應新架構
   - ✅ 修復 Dockerfile.api 路徑問題
   - ✅ 修復 `apps/api-server/requirements.txt` 中相對路徑

3. **Docker 構建測試完成**
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

## 當前狀態

**專案架構重構已完成！** 🎉

新的 monorepo 架構提供了：
- 清晰的關注點分離
- 更好的程式碼重用
- 獨立的部署能力
- 統一的開發體驗
