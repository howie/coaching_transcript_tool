#!/usr/bin/env python3
"""
CheckMacValue 驗證和問題診斷工具
"""

import hashlib
import sys
import urllib.parse
from datetime import datetime

sys.path.insert(0, "src")

# ECPay 測試環境設定
ECPAY_MERCHANT_ID = "3002607"
ECPAY_HASH_KEY = "pwFHCqoQZGmho4w6"
ECPAY_HASH_IV = "EkRm7iFT261dpevs"
ECPAY_TEST_URL = "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"


def generate_checkmacvalue(data, hash_key, hash_iv):
    """生成 CheckMacValue - 完全按照 ECPay 規範"""

    # 移除 CheckMacValue 欄位
    filtered_data = {k: v for k, v in data.items() if k != "CheckMacValue"}

    # 按照 ASCII 排序
    sorted_items = sorted(filtered_data.items())

    # URL 編碼每個值
    encoded_params = []
    for key, value in sorted_items:
        # 確保值為字串並進行 URL 編碼
        str_value = str(value) if value is not None else ""
        encoded_value = urllib.parse.quote_plus(str_value, safe="", encoding="utf-8")
        encoded_params.append(f"{key}={encoded_value}")

    # 組成查詢字串
    query_string = "&".join(encoded_params)

    # 前後加上 HashKey 和 HashIV
    raw_string = f"HashKey={hash_key}&{query_string}&HashIV={hash_iv}"

    print("🔍 Raw string for hashing:")
    print(f"   {raw_string}")
    print(f"   Length: {len(raw_string)}")

    # URL 編碼整個字串並轉小寫
    encoded_string = urllib.parse.quote_plus(
        raw_string, safe="", encoding="utf-8"
    ).lower()

    print("\n🔍 Encoded string:")
    print(f"   {encoded_string}")
    print(f"   Length: {len(encoded_string)}")

    # 計算 SHA256
    hash_bytes = encoded_string.encode("utf-8")
    sha256_hash = hashlib.sha256(hash_bytes).hexdigest().upper()

    return sha256_hash


def validate_ecpay_parameters():
    """驗證 ECPay 參數設定"""

    print("🔍 ECPay 參數驗證")
    print("=" * 60)

    # 基本參數檢查
    print("1. 基本參數檢查:")
    print(f"   商店代號: {ECPAY_MERCHANT_ID}")
    print(f"   HashKey: {ECPAY_HASH_KEY}")
    print(f"   HashIV: {ECPAY_HASH_IV}")
    print(f"   測試網址: {ECPAY_TEST_URL}")

    # 模擬實際的參數組合
    test_params = {
        "MerchantID": ECPAY_MERCHANT_ID,
        "MerchantMemberID": "USER9B9F9BDC1755524994",
        "MerchantTradeNo": "SUB5249949B9F9BDC",
        "TotalAmount": "8999",
        "OrderResultURL": "http://localhost:3000/subscription/result",
        "ReturnURL": "http://localhost:8000/api/webhooks/ecpay-auth",
        "ClientBackURL": "http://localhost:3000/billing",
        "PeriodType": "Y",  # 年繳測試
        "Frequency": "1",
        "PeriodAmount": "8999",
        "ExecTimes": "99",
        "PaymentType": "aio",
        "ChoosePayment": "Credit",
        "TradeDesc": "教練助手訂閱",
        "ItemName": "訂閱方案#1#個#8999",
        "MerchantTradeDate": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
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

    print("\n2. 參數內容驗證:")
    for key, value in sorted(test_params.items()):
        value_type = type(value).__name__
        value_len = len(str(value)) if value is not None else 0
        print(f"   {key:<20}: '{value}' ({value_type}, len={value_len})")

    # 生成 CheckMacValue
    print("\n3. CheckMacValue 計算過程:")
    calculated_mac = generate_checkmacvalue(test_params, ECPAY_HASH_KEY, ECPAY_HASH_IV)

    print(f"\n✅ 計算出的 CheckMacValue: {calculated_mac}")

    return test_params, calculated_mac


def test_different_scenarios():
    """測試不同情境的參數組合"""

    print("\n🧪 不同情境測試")
    print("=" * 60)

    scenarios = [
        {
            "name": "月繳 PRO 方案",
            "params": {
                "TotalAmount": "899",
                "PeriodAmount": "899",
                "PeriodType": "M",
                "ExecTimes": "999",
                "CustomField1": "PRO",
                "CustomField2": "monthly",
                "ItemName": "訂閱方案#1#個#899",
            },
        },
        {
            "name": "年繳 ENTERPRISE 方案",
            "params": {
                "TotalAmount": "8999",
                "PeriodAmount": "8999",
                "PeriodType": "Y",
                "ExecTimes": "99",
                "CustomField1": "ENTERPRISE",
                "CustomField2": "annual",
                "ItemName": "訂閱方案#1#個#8999",
            },
        },
    ]

    base_params = {
        "MerchantID": ECPAY_MERCHANT_ID,
        "MerchantMemberID": "USER9B9F9BDC1755524994",
        "MerchantTradeNo": "SUB5249949B9F9BDC",
        "OrderResultURL": "http://localhost:3000/subscription/result",
        "ReturnURL": "http://localhost:8000/api/webhooks/ecpay-auth",
        "ClientBackURL": "http://localhost:3000/billing",
        "PaymentType": "aio",
        "ChoosePayment": "Credit",
        "TradeDesc": "教練助手訂閱",
        "MerchantTradeDate": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "ExpireDate": "7",
        "Frequency": "1",
        "Remark": "",
        "ChooseSubPayment": "",
        "PlatformID": "",
        "EncryptType": "1",
        "BindingCard": "0",
        "CustomField3": "9B9F9BDC",
        "CustomField4": "",
        "NeedExtraPaidInfo": "N",
        "DeviceSource": "",
        "IgnorePayment": "",
        "Language": "",
    }

    for scenario in scenarios:
        print(f"\n📋 {scenario['name']}:")

        # 合併參數
        test_params = {**base_params, **scenario["params"]}

        # 計算 CheckMacValue
        mac_value = generate_checkmacvalue(test_params, ECPAY_HASH_KEY, ECPAY_HASH_IV)

        print(f"   CheckMacValue: {mac_value}")
        print("   關鍵參數:")
        for key in ["TotalAmount", "PeriodType", "ExecTimes", "CustomField1"]:
            print(f"     {key}: '{test_params[key]}'")


def check_common_issues():
    """檢查常見問題"""

    print("\n🚨 常見問題檢查")
    print("=" * 60)

    issues = [
        {
            "問題": "交易金額格式",
            "檢查": "確保 TotalAmount 和 PeriodAmount 都是字串格式",
            "正確": "899 (字串)",
            "錯誤": "899 (數字) 或 8.99 (小數)",
        },
        {
            "問題": "中文字元編碼",
            "檢查": "TradeDesc 和 ItemName 的 UTF-8 編碼",
            "正確": "教練助手訂閱 -> %E6%95%99%E7%B7%B4%E5%8A%A9%E6%89%8B%E8%A8%82%E9%96%B1",
            "錯誤": "編碼不一致或使用錯誤的編碼方式",
        },
        {
            "問題": "URL 編碼一致性",
            "檢查": "前後端 URL 編碼方式必須一致",
            "正確": "使用 urllib.parse.quote_plus()",
            "錯誤": "使用不同的編碼函數",
        },
        {
            "問題": "參數排序",
            "檢查": "參數必須按照 ASCII 順序排序",
            "正確": "BindingCard, ChoosePayment, CustomField1...",
            "錯誤": "任何其他順序",
        },
        {
            "問題": "空值處理",
            "檢查": "空值應該轉換為空字串",
            "正確": "'' (空字串)",
            "錯誤": "None, null, undefined",
        },
    ]

    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue['問題']}:")
        print(f"   檢查內容: {issue['檢查']}")
        print(f"   ✅ 正確: {issue['正確']}")
        print(f"   ❌ 錯誤: {issue['錯誤']}")
        print()


if __name__ == "__main__":
    print("🔍 ECPay CheckMacValue 深度診斷工具")
    print("=" * 60)

    # 執行所有檢查
    validate_ecpay_parameters()
    test_different_scenarios()
    check_common_issues()

    print("\n🎯 診斷結果建議:")
    print("1. 檢查前端實際提交的參數是否與後端計算完全一致")
    print("2. 驗證 ECPay 測試商店設定是否正確")
    print("3. 確認交易金額符合 ECPay 限制")
    print("4. 檢查網路連線和防火牆設定")
    print("5. 嘗試使用 ECPay 官方測試工具驗證參數")
