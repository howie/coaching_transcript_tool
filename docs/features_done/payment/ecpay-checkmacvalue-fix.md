# ECPay CheckMacValue Error (10200073) 修復記錄

## 問題概述

**錯誤代碼**: 10200073  
**錯誤訊息**: CheckMacValue Error  
**根本原因**: CheckMacValue 計算方法不符合 ECPay 官方規範  
**修復日期**: 2025-08-28  

## 問題分析

### 初始誤判
最初將問題歸因於 Content Security Policy (CSP) 警告，但實際上：
- **CheckMacValue Error (10200073)** = 伺服器端簽章計算錯誤
- **CSP 警告訊息** = ECPay 付款頁面的瀏覽器安全機制，與 CheckMacValue 無關

### 真正原因
CheckMacValue 計算缺少關鍵的第 7 步：**.NET 風格字元替換**

## 解決方案

### ECPay 官方 8 步計算法

```python
def _generate_check_mac_value(self, data: Dict[str, str]) -> str:
    """
    ECPay CheckMacValue 官方 8 步計算法：
    
    1. 移除 CheckMacValue 參數
    2. 參數 A-Z 排序  
    3. 建立 key=value 查詢字串
    4. 加入 HashKey/HashIV: HashKey={key}&{query}&HashIV={iv}
    5. URL 編碼整個字串
    6. 轉小寫
    7. .NET 風格替換 ⭐ 關鍵步驟
    8. SHA256 雜湊 + 轉大寫
    """
    
    # Step 1: 移除 CheckMacValue
    clean_data = {k: v for k, v in data.items() if k != "CheckMacValue"}
    
    # Step 2: A-Z 排序
    sorted_items = sorted(clean_data.items())
    
    # Step 3: 建立查詢字串
    param_strings = []
    for key, value in sorted_items:
        param_strings.append(f"{key}={value}")
    query_string = "&".join(param_strings)
    
    # Step 4: 加入 HashKey 和 HashIV
    raw_string = f"HashKey={self.hash_key}&{query_string}&HashIV={self.hash_iv}"
    
    # Step 5: URL 編碼
    encoded_string = urllib.parse.quote_plus(raw_string)
    
    # Step 6: 轉小寫
    encoded_lower = encoded_string.lower()
    
    # Step 7: .NET 風格替換 ⭐
    replacements = {
        '%2d': '-',   # dash
        '%5f': '_',   # underscore  
        '%2e': '.',   # period
        '%21': '!',   # exclamation
        '%2a': '*',   # asterisk
        '%28': '(',   # left parenthesis
        '%29': ')'    # right parenthesis
    }
    
    final_string = encoded_lower
    for old, new in replacements.items():
        final_string = final_string.replace(old, new)
    
    # Step 8: SHA256 + 大寫
    return hashlib.sha256(final_string.encode('utf-8')).hexdigest().upper()
```

### 關鍵差異

| 步驟 | 修正前 | 修正後 |
|------|--------|--------|
| 1-6 | ✅ 正確 | ✅ 正確 |
| **7. .NET 替換** | ❌ **缺少** | ✅ **新增** |
| 8 | ✅ 正確 | ✅ 正確 |

## 修改的文件

### 後端服務
- `src/coaching_assistant/core/services/ecpay_service.py`
  - 更新 `_generate_check_mac_value()` 方法
  - 加入完整的官方 8 步計算流程
  - 改進日誌輸出

### 前端組件  
- `apps/web/components/billing/ChangePlan.tsx`
  - 移除不必要的 CSP nonce 相關代碼
  - 簡化表單提交邏輯

### 清理工作
- 移除所有 CSP nonce 相關的臨時文件
- 移除不必要的 middleware 和 context

## 測試驗證

### 測試結果
| 測試項目 | 結果 | 說明 |
|----------|------|------|
| 基本付款 | ✅ 通過 | 最小參數集合測試 |
| 定期定額 | ✅ 通過 | 完整定期定額參數 |
| ECPay API | ✅ 成功 | 實際進入付款頁面 |
| 官方規範 | ✅ 符合 | 嚴格遵循 8 步流程 |

### 驗證方法
```bash
# 運行官方規範驗證
python tmp/ecpay_archive/ecpay_checkmacvalue_strict_fix.py

# 使用瀏覽器測試實際付款
open tmp/ecpay_archive/ecpay_fixed_implementation_test.html
```

## 重要提醒

### ✅ 已解決
- CheckMacValue Error (10200073) 完全修復
- 實作符合 ECPay 官方規範的計算方法
- 建立完整的測試驗證機制

### ⚠️ 注意事項  
- **CSP 警告可以忽略** - 那是 ECPay 付款頁面的瀏覽器安全機制
- **生產環境** - 確保使用正確的 HashKey/HashIV
- **安全性** - 絕不將 HashKey/HashIV 暴露到前端

## 學到的經驗

1. **嚴格遵循官方文檔** - ECPay 的 8 步驟不可省略任何一步
2. **.NET 風格替換是關鍵** - 這是最容易被忽略但又最重要的步驟  
3. **區分不同類型的錯誤** - CheckMacValue 錯誤與 CSP 警告是完全不同的問題
4. **逐步驗證** - 在除錯時要分別驗證每個計算步驟

## 後續監控

建議監控以下指標：
- CheckMacValue Error 的發生率
- 付款成功率和失敗原因  
- ECPay API 的回應時間
- 用戶付款流程的完成率

---

**狀態**: ✅ 已完全解決  
**修復日期**: 2025-08-28  
**負責人**: Claude Code Assistant  
**驗證**: 通過實際 ECPay API 測試