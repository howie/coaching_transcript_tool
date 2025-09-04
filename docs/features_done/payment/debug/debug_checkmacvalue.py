#!/usr/bin/env python3
"""
Debug script to identify CheckMacValue calculation issues
"""

import sys
import hashlib
import urllib.parse
from datetime import datetime

sys.path.insert(0, 'src')

def debug_checkmacvalue_step_by_step():
    """逐步除錯 CheckMacValue 計算過程"""
    
    print("🔍 CheckMacValue 計算逐步除錯")
    print("=" * 60)
    
    # 模擬實際參數 (基於用戶提供的資訊)
    sample_data = {
        "MerchantID": "3002607",
        "MerchantMemberID": "USER9B9F9BDC1755523767",
        "MerchantTradeNo": "SUB5237679B9F9BDC",
        "TotalAmount": "899",
        "OrderResultURL": "http://localhost:3000/subscription/result",
        "ReturnURL": "http://localhost:8000/api/webhooks/ecpay-auth",
        "ClientBackURL": "http://localhost:3000/billing",
        "PeriodType": "M",
        "Frequency": "1", 
        "PeriodAmount": "899",
        "ExecTimes": "999",
        "PaymentType": "aio",
        "ChoosePayment": "Credit",
        "TradeDesc": "教練助手訂閱",
        "ItemName": "訂閱方案#1#個#899",
        "MerchantTradeDate": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "ExpireDate": "7",
        "Remark": "",
        "ChooseSubPayment": "",
        "PlatformID": "",
        "EncryptType": "1",
        "BindingCard": "0",
        "CustomField1": "PRO",
        "CustomField2": "monthly", 
        "CustomField3": "9B9F9BDC",
        "CustomField4": "",
        "NeedExtraPaidInfo": "N",
        "DeviceSource": "",
        "IgnorePayment": "",
        "Language": "",
    }
    
    # ECPay 測試環境設定
    hash_key = "pwFHCqoQZGmho4w6"
    hash_iv = "EkRm7iFT261dpevs"
    
    print("1. 原始參數:")
    for key, value in sorted(sample_data.items()):
        print(f"   {key}: '{value}'")
    
    print("\n2. 排序後參數:")
    sorted_data = sorted(sample_data.items())
    for key, value in sorted_data:
        print(f"   {key}={value}")
    
    print("\n3. URL 編碼參數:")
    encoded_params = []
    for key, value in sorted_data:
        encoded_value = urllib.parse.quote_plus(str(value))
        encoded_params.append(f"{key}={encoded_value}")
        print(f"   {key}={encoded_value}")
    
    print("\n4. Query String:")
    query_string = "&".join(encoded_params)
    print(f"   {query_string}")
    
    print("\n5. 加入 HashKey 和 HashIV:")
    raw_string = f"HashKey={hash_key}&{query_string}&HashIV={hash_iv}"
    print(f"   {raw_string}")
    
    print("\n6. URL 編碼整個字串:")
    encoded_string = urllib.parse.quote_plus(raw_string).lower()
    print(f"   {encoded_string}")
    
    print("\n7. SHA256 計算:")
    final_hash = hashlib.sha256(encoded_string.encode('utf-8')).hexdigest().upper()
    print(f"   {final_hash}")
    
    print("\n" + "=" * 60)
    print(f"✅ 最終 CheckMacValue: {final_hash}")
    
    return final_hash

def test_problematic_characters():
    """測試可能有問題的字元"""
    
    print("\n🔍 測試可能有問題的字元")
    print("=" * 60)
    
    test_strings = [
        "教練助手訂閱",  # 中文
        "訂閱方案#1#個#899",  # 含 # 符號
        "http://localhost:3000/subscription/result",  # URL
        "",  # 空字串
        "N",  # 單字元
    ]
    
    for test_str in test_strings:
        encoded = urllib.parse.quote_plus(test_str)
        print(f"   '{test_str}' -> '{encoded}'")
        
        # 檢查是否有可能的編碼問題
        if test_str != encoded:
            print(f"     ⚠️  編碼改變了內容")

if __name__ == "__main__":
    calculated_mac = debug_checkmacvalue_step_by_step()
    test_problematic_characters()
    
    print(f"\n🎯 建議:")
    print("1. 在前端 console 檢查實際提交的參數")
    print("2. 比較前端提交的 CheckMacValue 與後端計算的值")
    print("3. 檢查是否有隱藏字元或編碼問題")
    print("4. 驗證中文字元和特殊符號處理")