# ECPay 整合故障排除指南

## 概述

本指南提供 ECPay 綠界金流整合過程中常見問題的診斷和解決方案，基於實際遇到的 7 個錯誤的解決經驗整理而成。

## 常見錯誤代碼和解決方案

### 1. MerchantTradeNo Error (10200052)

**錯誤訊息**: `MerchantTradeNo Error`

**可能原因**:
- MerchantTradeNo 超過 20 字元限制
- 包含非法字元（僅允許英數字）
- 格式不符合 ECPay 要求

**診斷步驟**:
```python
# 檢查 MerchantTradeNo 長度和格式
merchant_trade_no = "SUB1723967234USER12345"
print(f"Length: {len(merchant_trade_no)}")  # 應 ≤ 20
print(f"Valid chars: {merchant_trade_no.isalnum()}")  # 應為 True
```

**解決方案**:
```python
# 正確的 MerchantTradeNo 生成
timestamp = int(time.time())
safe_user_prefix = ''.join(c for c in user_id[:8].upper() if c.isalnum())[:8]
merchant_trade_no = f"SUB{str(timestamp)[-6:]}{safe_user_prefix}"  # ≤ 17 字元
```

### 2. TradeNo Error (10200027)

**錯誤訊息**: `TradeNo Error`

**可能原因**:
- 使用錯誤的 API 端點
- 混用不同版本的 ECPay API

**解決方案**:
```python
# 使用正確的端點
# ❌ 錯誤 - CreditDetail 適用於單次付款
credit_url = "https://payment-stage.ecpay.com.tw/CreditDetail/DoAction"

# ✅ 正確 - AioCheckOut V5 適用於定期定額
aio_url = "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"
```

### 3. ExecTimes Error (10100228 / 10100227)

**錯誤訊息**: 
- `ExecTimes Error, PeriodType equal Y, ExecTimes between 2 and 99`
- `ExecTimes Error, PeriodType equal M, ExecTimes between 2 and 999`

**可能原因**:
- ExecTimes 值不符合 ECPay 業務規則

**ECPay 規則** (2025年更新):
- `PeriodType = "M"`: ExecTimes 必須在 2-999 之間
- `PeriodType = "Y"`: ExecTimes 必須在 2-99 之間

**解決方案**:
```python
# 正確的 ExecTimes 設定 (2025年更新)
exec_times = "999" if billing_cycle == "monthly" else "99"
period_type = "M" if billing_cycle == "monthly" else "Y"
```

### 4. Parameter Error (10100050)

**錯誤訊息**: `Parameter Error. [FieldName] Not In Spec`

**可能原因**:
- 使用了 API 版本不支援的參數
- 參數名稱錯誤或拼寫錯誤

**常見不支援的參數**:
- `ActionType` - AioCheckOut V5 不需要
- `ProductDesc` - V5 僅支援 TradeDesc 和 ItemName
- `TradeNo` - 由 ECPay 生成，不應在建立時提供

**解決方案**:
```python
# ❌ 不要包含這些參數
"ActionType": "CreateAuth",  # V5 不支援
"ProductDesc": "產品描述",    # V5 不支援  
"TradeNo": "ECPay_generated" # 由 ECPay 生成

# ✅ 使用正確的參數
"TradeDesc": "教練助手訂閱",
"ItemName": "訂閱方案#1#個#899"
```

### 5. CheckMacValue Error (10200073) - 🔴 待解決問題

**錯誤訊息**: `CheckMacValue Error` + 常見失敗原因說明

**ECPay 提供的常見原因**:
- 商店尚未開啟收款服務，請聯繫商店處理
- 交易金額低於下限或超過上限
- 此商店未提供任何付款方式，請聯繫商店處理
- 此商店所傳送串接參數錯誤，請聯繫商店處理

**當前狀況** (2025-08-20):
- ❌ **問題持續存在**: 即使修正所有已知參數問題，仍出現 CheckMacValue 錯誤
- ❌ **已嘗試方案**: 
  - 重新計算 CheckMacValue 演算法
  - 修正所有參數格式問題
  - 確認 UTF-8 編碼正確性
  - 測試不同的參數組合
- 🔍 **需要進一步調查**: 可能是測試商店設定或 ECPay 服務端問題

**下一步行動**:
1. **聯繫 ECPay 技術支援** - 詢問測試商店 3002607 狀態
2. **請求詳細錯誤資訊** - 取得更具體的失敗原因
3. **驗證商店設定** - 確認定期定額功能是否已啟用
4. **考慮申請新的測試商店** - 如果目前商店有問題

**診斷方法**:
1. **測試 ECPay 服務狀態**:
   ```bash
   curl -I https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5
   # 應該回傳 200，如果是 500 表示服務異常
   ```

2. **檢查測試商店狀態**:
   - 確認測試商店 3002607 是否仍然可用
   - 聯繫 ECPay 技術支援確認狀態

3. **驗證 CheckMacValue 計算**:
   ```python
   # 使用官方範例參數測試
   test_params = {
       "MerchantID": "3002607",
       "MerchantTradeNo": "TEST" + str(int(time.time())),
       "TotalAmount": "100",  # 使用小額測試
       "TradeDesc": "Test Order",
       "ItemName": "Test Item",
       # ... 其他基本參數
   }
   ```

**診斷步驟**:

1. **檢查參數格式一致性**:
```python
# 確保所有數值參數都是字串格式
auth_data = {
    "TotalAmount": str(amount),      # 不是 int
    "ExecTimes": str(exec_times),    # 不是 int
    "PeriodAmount": str(period_amt), # 不是 int
}
```

2. **驗證簽章計算過程**:
```bash
# 運行除錯腳本
python debug_checkmacvalue.py
```

3. **檢查前端處理**:
```javascript
// 前端不應修改參數值
input.value = value === null || value === undefined ? '' : String(value).trim()
```

**解決步驟**:

1. **後端統一使用字串格式**
2. **前端避免型別轉換**
3. **檢查 UTF-8 編碼一致性**
4. **驗證參數排序邏輯**

## 診斷工具和方法

### 1. 使用除錯腳本

```bash
# 運行 CheckMacValue 計算驗證
python debug_checkmacvalue.py

# 運行前後端比較分析
python debug_frontend_backend_comparison.py
```

### 2. 前端除錯

在瀏覽器控制台檢查：
```javascript
// 檢查表單資料完整性
console.log("=== ECPay Form Debug ===");
console.log("Form Fields:", formDebug);

// 檢查關鍵參數
['CheckMacValue', 'TotalAmount', 'MerchantTradeNo'].forEach(field => {
  console.log(`${field}: "${formData[field]}"`);
});
```

### 3. 網路請求檢查

使用瀏覽器 Network 面板：
- 檢查實際送出的表單資料
- 確認 Content-Type 正確
- 驗證參數編碼無誤

## 預防措施檢查清單

### 開發階段
- [ ] 所有數值參數使用字串格式
- [ ] MerchantTradeNo 長度 ≤ 20 字元
- [ ] 只使用 API 版本支援的參數
- [ ] ExecTimes 符合業務規則
- [ ] 中文字元 UTF-8 編碼正確

### 測試階段
- [ ] 單元測試覆蓋所有參數組合
- [ ] 整合測試包含前後端完整流程
- [ ] E2E 測試使用真實 ECPay API
- [ ] 多瀏覽器相容性測試

### 部署前檢查
- [ ] CheckMacValue 計算一致性驗證
- [ ] 所有已知錯誤情境測試通過
- [ ] 生產環境 ECPay 設定正確
- [ ] 監控和日誌系統就緒

## 錯誤處理最佳實踐

### 1. 完整的錯誤日誌

```python
# 記錄關鍵參數用於除錯
logger.info(f"ECPay Request - MerchantTradeNo: {merchant_trade_no}")
logger.info(f"ECPay Request - CheckMacValue: {check_mac_value[:8]}...")
logger.info(f"ECPay Response: {response_data}")
```

### 2. 參數驗證

```python
def validate_ecpay_params(auth_data):
    """驗證 ECPay 參數格式"""
    
    # 長度檢查
    assert len(auth_data["MerchantTradeNo"]) <= 20
    
    # 格式檢查
    assert auth_data["TotalAmount"].isdigit()
    assert auth_data["ExecTimes"].isdigit()
    
    # 業務規則檢查
    if auth_data["PeriodType"] == "Y":
        exec_times = int(auth_data["ExecTimes"])
        assert 2 <= exec_times <= 99
```

### 3. 降級方案

```python
def handle_ecpay_error(error_code, user_id):
    """處理 ECPay 錯誤的降級方案"""
    
    if error_code in ["10200052", "10200027"]:
        # 參數錯誤 - 記錄並通知開發團隊
        notify_dev_team(f"ECPay parameter error: {error_code}")
        
    # 提供用戶替代方案
    return {
        "success": False,
        "message": "付款服務暫時無法使用，請稍後再試或聯繫客服",
        "support_contact": "support@example.com"
    }
```

## 參考資源

### ECPay 官方文檔
- [AioCheckOut V5 API](https://developers.ecpay.com.tw/?p=16449)
- [信用卡定期定額文檔](https://developers.ecpay.com.tw/?p=16551)
- [CheckMacValue 計算說明](https://developers.ecpay.com.tw/?p=2856)

### 測試工具
- [ECPay 測試環境](https://payment-stage.ecpay.com.tw/)
- [ECPay 參數檢測工具](https://developers.ecpay.com.tw/developer-tools)

### 社群資源
- [ECPay 開發者論壇](https://developers.ecpay.com.tw/forum)
- [GitHub ECPay SDK](https://github.com/ECPay)

## 支援聯繫

### 內部團隊
- 開發團隊：當遇到新的錯誤類型時
- 測試團隊：進行回歸測試驗證
- 營運團隊：監控付款成功率

### 外部支援
- ECPay 技術支援：官方 API 問題
- 瀏覽器廠商：瀏覽器相容性問題

---

*最後更新：2025-08-18*
*基於 7 個實際錯誤的解決經驗編寫*