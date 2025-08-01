# Coaching Assistant Core Logic

共享的核心邏輯包，提供 coaching transcript 處理功能給所有應用使用。

## 功能特色

- **VTT 格式解析**: 解析 WebVTT 字幕檔案
- **文字處理**: 繁簡體轉換、格式化
- **多種輸出格式**: Markdown、Excel 等
- **Cloud Storage**: AWS S3 整合
- **API 路由**: FastAPI 路由定義

## 架構

```
src/coaching_assistant/
├── api/           # FastAPI 路由定義
├── core/          # 核心處理邏輯
├── exporters/     # 匯出功能 (Markdown, Excel)
├── middleware/    # 中介軟體 (錯誤處理, 日誌)
├── static/        # 靜態資源
└── utils/         # 工具函數
```

## 安裝

```bash
# 開發模式安裝
pip install -e .

# 生產環境安裝
pip install coaching-assistant-core
```

## 使用方式

```python
from coaching_assistant.core.processor import TranscriptProcessor
from coaching_assistant.exporters.markdown import MarkdownExporter

# 處理 VTT 檔案
processor = TranscriptProcessor()
result = processor.process_vtt_content(vtt_content)

# 匯出為 Markdown
exporter = MarkdownExporter()
markdown_content = exporter.export(result)
```

## 開發

```bash
# 安裝開發依賴
pip install -e ".[dev]"

# 執行測試
pytest

# 代碼格式化
black src/
isort src/

# 型別檢查
mypy src/
```

## 依賴套件

- FastAPI: Web API 框架
- Pandas: 資料處理
- OpenCC: 繁簡體轉換
- Boto3: AWS S3 整合
- Pydantic: 資料驗證

## 版本歷史

- **0.1.0**: 初始版本，包含基本的 VTT 處理和匯出功能
