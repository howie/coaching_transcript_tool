#!/usr/bin/env python3
"""
按照用戶建議系統性檢查 ECPay CheckMacValue 計算
"""

import sys
import hashlib
import urllib.parse
from datetime import datetime
import json

sys.path.insert(0, 'src')

def check_merchant_trade_date_format():
    """檢查 MerchantTradeDate 格式"""
    
    print("🔍 1. MerchantTradeDate 格式檢查")
    print("=" * 60)
    
    # 測試不同格式
    now = datetime.now()
    
    formats_to_test = [
        ("正確格式", now.strftime("%Y/%m/%d %H:%M:%S")),
        ("錯誤-dash", now.strftime("%Y-%m-%d %H:%M:%S")),
        ("錯誤-no-zero", now.strftime("%Y/%m/%d %H:%M:%S").replace(" 0", " ")),
        ("錯誤-T分隔", now.strftime("%Y/%m/%dT%H:%M:%S")),
    ]
    
    for name, format_str in formats_to_test:
        print(f"   {name}: '{format_str}'")
        if name == "正確格式":
            print(f"   ✅ 應使用此格式")
        else:
            print(f"   ❌ 此格式會導致 CheckMacValue 錯誤")
    
    return formats_to_test[0][1]  # 返回正確格式

def check_parameter_order_and_completeness():
    """檢查參數順序和完整性"""
    
    print("\n🔍 2. 參數順序和完整性檢查")
    print("=" * 60)
    
    # ECPay V5 AioCheckOut 必要參數 (根據官方文檔)
    required_params = [
        "MerchantID", "MerchantTradeNo", "MerchantTradeDate", "PaymentType",
        "TotalAmount", "TradeDesc", "ItemName", "ReturnURL", "ChoosePayment", "EncryptType"
    ]
    
    # 定期定額額外必要參數
    recurring_required = [
        "MerchantMemberID", "PeriodType", "Frequency", "ExecTimes", "PeriodAmount"
    ]
    
    # 可選參數（如果提供則必須包含在 CheckMacValue 計算中）
    optional_params = [
        "OrderResultURL", "ClientBackURL", "Remark", "ChooseSubPayment", 
        "PlatformID", "CustomField1", "CustomField2", "CustomField3", "CustomField4",
        "NeedExtraPaidInfo", "DeviceSource", "IgnorePayment", "Language",
        "BindingCard", "ExpireDate"
    ]
    
    print("✅ 必要參數:")
    for param in required_params + recurring_required:
        print(f"   {param}")
    
    print("\n⚠️  可選參數（如果使用必須包含）:")
    for param in optional_params:
        print(f"   {param}")
    
    # 模擬完整參數集
    complete_params = {
        # 必要參數
        "MerchantID": "3002607",
        "MerchantTradeNo": "SUB5249949B9F9BDC",
        "MerchantTradeDate": check_merchant_trade_date_format(),
        "PaymentType": "aio",
        "TotalAmount": "8999",
        "TradeDesc": "教練助手訂閱",
        "ItemName": "訂閱方案#1#個#8999",
        "ReturnURL": "http://localhost:8000/api/webhooks/ecpay-auth",
        "ChoosePayment": "Credit",
        "EncryptType": "1",
        
        # 定期定額參數
        "MerchantMemberID": "USER9B9F9BDC1755524994",
        "PeriodType": "Y",
        "Frequency": "1",
        "ExecTimes": "99",
        "PeriodAmount": "8999",
        
        # 可選參數（我們實際使用的）
        "OrderResultURL": "http://localhost:3000/subscription/result",
        "ClientBackURL": "http://localhost:3000/billing",
        "Remark": "",
        "ChooseSubPayment": "",
        "PlatformID": "",
        "CustomField1": "ENTERPRISE",
        "CustomField2": "annual",
        "CustomField3": "9B9F9BDC",
        "CustomField4": "",
        "NeedExtraPaidInfo": "N",
        "DeviceSource": "",
        "IgnorePayment": "",
        "Language": "",
        "BindingCard": "0",
        "ExpireDate": "7"
    }
    
    print(f"\n📋 完整參數集 (按 ASCII 排序):")
    for key in sorted(complete_params.keys()):
        value = complete_params[key]
        print(f"   {key}: '{value}' (type: {type(value).__name__}, len: {len(str(value))})")
    
    return complete_params

def detailed_checkmacvalue_calculation(params):
    """詳細的 CheckMacValue 計算過程"""
    
    print("\n🔍 3. 詳細 CheckMacValue 計算過程")
    print("=" * 60)
    
    hash_key = "pwFHCqoQZGmho4w6"
    hash_iv = "EkRm7iFT261dpevs"
    
    # 步驟 1: 移除 CheckMacValue
    filtered_params = {k: v for k, v in params.items() if k != "CheckMacValue"}
    print(f"步驟 1: 移除 CheckMacValue，剩餘 {len(filtered_params)} 個參數")
    
    # 步驟 2: ASCII 排序
    sorted_items = sorted(filtered_params.items())
    print(f"步驟 2: 按 ASCII 排序完成")
    
    # 步驟 3: URL 編碼每個值
    print(f"步驟 3: URL 編碼每個參數值")
    encoded_params = []
    for i, (key, value) in enumerate(sorted_items):
        # 確保值為字串
        str_value = str(value) if value is not None else ""
        
        # URL 編碼 - 使用 quote_plus 並指定 UTF-8
        encoded_value = urllib.parse.quote_plus(str_value, encoding='utf-8')
        
        param_str = f"{key}={encoded_value}"
        encoded_params.append(param_str)
        
        # 顯示編碼前後對比（特別關注中文和特殊字元）
        if str_value != encoded_value or '教練' in str_value or '#' in str_value:
            print(f"   {i+1:2d}. {key}: '{str_value}' -> '{encoded_value}'")
    
    # 步驟 4: 組成查詢字串
    query_string = "&".join(encoded_params)
    print(f"\n步驟 4: 組成查詢字串 (長度: {len(query_string)})")
    print(f"   前 100 字元: {query_string[:100]}...")
    print(f"   後 100 字元: ...{query_string[-100:]}")
    
    # 步驟 5: 加入 HashKey 和 HashIV
    raw_string = f"HashKey={hash_key}&{query_string}&HashIV={hash_iv}"
    print(f"\n步驟 5: 加入 HashKey 和 HashIV (總長度: {len(raw_string)})")
    print(f"   HashKey: {hash_key}")
    print(f"   HashIV: {hash_iv}")
    
    # 步驟 6: URL 編碼整個字串並轉小寫
    encoded_raw_string = urllib.parse.quote_plus(raw_string, encoding='utf-8').lower()
    print(f"\n步驟 6: URL 編碼整個字串並轉小寫 (長度: {len(encoded_raw_string)})")
    print(f"   前 100 字元: {encoded_raw_string[:100]}...")
    print(f"   後 100 字元: ...{encoded_raw_string[-100:]}")
    
    # 步驟 7: SHA256 計算
    sha256_hash = hashlib.sha256(encoded_raw_string.encode('utf-8')).hexdigest().upper()
    print(f"\n步驟 7: SHA256 計算")
    print(f"   最終 CheckMacValue: {sha256_hash}")
    
    return {
        'query_string': query_string,
        'raw_string': raw_string,
        'encoded_raw_string': encoded_raw_string,
        'checkmacvalue': sha256_hash
    }

def check_common_pitfalls(params, calculation_result):
    """檢查常見踩雷點"""
    
    print("\n🔍 4. 常見踩雷點檢查")
    print("=" * 60)
    
    issues_found = []
    
    # 檢查 1: MerchantTradeDate 格式
    trade_date = params.get("MerchantTradeDate", "")
    if "/" not in trade_date or "-" in trade_date or "T" in trade_date:
        issues_found.append("❌ MerchantTradeDate 格式錯誤")
    else:
        print("✅ MerchantTradeDate 格式正確")
    
    # 檢查 2: 數值參數是否為字串
    numeric_fields = ["TotalAmount", "PeriodAmount", "ExecTimes", "Frequency", "ExpireDate"]
    for field in numeric_fields:
        if field in params:
            value = params[field]
            if not isinstance(value, str):
                issues_found.append(f"❌ {field} 應為字串格式，目前是 {type(value).__name__}")
            else:
                print(f"✅ {field} 為字串格式: '{value}'")
    
    # 檢查 3: 空值處理
    empty_fields = []
    for key, value in params.items():
        if value == "" or value is None:
            empty_fields.append(key)
    
    if empty_fields:
        print(f"⚠️  空值欄位: {', '.join(empty_fields)}")
        print(f"   空值應該以空字串 '' 的形式包含在計算中")
    
    # 檢查 4: 中文字元 UTF-8 編碼
    chinese_fields = []
    for key, value in params.items():
        str_value = str(value)
        if any('\u4e00' <= char <= '\u9fff' for char in str_value):
            chinese_fields.append((key, str_value))
    
    if chinese_fields:
        print(f"🔤 含中文字元的欄位:")
        for key, value in chinese_fields:
            encoded = urllib.parse.quote_plus(value, encoding='utf-8')
            print(f"   {key}: '{value}' -> '{encoded}'")
    
    # 檢查 5: ItemName 格式
    item_name = params.get("ItemName", "")
    if "#" in item_name:
        parts = item_name.split("#")
        print(f"📦 ItemName 分解:")
        print(f"   原始: '{item_name}'")
        print(f"   分解: {parts}")
        if len(parts) == 4:  # 品名#數量#單位#價格
            print(f"   ✅ 格式正確: 品名#{parts[1]}#{parts[2]}#{parts[3]}")
        else:
            issues_found.append("❌ ItemName 格式可能錯誤")
    
    # 總結
    if issues_found:
        print(f"\n🚨 發現問題:")
        for issue in issues_found:
            print(f"   {issue}")
    else:
        print(f"\n✅ 所有常見踩雷點檢查通過")
    
    return len(issues_found) == 0

def generate_frontend_comparison():
    """生成前端比較用的資料"""
    
    print("\n🔍 5. 前端比較資料生成")
    print("=" * 60)
    
    params = check_parameter_order_and_completeness()
    calculation = detailed_checkmacvalue_calculation(params)
    
    print(f"\n📋 請在前端 console 比較以下資料:")
    
    print(f"\n1. 後端計算的 CheckMacValue:")
    print(f"   {calculation['checkmacvalue']}")
    
    print(f"\n2. 前端實際提交的參數 (請用 JSON.stringify 輸出):")
    frontend_params = dict(params)
    frontend_params['CheckMacValue'] = calculation['checkmacvalue']
    
    # 按照 ASCII 排序輸出
    sorted_frontend = {k: frontend_params[k] for k in sorted(frontend_params.keys())}
    
    print(f"   完整參數 JSON:")
    print(f"   {json.dumps(sorted_frontend, ensure_ascii=False, indent=2)}")
    
    print(f"\n3. 關鍵比較點:")
    critical_fields = ['MerchantTradeDate', 'TotalAmount', 'TradeDesc', 'ItemName', 'CheckMacValue']
    for field in critical_fields:
        if field in params:
            print(f"   {field}: '{params[field] if field != 'CheckMacValue' else calculation['checkmacvalue']}'")
    
    return calculation

if __name__ == "__main__":
    print("🔧 ECPay CheckMacValue 系統性檢查工具")
    print("=" * 60)
    
    # 執行系統性檢查
    correct_date = check_merchant_trade_date_format()
    complete_params = check_parameter_order_and_completeness()
    calculation_result = detailed_checkmacvalue_calculation(complete_params)
    all_checks_passed = check_common_pitfalls(complete_params, calculation_result)
    frontend_data = generate_frontend_comparison()
    
    print(f"\n🎯 總結:")
    print(f"   所有檢查通過: {'✅ 是' if all_checks_passed else '❌ 否'}")
    print(f"   計算的 CheckMacValue: {calculation_result['checkmacvalue']}")
    print(f"   前端目標值: 5DCC55EEA22463E1F51DDF39CD65D0FB21D085A2595849F6B2D5997EAE0D3216")
    print(f"   是否匹配: {'✅ 是' if calculation_result['checkmacvalue'] == '5DCC55EEA22463E1F51DDF39CD65D0FB21D085A2595849F6B2D5997EAE0D3216' else '❌ 否'}")
    
    if calculation_result['checkmacvalue'] != '5DCC55EEA22463E1F51DDF39CD65D0FB21D085A2595849F6B2D5997EAE0D3216':
        print(f"\n💡 下一步建議:")
        print(f"1. 請在前端加入以下 debug 代碼輸出完整參數")
        print(f"2. 確認 MerchantTradeDate 的精確時間")
        print(f"3. 逐個比較每個參數值的完全一致性")