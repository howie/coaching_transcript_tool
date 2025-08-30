#!/usr/bin/env python3
"""
分析新交易的參數差異
"""

import hashlib
import urllib.parse
import json

# 從最新前端日誌提取的參數
FRONTEND_PARAMS = {
    # 從前端日誌中看到的關鍵參數
    "MerchantTradeNo": "SUB6011469B9F9BDC",
    "TotalAmount": "8999", 
    "TradeDesc": "教練助手訂閱",
    "ItemName": "訂閱方案#1#個#8999",
    "CheckMacValue": "7034111AC7695971EB0071B096BFBAC7601FDB7A4DE622B6BB0B3733263CBFD9",
    
    # 推測的其他必要參數 (基於之前的模式)
    "MerchantID": "3002607",
    "MerchantMemberID": "USER9B9F9BDC1755601146",  # 從後端 response 中看到
    "PaymentType": "aio",
    "ChoosePayment": "Credit", 
    "EncryptType": "1",
    "PeriodType": "Y",  # 年繳
    "Frequency": "1",
    "ExecTimes": "99",
    "PeriodAmount": "8999",
    "ReturnURL": "http://localhost:8000/api/webhooks/ecpay-auth",
    "OrderResultURL": "http://localhost:3000/subscription/result",
    "ClientBackURL": "http://localhost:3000/billing",
    "ExpireDate": "7",
    "BindingCard": "0",
    "NeedExtraPaidInfo": "N",
    
    # 自定義欄位
    "CustomField1": "ENTERPRISE",  # 猜測是企業方案
    "CustomField2": "annual",
    "CustomField3": "9b9f9bdc",  # 用戶 ID 小寫
    
    # 空值欄位
    "Remark": "",
    "ChooseSubPayment": "",
    "PlatformID": "",
    "CustomField4": "",
    "DeviceSource": "",
    "IgnorePayment": "",
    "Language": "",
}

# ECPay 憑證
HASH_KEY = "pwFHCqoQZGmho4w6"
HASH_IV = "EkRm7iFT261dpevs"

def generate_checkmacvalue_with_time_variations():
    """嘗試不同的時間戳找出匹配"""
    
    print("🕐 嘗試不同時間戳找出匹配的 CheckMacValue")
    print("=" * 60)
    
    target_mac = "7034111AC7695971EB0071B096BFBAC7601FDB7A4DE622B6BB0B3733263CBFD9"
    
    # 嘗試可能的時間範圍 (前後30秒)
    import datetime
    now = datetime.datetime.now()
    
    # 生成測試時間列表 (從當前時間前後各30秒)
    test_times = []
    for i in range(-30, 31):
        test_time = now + datetime.timedelta(seconds=i)
        test_times.append(test_time.strftime("%Y/%m/%d %H:%M:%S"))
    
    for test_time in test_times:
        test_params = dict(FRONTEND_PARAMS)
        test_params["MerchantTradeDate"] = test_time
        
        # 移除 CheckMacValue 進行計算
        calc_params = {k: v for k, v in test_params.items() if k != "CheckMacValue"}
        
        # 按 ASCII 排序
        sorted_items = sorted(calc_params.items())
        
        # URL 編碼
        encoded_params = []
        for key, value in sorted_items:
            str_value = str(value) if value is not None else ""
            encoded_value = urllib.parse.quote_plus(str_value, encoding='utf-8')
            encoded_params.append(f"{key}={encoded_value}")
        
        query_string = "&".join(encoded_params)
        raw_string = f"HashKey={HASH_KEY}&{query_string}&HashIV={HASH_IV}"
        encoded_raw_string = urllib.parse.quote_plus(raw_string, encoding='utf-8').lower()
        calculated_mac = hashlib.sha256(encoded_raw_string.encode('utf-8')).hexdigest().upper()
        
        if calculated_mac == target_mac:
            print(f"🎉 找到匹配！時間: {test_time}")
            print(f"   CheckMacValue: {calculated_mac}")
            
            print(f"\n📋 匹配的完整參數:")
            for key in sorted(test_params.keys()):
                if key != "CheckMacValue":
                    print(f"   {key}: '{test_params[key]}'")
            
            return test_params
        
        # 只顯示部分測試結果，避免輸出太多
        if test_time.endswith(":00") or test_time.endswith(":30"):
            print(f"   {test_time}: {calculated_mac[:16]}... {'✅' if calculated_mac == target_mac else '❌'}")
    
    print("❌ 沒有找到匹配的時間戳")
    return None

def try_different_field_combinations():
    """嘗試不同的欄位組合"""
    
    print("\n🔧 嘗試不同欄位組合")
    print("=" * 60)
    
    target_mac = "7034111AC7695971EB0071B096BFBAC7601FDB7A4DE622B6BB0B3733263CBFD9"
    
    # 嘗試不同的 CustomField1 值
    custom_field1_options = ["PRO", "ENTERPRISE", "pro", "enterprise"]
    custom_field3_options = ["9b9f9bdc", "9B9F9BDC"]
    
    # 嘗試當前時間
    current_time = "2025/08/19 13:30:00"  # 大概的時間
    
    for cf1 in custom_field1_options:
        for cf3 in custom_field3_options:
            test_params = dict(FRONTEND_PARAMS)
            test_params["CustomField1"] = cf1
            test_params["CustomField3"] = cf3
            test_params["MerchantTradeDate"] = current_time
            
            # 計算 CheckMacValue
            calc_params = {k: v for k, v in test_params.items() if k != "CheckMacValue"}
            sorted_items = sorted(calc_params.items())
            
            encoded_params = []
            for key, value in sorted_items:
                str_value = str(value) if value is not None else ""
                encoded_value = urllib.parse.quote_plus(str_value, encoding='utf-8')
                encoded_params.append(f"{key}={encoded_value}")
            
            query_string = "&".join(encoded_params)
            raw_string = f"HashKey={HASH_KEY}&{query_string}&HashIV={HASH_IV}"
            encoded_raw_string = urllib.parse.quote_plus(raw_string, encoding='utf-8').lower()
            calculated_mac = hashlib.sha256(encoded_raw_string.encode('utf-8')).hexdigest().upper()
            
            print(f"   CF1='{cf1}', CF3='{cf3}': {calculated_mac[:16]}... {'✅' if calculated_mac == target_mac else '❌'}")
            
            if calculated_mac == target_mac:
                print(f"🎉 找到匹配的欄位組合！")
                print(f"   CustomField1: '{cf1}'")
                print(f"   CustomField3: '{cf3}'") 
                print(f"   MerchantTradeDate: '{current_time}'")
                return test_params

def main():
    print("🔍 新交易參數分析工具")
    print("=" * 60)
    
    print("🎯 目標 CheckMacValue:")
    print("   7034111AC7695971EB0071B096BFBAC7601FDB7A4DE622B6BB0B3733263CBFD9")
    
    # 嘗試時間變化
    time_match = generate_checkmacvalue_with_time_variations()
    
    if not time_match:
        # 嘗試欄位組合
        field_match = try_different_field_combinations()
    
    print(f"\n💡 建議:")
    print("1. 請提供前端 Console 中的完整參數列表")
    print("2. 特別需要確認 MerchantTradeDate 的精確值")
    print("3. 需要確認所有自定義欄位的值")

if __name__ == "__main__":
    main()