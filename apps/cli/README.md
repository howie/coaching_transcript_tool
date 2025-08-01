# Coaching Transcript CLI Tool

獨立的命令列工具，用於處理教練對話逐字稿文件。

## 功能特色

- 將 VTT 格式的逐字稿轉換為結構化的 Markdown 或 Excel 文件
- 支援說話者匿名化處理
- 支援簡體中文轉繁體中文
- 完全容器化，無需本地 Python 環境

## 快速開始

### 使用 Docker 運行

1. **建置 Docker 映像**：
   ```bash
   # 在專案根目錄執行
   docker build -f apps/cli/Dockerfile -t coaching-transcript-cli .
   ```

2. **基本使用**：
   ```bash
   # 顯示幫助
   docker run --rm coaching-transcript-cli --help
   
   # 轉換 VTT 到 Markdown
   docker run --rm -v /path/to/data:/data coaching-transcript-cli \
     format-command /data/input.vtt /data/output.md
   
   # 轉換 VTT 到 Excel
   docker run --rm -v /path/to/data:/data coaching-transcript-cli \
     format-command /data/input.vtt /data/output.xlsx --format excel
   ```

3. **進階選項**：
   ```bash
   # 匿名化說話者並轉換為繁體中文
   docker run --rm -v /path/to/data:/data coaching-transcript-cli \
     format-command /data/input.vtt /data/output.md \
     --coach "張教練" --client "李同學" --traditional
   ```

## 命令選項

### `format-command`

將 VTT 文件轉換為指定格式：

- `input_file`: 輸入的 VTT 文件路徑
- `output_file`: 輸出文件路徑
- `--format, -f`: 輸出格式 (`markdown` 或 `excel`)
- `--coach`: 教練姓名（將被替換為 "Coach"）
- `--client`: 學員姓名（將被替換為 "Client"）
- `--traditional`: 轉換簡體中文為繁體中文

## 依賴說明

此 CLI 工具依賴於：
- `packages/core-logic`: 共享的核心業務邏輯
- `typer`: 命令列介面框架
- `openpyxl`: Excel 文件處理
- `pandas`: 數據處理

## 架構特色

- **單一職責**: 專注於命令列處理，不包含 API 服務相關依賴
- **共享邏輯**: 使用 `packages/core-logic` 確保與 API 服務的一致性
- **輕量化**: Docker 映像只包含 CLI 執行所需的最小依賴
