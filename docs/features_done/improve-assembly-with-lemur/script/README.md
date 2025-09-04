# LeMUR Optimization Verification Scripts

這些腳本用於驗證LeMUR (Large Language Model) 驅動的逐字稿優化功能，包括說話者識別和標點符號改善。

## 📁 文件列表

- `test_lemur_full_pipeline.py` - 完整流程測試：上傳 → 轉檔 → LeMUR優化
- `test_lemur_database_processing.py` - 資料庫處理測試：使用已存在的逐字稿
- `README.md` - 使用說明 (本文件)
- `requirements.txt` - Python依賴套件
- `examples/` - 使用範例

## 🚀 快速開始

### 1. 安裝依賴

```bash
cd docs/features/improve-assembly-with-lemur/script
pip install -r requirements.txt
```

### 2. 設定環境變量

```bash
# 設定API認證token
export AUTH_TOKEN="your_auth_token_here"

# (可選) 設定API URL，默認為 localhost:8000
export API_URL="http://localhost:8000"
```

### 3. 獲取認證Token

```bash
# 使用你的API取得認證token
# 範例：透過登入API獲取
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "password": "your-password"}'
```

## 🧪 測試腳本使用方法

### Script 1: 完整流程測試 (`test_lemur_full_pipeline.py`)

**用途**：測試從音檔上傳到LeMUR優化的完整流程

#### 基本使用
```bash
python test_lemur_full_pipeline.py \
  --audio-file /path/to/coaching_session.mp3 \
  --auth-token $AUTH_TOKEN
```

#### 進階使用
```bash
python test_lemur_full_pipeline.py \
  --audio-file /path/to/coaching_session.mp3 \
  --auth-token $AUTH_TOKEN \
  --session-title "教練對話測試 - 張小姐" \
  --speaker-prompt "這是一段教練與客戶的對話，請識別誰是教練，誰是客戶" \
  --punctuation-prompt "請改善標點符號，讓對話更容易閱讀" \
  --output results_full_pipeline.json
```

#### 參數說明
- `--audio-file`: 音檔路徑 (必需)
- `--auth-token`: 認證token (必需)
- `--session-title`: 自訂會話標題
- `--speaker-prompt`: 自訂說話者識別提示
- `--punctuation-prompt`: 自訂標點符號改善提示
- `--api-url`: API URL (預設: http://localhost:8000)
- `--output`: 結果輸出檔案 (JSON格式)

#### 預期流程
1. ✅ 建立會話
2. ✅ 上傳音檔
3. ✅ 啟動轉檔
4. ⏳ 等待轉檔完成 (可能需要數分鐘)
5. ✅ 取得原始逐字稿
6. ✅ 套用LeMUR說話者識別
7. ✅ 套用LeMUR標點符號優化
8. ✅ 比較前後差異
9. 📊 輸出詳細分析報告

---

### Script 2: 資料庫處理測試 (`test_lemur_database_processing.py`)

**用途**：測試對已存在逐字稿的LeMUR優化處理

#### 查看可用的會話
```bash
python test_lemur_database_processing.py \
  --list-sessions \
  --auth-token $AUTH_TOKEN
```

#### 基本使用
```bash
python test_lemur_database_processing.py \
  --session-id "e7e1a9b2-45a2-4cad-83ae-e2d4a5871bb9" \
  --auth-token $AUTH_TOKEN
```

#### 進階使用
```bash
python test_lemur_database_processing.py \
  --session-id "e7e1a9b2-45a2-4cad-83ae-e2d4a5871bb9" \
  --auth-token $AUTH_TOKEN \
  --speaker-prompt "請根據對話內容判斷誰是教練、誰是客戶" \
  --punctuation-prompt "請添加適當的標點符號，改善可讀性" \
  --output results_db_processing.json
```

#### 部分處理
```bash
# 只執行說話者識別
python test_lemur_database_processing.py \
  --session-id "your-session-id" \
  --auth-token $AUTH_TOKEN \
  --skip-punctuation

# 只執行標點符號優化
python test_lemur_database_processing.py \
  --session-id "your-session-id" \
  --auth-token $AUTH_TOKEN \
  --skip-speaker
```

#### 參數說明
- `--session-id`: 要處理的會話ID (必需，除非使用 --list-sessions)
- `--auth-token`: 認證token (必需)
- `--list-sessions`: 列出可用的已完成會話
- `--speaker-prompt`: 自訂說話者識別提示
- `--punctuation-prompt`: 自訂標點符號改善提示
- `--skip-speaker`: 跳過說話者識別
- `--skip-punctuation`: 跳過標點符號優化
- `--api-url`: API URL (預設: http://localhost:8000)
- `--output`: 結果輸出檔案 (JSON格式)

#### 預期流程
1. ✅ 驗證會話狀態
2. ✅ 取得初始逐字稿段落
3. ✅ 套用LeMUR說話者識別 (如未跳過)
4. ✅ 套用LeMUR標點符號優化 (如未跳過)
5. ✅ 分析變更詳情
6. 📊 輸出詳細比較報告

## 📊 結果解讀

### 成功指標
- ✅ **會話建立/查找成功**
- ✅ **LeMUR處理無錯誤**
- ✅ **資料庫更新成功**
- 📈 **有合理數量的改善** (不一定所有段落都需要改善)

### 結果分析
- **Speaker Changes**: 說話者標記變更數量
- **Content Changes**: 文字內容變更數量
- **Database Updates**: 實際資料庫更新次數
- **Processing Time**: LeMUR處理時間

### 品質評估
```
優秀：變更合理且準確，改善了逐字稿品質
良好：部分改善，少數不必要的變更
可接受：變更較少，可能已經很好了
需檢查：大量變更或處理錯誤
```

## 🔧 故障排除

### 常見錯誤

#### 1. 認證失敗
```
Error: Failed to create session: 401 - Unauthorized
```
**解決方法**：檢查AUTH_TOKEN是否正確且未過期

#### 2. 會話不存在
```
Error: Failed to get session details: 404 - Session not found
```
**解決方法**：使用 `--list-sessions` 查看可用的會話ID

#### 3. 逐字稿未完成
```
Error: Session status is 'processing', expected 'completed'
```
**解決方法**：等待轉檔完成或選擇其他已完成的會話

#### 4. API連線失敗
```
Error: Connection refused
```
**解決方法**：確認API server正在運行且URL正確

### 除錯模式
```bash
# 啟用詳細日誌
python -u test_lemur_*.py [參數] 2>&1 | tee debug.log
```

## 📝 自訂提示詞範例

### 說話者識別提示
```python
speaker_prompt = """
這是一段教練與客戶的一對一對話記錄。
請根據說話內容和語氣判斷：
- 誰是教練 (通常會提問、引導、給予建議)
- 誰是客戶 (通常會分享、回答、描述困擾)

請將說話者標記為「教練」或「客戶」。
"""
```

### 標點符號優化提示
```python
punctuation_prompt = """
請改善這段教練對話的標點符號和斷句：
1. 在適當位置加上逗號、句號
2. 改善語氣詞的標點 (如：喔、嗯、對)
3. 保持原有的說話風格和用詞
4. 讓對話更容易閱讀和理解

請保持內容完整，只改善標點和格式。
"""
```

## 🧪 測試案例建議

### 1. 基本功能測試
- 短音檔 (1-2分鐘)
- 中文教練對話
- 清楚的兩個說話者

### 2. 邊界情況測試
- 長音檔 (>10分鐘)
- 多說話者
- 中英混合
- 背景噪音

### 3. 效能測試
- 大量段落 (>100段)
- 並發處理
- 網路延遲環境

## 📈 效能基準

### 預期處理時間
- **說話者識別**: 30-60秒 (取決於段落數)
- **標點符號優化**: 1-3分鐘 (批次處理)
- **完整轉檔**: 音檔長度 × 0.3-0.8

### 資源使用
- **記憶體**: 通常 < 1GB
- **網路**: 上傳速度影響音檔處理
- **API限制**: LeMUR API有速率限制

## 🔗 相關文件

- [LeMUR API Documentation](../technical/implementation-spec.md)
- [Session ID Mapping](../../../claude/session-id-mapping.md)
- [Error Handling Guide](../../../claude/testing.md)

## 💡 提示與最佳實踐

1. **測試前準備**：確保API server正常運行
2. **選擇合適音檔**：清楚的兩人對話效果最佳
3. **監控處理進度**：使用詳細日誌模式
4. **保存測試結果**：使用 `--output` 保存JSON結果
5. **比較不同提示詞**：測試不同的custom prompt效果
6. **定期測試**：確保功能持續穩定

## ❓ 常見問題

**Q: 為什麼有些段落沒有改變？**
A: LeMUR很聰明，只改真正需要改善的內容。沒有改變通常表示原內容已經很好了。

**Q: 處理時間為什麼很長？**
A: LeMUR使用大語言模型處理，需要時間分析和改善內容。批次處理可以提高效率。

**Q: 如何判斷結果品質？**
A: 檢查範例變更、對比前後內容、驗證說話者識別準確性。

**Q: 可以重複處理同一個會話嗎？**
A: 可以，每次處理都會基於當前資料庫內容，可以用不同prompt重複優化。