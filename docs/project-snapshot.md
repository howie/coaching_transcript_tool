# 專案快照 (Project Snapshot)

生成時間：2025-07-31 10:29 (UTC+8)

## 專案概覽 (Project Overview)

**專案名稱：** Coaching Transcript Tool  
**版本：** 1.1.0  
**GitHub：** https://github.com/howie/coaching_transcript_tool  
**作者：** Howie Yu (howie.yu@gmail.com)  
**授權：** MIT License  

### 專案描述
一個專業的教練對話逐字稿處理工具，支援將 VTT 格式的逐字稿轉換為結構化的 Markdown 或 Excel 文件。專案正從單純的 CLI 工具演進為完整的 SaaS 服務，計劃整合至 Custom GPT 和其他 AI Agent 平台。

## 技術架構 (Technical Architecture)

### 核心技術棧
- **後端框架：** FastAPI + Flask (混合架構)
- **程式語言：** Python 3.8+
- **資料處理：** pandas, openpyxl
- **中文處理：** opencc-python-reimplemented
- **認證：** Google OAuth 2.0 (設定中)
- **雲端整合：** AWS S3 (boto3)
- **容器化：** Docker, Docker Compose
- **CLI框架：** Typer
- **測試框架：** pytest

### 應用架構
```
coaching_transcript_tool/
├── main.py                 # FastAPI 主應用入口
├── app/                    # Web 應用層
│   ├── __init__.py        # Flask 應用初始化
│   ├── frontend/          # Flask 前端
│   │   └── routes.py      # 前端路由
│   ├── api/               # FastAPI API
│   │   └── api_service.py # API 服務端點
│   ├── static/            # 靜態資源
│   └── templates/         # HTML 範本
├── src/                   # 核心業務邏輯
│   └── coaching_assistant/
│       ├── cli.py         # CLI 介面
│       ├── parser.py      # VTT 解析器
│       ├── core/          # 核心處理邏輯
│       ├── exporters/     # 輸出格式處理
│       └── utils/         # 工具函式
├── tests/                 # 測試套件
├── docs/                  # 專案文件
└── frontend/              # (待整理)
```

## 核心功能 (Core Features)

### 1. 檔案格式支援
- **輸入格式：** VTT (WebVTT) 逐字稿檔案
- **輸出格式：** 
  - Markdown (.md) - 適合閱讀和版本控制
  - Excel (.xlsx) - 適合數據分析和處理

### 2. 文字處理功能
- **說話者匿名化：** 將特定姓名替換為 "Coach" 和 "Client"
- **中文轉換：** 簡體中文轉繁體中文支援
- **說話者合併：** 自動合併連續的同一說話者內容
- **時間戳保留：** 維持原始時間標記資訊

### 3. 多種使用介面
- **CLI 工具：** `transcript-tool` 命令行介面
- **Web 介面：** Flask 前端提供檔案上傳和處理
- **API 服務：** RESTful API 端點供程式化存取
- **Custom GPT 整合：** (開發中) 透過 OpenAPI schema 整合

### 4. 雲端功能
- **檔案上傳：** 支援大檔案上傳處理
- **S3 整合：** AWS S3 儲存未識別格式檔案片段
- **容器化部署：** Docker 支援，準備雲端部署

## 專案配置 (Project Configuration)

### 環境變數配置
```bash
# Google OAuth 設定
GOOGLE_OAUTH_SECRETS="..."
GOOGLE_OAUTH_REDIRECT_URI="http://localhost:8000/oauth2callback"
FLASK_SECRET_KEY="your-secret-key-here"

# AWS 設定
S3_BUCKET_NAME="your-s3-bucket-name"
AWS_ACCESS_KEY_ID="your-aws-access-key-id"
AWS_SECRET_ACCESS_KEY="your-aws-secret-access-key"
AWS_REGION="your-aws-region"
```

### 依賴套件 (主要)
```toml
dependencies = [
    "pandas>=1.3.0",
    "openpyxl>=3.0.9",
    "fastapi>=0.100.0",
    "uvicorn>=0.22.0",
    "flask==3.0.2",
    "python-multipart",
    "typer[all]",
    "boto3>=1.28.0",
    "python-dotenv>=1.0.0",
    "opencc-python-reimplemented==0.1.7"
]
```

### Docker 配置
- **CLI 工具：** `Dockerfile` - 輕量級 Python 3.10 映像
- **API 服務：** `Dockerfile.api` - 多階段構建，包含健康檢查
- **Docker Compose：** 提供完整的開發和部署環境

## 開發工作流程 (Development Workflow)

### 可用的 Make 命令
```bash
make help          # 顯示所有可用命令
make clean         # 清理建置產物
make build         # 建置套件
make install       # 本地安裝
make dev-setup     # 安裝開發依賴
make test          # 執行測試
make lint          # 程式碼檢查
make docker        # 建置 Docker 映像
make docker-run    # 執行 Docker 容器
```

### CLI 使用範例
```bash
# 基本轉換
transcript-tool format-command input.vtt output.md

# Excel 輸出
transcript-tool format-command input.vtt output.xlsx --format excel

# 說話者匿名化
transcript-tool format-command input.vtt output.md \
    --coach-name "Dr. Smith" --client-name "Mr. Johnson"

# 繁體中文轉換
transcript-tool format-command input.vtt output.md --traditional
```

### API 端點
```
POST /api/format
- 檔案上傳和處理
- 支援多種輸出格式
- 說話者替換和中文轉換

GET /api/openai.json
- OpenAPI schema 檔案
- Custom GPT 整合使用
```

## 當前開發狀態 (Current Development Status)

### ✅ 已完成功能
- [x] CLI 工具核心功能
- [x] VTT 檔案解析和處理
- [x] Markdown/Excel 輸出格式
- [x] Flask Web 介面基礎功能
- [x] FastAPI API 服務架構
- [x] Docker 容器化支援
- [x] 基礎的 Google OAuth 設定 (模擬登入)
- [x] S3 整合 (錯誤檔案上傳)

### 🚧 進行中
- [ ] 程式碼模組化重構
- [ ] 完整的認證系統
- [ ] Custom GPT Action 整合
- [ ] 雲端部署自動化

### 📝 待開發功能
- [ ] API Key 認證機制
- [ ] 使用量限制和計費
- [ ] Slack/Teams Bot 整合
- [ ] 進階 AI 功能 (Whisper 整合)
- [ ] 管理後台介面

## 專案文件結構 (Documentation Structure)

```
docs/
├── architect.md    # 架構設計文件
├── changelog.md    # 變更日誌
├── roadmap.md     # 發展藍圖 (4個階段)
└── todo.md        # 詳細任務清單 (10個主要項目)
```

## 發展策略 (Development Strategy)

### Phase 1: 基礎建設與重構 ✅
- 程式碼模組化
- API 骨架建立
- 單元測試導入
- 開發環境標準化

### Phase 2: API 服務化與 GPT 整合 🚧
- 完善 API 功能
- 雲端部署
- Custom GPT Action 建立
- 基礎文件撰寫

### Phase 3: 商業化與生態系拓展 📝
- 使用者認證與計費
- 平台整合 (Slack/Teams)
- 市場推廣
- 監控與維運

### Phase 4: 企業級功能 📝
- 進階 AI 功能
- 安全性強化
- 多租戶架構
- 國際化支援

## 部署配置 (Deployment Configuration)

### 本地開發
```bash
# 啟動開發環境
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 或使用 Docker Compose
docker-compose up -d
```

### 生產部署
- 支援 Fly.io, Render, Railway 等雲端平台
- 使用 Docker 多階段構建最佳化映像大小
- 內建健康檢查和優雅關閉

## 品質保證 (Quality Assurance)

### 測試策略
```
tests/
├── conftest.py          # pytest 配置
├── test_processor.py    # 核心處理邏輯測試
└── data/               # 測試資料
    ├── sample_1.vtt
    └── sample_2.vtt
```

### 程式碼品質
- Python 3.8+ 支援
- Type hints 使用
- 結構化錯誤處理
- 完整的日誌記錄

## 商業模式規劃 (Business Model Planning)

### 目標市場
- 專業教練 (Life Coach, Executive Coach)
- 企業培訓部門
- 顧問公司
- AI Agent 開發者

### 價值主張
- 自動化逐字稿處理，節省人工時間
- 隱私保護的說話者匿名化
- 多語言支援 (中文轉換)
- 多平台整合能力

### 收入模式 (計劃)
- API 使用量計費
- 企業級功能訂閱
- Custom GPT 整合服務

## 技術債務和改進機會 (Technical Debt & Improvements)

### 已識別問題
1. **架構混雜：** Flask + FastAPI 並存，需整合或選擇
2. **設定分散：** 環境變數和設定檔管理需統一
3. **測試覆蓋率：** 需要更完整的測試套件
4. **錯誤處理：** API 錯誤回應需標準化
5. **文件同步：** 程式碼和文件需保持同步

### 改進建議
1. 選擇單一 Web 框架 (建議 FastAPI)
2. 建立統一的設定管理系統
3. 實作完整的 CI/CD pipeline
4. 加強 API 文件和範例
5. 建立效能基準測試

## 風險評估 (Risk Assessment)

### 技術風險
- **依賴套件安全性：** 定期更新和安全性掃描
- **檔案處理安全：** 上傳檔案的格式驗證和大小限制
- **資料隱私：** 敏感資料的處理和儲存機制

### 商業風險
- **競爭對手：** 類似服務的市場競爭
- **使用者接受度：** 新工具的學習曲線
- **法規遵循：** GDPR 等資料保護法規

## 聯絡資訊 (Contact Information)

**維護者：** Howie Yu  
**Email：** howie.yu@gmail.com  
**GitHub：** https://github.com/howie/coaching_transcript_tool  
**Issue 追蹤：** https://github.com/howie/coaching_transcript_tool/issues  

---

*此文件為專案當前狀態的完整快照，用於重構規劃和團隊協作參考。*
