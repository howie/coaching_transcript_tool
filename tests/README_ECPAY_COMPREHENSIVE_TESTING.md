# ECPay 綜合測試策略

## 概述

基於 ECPay 整合過程中遇到的 7 個錯誤和經驗教訓，本文件定義了一套全面的測試策略，確保 ECPay 整合的可靠性和穩定性。

## 測試層級架構

```
┌─────────────────────────────────────────────────────────────┐
│                    E2E 測試層                                │
│  (前端 + 後端 + ECPay 真實 API)                              │
├─────────────────────────────────────────────────────────────┤
│                   整合測試層                                 │
│  (後端服務 + Mock ECPay API)                                │
├─────────────────────────────────────────────────────────────┤
│                   單元測試層                                 │
│  (個別函數和組件)                                           │
└─────────────────────────────────────────────────────────────┘
```

## 1. 單元測試層

### 1.1 參數生成測試

**目標**: 確保每個參數都符合 ECPay 規格

```python
# tests/unit/test_ecpay_parameter_generation.py

class TestECPayParameterGeneration:
    
    def test_merchant_trade_no_format(self):
        """測試 MerchantTradeNo 格式正確性"""
        # 測試長度限制 (≤20 字元)
        # 測試字元安全性 (只含英數)
        # 測試唯一性
        
    def test_total_amount_format(self):
        """測試 TotalAmount 格式"""
        # 確保是字串格式
        # 測試金額轉換正確性
        
    def test_exec_times_business_rules(self):
        """測試 ExecTimes 業務規則"""
        # 月繳: ExecTimes = "999" (2025年更新規則)
        # 年繳: ExecTimes = "99"
        
    def test_period_type_format(self):
        """測試 PeriodType 格式"""
        # 月繳: "M"
        # 年繳: "Y"
```

### 1.2 CheckMacValue 計算測試

```python
def test_check_mac_value_consistency(self):
    """測試 CheckMacValue 計算一致性"""
    # 測試相同參數產生相同 MAC
    # 測試參數順序不影響 MAC
    # 測試字串格式一致性
    
def test_check_mac_value_with_edge_cases(self):
    """測試邊緣情況的 MAC 計算"""
    # 空字串參數
    # 中文字元參數
    # 特殊字元處理
```

## 2. 整合測試層

### 2.1 ECPay 服務整合測試

```python
# tests/integration/test_ecpay_service_integration.py

class TestECPayServiceIntegration:
    
    def test_authorization_creation_flow(self):
        """測試完整的授權建立流程"""
        # 模擬真實的計費週期和方案
        # 驗證回傳的表單資料完整性
        # 檢查所有必要欄位存在
        
    def test_parameter_format_compliance(self):
        """測試參數格式符合 ECPay 規格"""
        # 驗證所有字串欄位
        # 檢查參數長度限制
        # 確認無不應存在的欄位
        
    def test_different_plan_combinations(self):
        """測試不同方案組合"""
        plans = ["PRO", "ENTERPRISE"]
        cycles = ["monthly", "annual"]
        # 測試所有組合的參數生成
```

### 2.2 API 端點測試

```python
def test_subscription_authorize_endpoint(self):
    """測試訂閱授權 API 端點"""
    response = client.post("/api/v1/subscriptions/authorize", {
        "plan_id": "PRO",
        "billing_cycle": "monthly"
    })
    
    # 驗證回應格式
    assert response["success"] == True
    assert "action_url" in response
    assert "form_data" in response
    
    # 驗證 form_data 完整性
    form_data = response["form_data"]
    assert "CheckMacValue" in form_data
    assert len(form_data["MerchantTradeNo"]) <= 20
```

## 3. E2E 測試層

### 3.1 真實 ECPay API 測試

```python
# tests/e2e/test_ecpay_real_api_integration.py

class TestECPayRealAPIIntegration:
    
    @pytest.mark.integration
    def test_complete_authorization_flow(self):
        """測試完整授權流程"""
        # 1. 呼叫後端 API
        backend_response = call_backend_authorization_api()
        
        # 2. 模擬前端表單提交
        form_submission = simulate_frontend_form_submission(
            backend_response["form_data"]
        )
        
        # 3. 實際調用 ECPay API
        ecpay_response = requests.post(
            backend_response["action_url"],
            data=form_submission
        )
        
        # 4. 驗證結果
        assert ecpay_response.status_code == 200
        assert "10100050" not in ecpay_response.text  # 無參數錯誤
        assert "10200073" not in ecpay_response.text  # 無 MAC 錯誤
        
    def test_parameter_error_prevention(self):
        """測試預防已知參數錯誤"""
        # 確保不會重現已修復的錯誤
        error_codes_to_prevent = [
            "10200052",  # MerchantTradeNo Error
            "10200027",  # TradeNo Error
            "10100228",  # ExecTimes Error
            "10100050",  # Parameter Errors
            "10200073",  # CheckMacValue Error
        ]
        
        response = test_real_ecpay_api()
        for error_code in error_codes_to_prevent:
            assert error_code not in response.text
```

### 3.2 前端整合測試

```python
def test_frontend_form_submission_integrity(self):
    """測試前端表單提交完整性"""
    # 驗證前端不會修改後端參數
    # 檢查 String() 轉換一致性
    # 確認 hidden input 正確建立
    
def test_cross_browser_compatibility(self):
    """測試跨瀏覽器相容性"""
    # 不同瀏覽器的 form encoding
    # JavaScript String() 行為一致性
```

## 4. 錯誤重現測試

### 4.1 已修復錯誤的重現測試

```python
# tests/regression/test_ecpay_error_regression.py

class TestECPayErrorRegression:
    
    def test_merchant_trade_no_length_regression(self):
        """重現 MerchantTradeNo 長度錯誤"""
        # 使用會導致超長 ID 的參數
        # 確認修正後不會超過 20 字元
        
    def test_check_mac_value_regression(self):
        """重現 CheckMacValue 不一致錯誤"""
        # 模擬前端 String() 轉換
        # 確認 MAC 值一致性
        
    def test_parameter_presence_regression(self):
        """重現參數存在性錯誤"""
        # 確認不包含 ProductDesc, ActionType, TradeNo
        # 驗證所有必要參數存在
```

## 5. 效能和可靠性測試

### 5.1 負載測試

```python
def test_concurrent_authorization_requests(self):
    """測試並發授權請求"""
    # 模擬多用戶同時升級
    # 確保 MerchantTradeNo 唯一性
    # 驗證效能表現
    
def test_ecpay_api_timeout_handling(self):
    """測試 ECPay API 超時處理"""
    # 模擬網路延遲
    # 測試超時重試機制
```

### 5.2 資料完整性測試

```python
def test_utf8_encoding_integrity(self):
    """測試 UTF-8 編碼完整性"""
    # 中文字元在各階段保持一致
    # URL encoding 正確性
    
def test_parameter_value_preservation(self):
    """測試參數值保持性"""
    # 前後端傳輸過程不變化
    # JSON 序列化/反序列化一致性
```

## 6. 測試資料和環境

### 6.1 測試資料管理

```python
# tests/fixtures/ecpay_test_data.py

ECPAY_TEST_SCENARIOS = [
    {
        "name": "pro_monthly",
        "plan_id": "PRO", 
        "billing_cycle": "monthly",
        "expected_amount": "899",
        "expected_exec_times": "999"
    },
    {
        "name": "enterprise_annual",
        "plan_id": "ENTERPRISE",
        "billing_cycle": "annual", 
        "expected_amount": "2999",
        "expected_exec_times": "99"
    }
]

PROBLEMATIC_USER_IDS = [
    "550e8400-e29b-41d4-a716-446655440000",  # 標準 UUID
    "user@domain.com",                        # Email 格式
    "用戶中文名稱",                              # 中文字元
    "user with spaces",                       # 包含空格
]
```

### 6.2 測試環境配置

```bash
# ECPay 測試環境變數
export ECPAY_MERCHANT_ID="3002607"
export ECPAY_HASH_KEY="pwFHCqoQZGmho4w6"  
export ECPAY_HASH_IV="EkRm7iFT261dpevs"
export ECPAY_ENVIRONMENT="sandbox"

# 測試標記
pytest -m integration  # 整合測試
pytest -m e2e          # E2E 測試
pytest -m regression   # 回歸測試
```

## 7. 測試執行策略

### 7.1 CI/CD 整合

```yaml
# .github/workflows/ecpay-tests.yml
name: ECPay Integration Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run Unit Tests
        run: pytest tests/unit/test_ecpay_* -v
        
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run Integration Tests
        run: pytest tests/integration/test_ecpay_* -v
        
  e2e-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Run E2E Tests
        run: pytest tests/e2e/test_ecpay_* -v --tb=short
```

### 7.2 測試報告

```python
# tests/conftest.py

@pytest.fixture(scope="session", autouse=True)
def ecpay_test_report():
    """生成 ECPay 測試報告"""
    yield
    
    # 測試完成後生成報告
    generate_ecpay_test_report({
        "total_tests": pytest.total_tests,
        "passed": pytest.passed_tests,
        "failed": pytest.failed_tests,
        "error_coverage": check_error_coverage(),
        "api_call_success_rate": calculate_api_success_rate()
    })
```

## 8. 測試檢核清單

### 8.1 開發階段檢核

- [ ] 單元測試涵蓋所有參數生成邏輯
- [ ] CheckMacValue 計算一致性測試通過
- [ ] 所有已知錯誤情境有回歸測試
- [ ] 參數格式符合 ECPay 最新規格

### 8.2 整合階段檢核

- [ ] 前後端參數傳遞完整性測試
- [ ] 不同方案和計費週期組合測試
- [ ] API 端點回應格式驗證
- [ ] 錯誤處理流程測試

### 8.3 部署前檢核

- [ ] 真實 ECPay API 調用成功
- [ ] 所有已修復錯誤不會重現
- [ ] 效能和負載測試通過
- [ ] 跨瀏覽器相容性確認

## 結論

這套綜合測試策略基於實際遇到的問題和解決經驗，提供了多層級的測試保障：

1. **預防性測試** - 在開發階段就避免常見問題
2. **完整性測試** - 確保前後端整合無縫
3. **真實性測試** - 與真實 ECPay API 的完整驗證
4. **持續性測試** - 透過 CI/CD 持續驗證

通過執行這套測試策略，可以大幅提高 ECPay 整合的可靠性，並為未來的維護和更新提供堅實的測試基礎。

---

*測試策略版本: v2.0*
*基於錯誤解決經驗更新: 2025-08-18*