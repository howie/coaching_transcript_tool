#!/usr/bin/env python3
"""
檢查實際後端生成的參數
"""

import sys
import hashlib
import urllib.parse

sys.path.insert(0, 'src')

# 從前端日誌中提取的實際參數
# 基於用戶提供的 debug 輸出
ACTUAL_FRONTEND_PARAMS = {
    # 從你的 console.log 中看到的實際值
    "MerchantTradeNo": "SUB5249949B9F9BDC",
    "TotalAmount": "8999",
    "TradeDesc": "教練助手訂閱", 
    "ItemName": "訂閱方案#1#個#8999",
    "CheckMacValue": "5DCC55EEA22463E1F51DDF39CD65D0FB21D085A2595849F6B2D5997EAE0D3216"  # 前端實際值
}

def generate_checkmacvalue_exact(data, hash_key, hash_iv):
    """精確重現 CheckMacValue 計算"""
    
    # 移除 CheckMacValue
    filtered_data = {k: v for k, v in data.items() if k != "CheckMacValue"}
    
    print("🔍 實際參數 (按字母順序):")
    for key, value in sorted(filtered_data.items()):
        print(f"   {key}: '{value}'")
    
    # 按 ASCII 排序
    sorted_items = sorted(filtered_data.items())
    
    # URL 編碼
    encoded_params = []
    for key, value in sorted_items:
        str_value = str(value) if value is not None else ""
        encoded_value = urllib.parse.quote_plus(str_value, encoding='utf-8')
        encoded_params.append(f"{key}={encoded_value}")
    
    query_string = "&".join(encoded_params)
    raw_string = f"HashKey={hash_key}&{query_string}&HashIV={hash_iv}"
    
    print(f"\n🔍 Raw string:")
    print(f"   {raw_string}")
    
    # URL 編碼並轉小寫
    encoded_string = urllib.parse.quote_plus(raw_string, encoding='utf-8').lower()
    
    print(f"\n🔍 Final encoded string:")
    print(f"   {encoded_string}")
    
    # SHA256
    calculated_hash = hashlib.sha256(encoded_string.encode('utf-8')).hexdigest().upper()
    
    return calculated_hash

def reverse_engineer_from_frontend():
    """從前端提交的參數逆推完整參數集"""
    
    print("🔍 從前端逆推完整參數")
    print("=" * 60)
    
    # 推測完整參數集 (基於 ECPay 要求和前端顯示的值)
    complete_params = {
        "MerchantID": "3002607",
        "MerchantMemberID": "USER9B9F9BDC1755524994",  # 從前端日誌
        "MerchantTradeNo": "SUB5249949B9F9BDC",       # 從前端日誌
        "TotalAmount": "8999",                         # 從前端日誌 (年繳價格)
        "OrderResultURL": "http://localhost:3000/subscription/result",
        "ReturnURL": "http://localhost:8000/api/webhooks/ecpay-auth",
        "ClientBackURL": "http://localhost:3000/billing",
        "PeriodType": "Y",                             # 年繳
        "Frequency": "1",
        "PeriodAmount": "8999",                        # 應與 TotalAmount 相同
        "ExecTimes": "99",                             # 年繳規則
        "PaymentType": "aio",
        "ChoosePayment": "Credit",
        "TradeDesc": "教練助手訂閱",                   # 從前端日誌
        "ItemName": "訂閱方案#1#個#8999",              # 從前端日誌
        "MerchantTradeDate": "2025/08/18 21:52:45",   # 估計時間
        "ExpireDate": "7",
        "Remark": "",
        "ChooseSubPayment": "",
        "PlatformID": "",
        "EncryptType": "1",
        "BindingCard": "0",
        "CustomField1": "ENTERPRISE",                  # 年繳企業方案
        "CustomField2": "annual",
        "CustomField3": "9B9F9BDC",
        "CustomField4": "",
        "NeedExtraPaidInfo": "N",
        "DeviceSource": "",
        "IgnorePayment": "",
        "Language": "",
    }
    
    hash_key = "pwFHCqoQZGmho4w6"
    hash_iv = "EkRm7iFT261dpevs"
    
    calculated_mac = generate_checkmacvalue_exact(complete_params, hash_key, hash_iv)
    frontend_mac = "5DCC55EEA22463E1F51DDF39CD65D0FB21D085A2595849F6B2D5997EAE0D3216"
    
    print(f"\n🔍 CheckMacValue 比較:")
    print(f"   前端提交: {frontend_mac}")
    print(f"   我們計算: {calculated_mac}")
    print(f"   是否一致: {'✅ 是' if calculated_mac == frontend_mac else '❌ 否'}")
    
    return complete_params, calculated_mac

def try_parameter_variations():
    """嘗試不同的參數組合"""
    
    print("\n🧪 嘗試參數變化")
    print("=" * 60)
    
    base_params = {
        "MerchantID": "3002607",
        "MerchantMemberID": "USER9B9F9BDC1755524994",
        "MerchantTradeNo": "SUB5249949B9F9BDC",
        "TotalAmount": "8999",
        "OrderResultURL": "http://localhost:3000/subscription/result",
        "ReturnURL": "http://localhost:8000/api/webhooks/ecpay-auth",
        "ClientBackURL": "http://localhost:3000/billing",
        "PeriodType": "Y",
        "Frequency": "1",
        "PeriodAmount": "8999",
        "ExecTimes": "99",
        "PaymentType": "aio",
        "ChoosePayment": "Credit",
        "TradeDesc": "教練助手訂閱",
        "ItemName": "訂閱方案#1#個#8999",
        "ExpireDate": "7",
        "Remark": "",
        "ChooseSubPayment": "",
        "PlatformID": "",
        "EncryptType": "1",
        "BindingCard": "0",
        "CustomField1": "ENTERPRISE",
        "CustomField2": "annual", 
        "CustomField3": "9B9F9BDC",
        "CustomField4": "",
        "NeedExtraPaidInfo": "N",
        "DeviceSource": "",
        "IgnorePayment": "",
        "Language": "",
    }
    
    # 嘗試不同的時間戳
    time_variations = [
        "2025/08/18 21:52:44",
        "2025/08/18 21:52:45", 
        "2025/08/18 21:52:46",
        "2025/08/18 21:52:47",
        "2025/08/18 21:52:48",
    ]
    
    target_mac = "5DCC55EEA22463E1F51DDF39CD65D0FB21D085A2595849F6B2D5997EAE0D3216"
    hash_key = "pwFHCqoQZGmho4w6"
    hash_iv = "EkRm7iFT261dpevs"
    
    for time_str in time_variations:
        test_params = {**base_params, "MerchantTradeDate": time_str}
        calculated_mac = generate_checkmacvalue_exact(test_params, hash_key, hash_iv)
        
        print(f"⏰ 時間: {time_str}")
        print(f"   CheckMacValue: {calculated_mac}")
        print(f"   匹配: {'✅ 是' if calculated_mac == target_mac else '❌ 否'}")
        print()
        
        if calculated_mac == target_mac:
            print("🎉 找到匹配的參數組合！")
            return test_params

if __name__ == "__main__":
    print("🔍 實際參數分析工具")
    print("=" * 60)
    
    reverse_engineer_from_frontend()
    match_params = try_parameter_variations()
    
    if match_params:
        print(f"✅ 成功匹配的參數組合:")
        for key, value in sorted(match_params.items()):
            print(f"   {key}: '{value}'")