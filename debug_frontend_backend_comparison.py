#!/usr/bin/env python3
"""
Debug script to compare frontend vs backend parameter handling
"""

import json
import urllib.parse

def simulate_javascript_string_conversion():
    """模擬 JavaScript String() 轉換行為"""
    
    print("🔍 JavaScript String() 轉換測試")
    print("=" * 60)
    
    # 測試不同資料類型的轉換
    test_values = [
        ("integer", 899),
        ("string", "899"),
        ("empty_string", ""),
        ("null", None),
        ("undefined", None),  # JavaScript undefined
        ("boolean_true", True),
        ("boolean_false", False),
        ("zero", 0)
    ]
    
    for name, value in test_values:
        # Python 轉換
        python_str = str(value) if value is not None else ""
        
        # JavaScript String() 行為模擬
        if value is None:
            js_str = ""
        elif isinstance(value, bool):
            js_str = "true" if value else "false"
        else:
            js_str = str(value)
            
        print(f"   {name:<15}: Python='{python_str}' | JS='{js_str}' | Match: {python_str == js_str}")

def compare_form_data_processing():
    """比較表單資料處理過程"""
    
    print("\n🔍 表單資料處理比較")
    print("=" * 60)
    
    # 模擬後端生成的資料
    backend_data = {
        "TotalAmount": "899",  # 後端已改為 string
        "ExecTimes": "0",      # 後端已改為 string  
        "PeriodAmount": "899", # 後端已改為 string
        "TradeDesc": "教練助手訂閱",
        "ItemName": "訂閱方案#1#個#899"
    }
    
    print("1. 後端生成的資料:")
    for key, value in backend_data.items():
        print(f"   {key}: '{value}' (type: {type(value).__name__})")
    
    print("\n2. 前端 input.value 設定:")
    for key, value in backend_data.items():
        # 模擬前端的 input.value = value
        input_value = value if value is not None else ""
        print(f"   {key}: '{input_value}' (type: {type(input_value).__name__})")
    
    print("\n3. URL 編碼比較:")
    for key, value in backend_data.items():
        backend_encoded = urllib.parse.quote_plus(str(value))
        frontend_encoded = urllib.parse.quote_plus(str(value if value is not None else ""))
        match = backend_encoded == frontend_encoded
        print(f"   {key}: Backend='{backend_encoded}' | Frontend='{frontend_encoded}' | Match: {match}")

def analyze_checkmacvalue_mismatch():
    """分析 CheckMacValue 不匹配的可能原因"""
    
    print("\n🔍 CheckMacValue 不匹配分析")  
    print("=" * 60)
    
    potential_issues = [
        {
            "issue": "前端 JavaScript 環境編碼",
            "description": "瀏覽器的 form.submit() 可能使用不同的編碼方式",
            "solution": "檢查瀏覽器實際發送的 HTTP 請求"
        },
        {
            "issue": "表單欄位順序",
            "description": "HTML form 欄位的順序可能影響提交的參數順序",
            "solution": "確保前端按照 ECPay 要求的順序建立 input 欄位"
        },
        {
            "issue": "隱藏字元或空白",
            "description": "JSON 傳輸過程中可能包含隱藏的空白字元",
            "solution": "在前端對每個值執行 .trim() 清理"
        },
        {
            "issue": "瀏覽器特定行為",
            "description": "不同瀏覽器對 form encoding 的處理可能不同",
            "solution": "測試不同瀏覽器的行為一致性"
        },
        {
            "issue": "ECPay 伺服器端驗證",
            "description": "ECPay 可能對某些欄位有額外的格式要求",
            "solution": "參考 ECPay 官方範例，確保所有欄位格式正確"
        }
    ]
    
    for i, issue in enumerate(potential_issues, 1):
        print(f"{i}. {issue['issue']}:")
        print(f"   問題: {issue['description']}")
        print(f"   解決: {issue['solution']}\n")

def generate_frontend_debug_code():
    """生成前端除錯代碼"""
    
    print("🔍 前端除錯代碼建議")
    print("=" * 60)
    
    debug_code = '''
// 在 ChangePlan.tsx 的 handleConfirmChange 函數中加入此除錯代碼

console.log("=== ECPay Form Debug ===");
console.log("Backend Response:", data);

// 檢查每個表單欄位
const formDebug = {};
Object.entries(data.form_data).forEach(([key, value]) => {
  const input = document.createElement('input');
  input.value = value === null || value === undefined ? '' : value;
  
  formDebug[key] = {
    original: value,
    final: input.value,
    type: typeof value,
    length: input.value.length
  };
});

console.log("Form Fields Debug:", formDebug);

// 重點檢查關鍵欄位
const keyFields = ['CheckMacValue', 'TotalAmount', 'MerchantTradeNo', 'TradeDesc', 'ItemName'];
keyFields.forEach(field => {
  if (formDebug[field]) {
    console.log(`${field}: "${formDebug[field].final}" (${formDebug[field].type}, len=${formDebug[field].length})`);
  }
});

// 檢查是否有隱藏字元
Object.entries(formDebug).forEach(([key, info]) => {
  const hasHidden = info.final !== info.final.trim();
  if (hasHidden) {
    console.warn(`${key} has hidden characters:`, JSON.stringify(info.final));
  }
});
'''
    
    print(debug_code)

if __name__ == "__main__":
    simulate_javascript_string_conversion()
    compare_form_data_processing()
    analyze_checkmacvalue_mismatch()
    generate_frontend_debug_code()
    
    print("\n🎯 下一步建議:")
    print("1. 在前端加入上述除錯代碼")
    print("2. 實際測試時檢查 browser console 輸出")
    print("3. 使用瀏覽器 Network 面板檢查實際 HTTP 請求")
    print("4. 比較成功案例的參數格式")
    print("5. 測試不同瀏覽器的行為")