# AssemblyAI 處理流程優化計劃

## 問題分析

### 當前流程存在的效率問題：

1. **重複的繁體中文轉換**
   - 主流程對每個segment執行 `_process_chinese_text`（68次"Converted text to Traditional Chinese"）
   - LeMUR的combined prompt再次處理繁體轉換
   - 造成重複處理和資源浪費

2. **不必要的預處理**
   - 系統先處理所有segments（移除空格+轉繁體）
   - 如果符合LeMUR條件，從原始utterances重新建立segments
   - LeMUR成功後，預處理的segments被丟棄

3. **處理流程效率低下**
   - 預處理 → LeMUR處理 → 使用LeMUR結果
   - 預處理變成浪費（如果LeMUR成功）

## 優化方案

### 方案A：延遲預處理（建議採用）

**檔案**: `src/coaching_assistant/services/assemblyai_stt.py`

**修改內容**：
1. 檢查是否會使用LeMUR優化（lines 591-599）
2. 如果會使用LeMUR，跳過主流程的 `_process_chinese_text` 處理
3. 只有在LeMUR失敗時，才執行fallback預處理

**具體改動**：
```python
# Line 396: 加入條件判斷
needs_conversion = self._needs_traditional_conversion(original_language)

# 提前檢查是否會使用LeMUR
language_code = result.get("language_code") or ""
will_use_lemur = (
    (language_code == "zh" or "zh" in language_code or 
     language_code.startswith("cmn") or language_code in [None, "", "auto"]) 
    and result.get("utterances")
)

# Lines 449, 471, 488: 條件化處理
if not will_use_lemur:  # 只有在不使用LeMUR時才預處理
    text = self._process_chinese_text(text, needs_conversion)
```

### 方案B：移除本地預處理（較激進）

**修改內容**：
1. 完全移除 `_process_chinese_text` 的調用
2. 依賴LeMUR處理所有中文優化
3. 為非中文或LeMUR失敗的情況保留基本處理

### 方案C：優化預處理邏輯（保守方案）

**修改內容**：
1. 保持現有流程
2. 但在建立segments時不執行繁體轉換
3. 只移除空格，讓LeMUR處理繁體轉換

**具體改動**：
```python
# 修改 _process_chinese_text 函數
def _process_chinese_text(self, text: str, needs_conversion: bool, skip_conversion: bool = False) -> str:
    # 總是移除空格
    text = re.sub(...)
    
    # 只在需要且不跳過時才轉換
    if needs_conversion and not skip_conversion:
        text = convert_to_traditional(text)
```

## 實施步驟

1. **備份現有程式碼**
2. **實施方案A**（延遲預處理）
3. **測試驗證**：
   - 上傳中文音檔
   - 確認只有一次處理（無重複log）
   - 驗證LeMUR成功/失敗兩種情況
4. **性能對比**：
   - 記錄處理時間改善
   - 確認結果品質不受影響

## 預期效果

### Before：
- 68次本地繁體轉換
- 1次LeMUR combined處理
- 總計：69次處理

### After：
- 0次本地繁體轉換（如果LeMUR成功）
- 1次LeMUR combined處理
- 總計：1次處理（節省98.5%處理）

## 風險評估

- **低風險**：fallback機制確保品質
- **可回滾**：保留原有邏輯作為備選
- **漸進式**：先在測試環境驗證

## 實施記錄

### 2025-09-08 
- **問題發現**: 從worker log中發現68次重複的"Converted text to Traditional Chinese"
- **分析完成**: 確認主流程預處理與LeMUR處理重複
- **計劃制定**: 提出延遲預處理方案
- **計劃批准**: 用戶確認執行方案A

### 實施進度
- [x] 創建文檔 
- [x] 修改 assemblyai_stt.py
- [x] 測試驗證（lint + unit tests 通過）
- [ ] 部署到生產環境

### 實施詳情

#### 修改內容
1. **添加 will_use_lemur 判斷邏輯** (line 399-405)
   - 檢查語言和utterances條件
   - 決定是否跳過預處理

2. **修改4個 _process_chinese_text 調用點**
   - Line 416: utterances處理
   - Line 461: sentence processing
   - Line 485: remaining words
   - Line 504: fallback text

3. **添加 _apply_fallback_preprocessing 函數** (line 129-153)
   - 當LeMUR失敗時對segments進行後處理
   - 確保fallback品質

4. **更新LeMUR失敗處理邏輯** (line 676-690)
   - 檢測到LeMUR失敗時調用fallback預處理
   - 維持結果品質

#### 測試結果
- ✅ Lint 檢查：無語法錯誤
- ✅ Unit tests：所有測試通過
- ✅ Import 檢查：所有依賴正確

---

**Last Updated**: 2025-09-08  
**Status**: ✅ 實施完成 - 等待生產部署  
**Next Action**: 生產環境測試和部署