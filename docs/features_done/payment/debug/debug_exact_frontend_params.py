#!/usr/bin/env python3
"""
使用前端提供的精確參數重新計算 CheckMacValue
"""

import hashlib
import urllib.parse

# 從前端 Console 輸出複製的精確參數
EXACT_FRONTEND_PARAMS = {
    "BindingCard": "0",
    "ChoosePayment": "Credit",
    "ChooseSubPayment": "",
    "ClientBackURL": "http://localhost:3000/billing",
    "CustomField1": "PRO",
    "CustomField2": "annual",
    "CustomField3": "9b9f9bdc",
    "CustomField4": "",
    "DeviceSource": "",
    "EncryptType": "1",
    "ExecTimes": "99",
    "ExpireDate": "7",
    "Frequency": "1",
    "IgnorePayment": "",
    "ItemName": "訂閱方案#1#個#8999",
    "Language": "",
    "MerchantID": "3002607",
    "MerchantMemberID": "USER9B9F9BDC1755601385",
    "MerchantTradeDate": "2025/08/19 19:03:05",
    "MerchantTradeNo": "SUB6013859B9F9BDC",
    "NeedExtraPaidInfo": "N",
    "OrderResultURL": "http://localhost:3000/subscription/result",
    "PaymentType": "aio",
    "PeriodAmount": "8999",
    "PeriodType": "Y",
    "PlatformID": "",
    "Remark": "",
    "ReturnURL": "http://localhost:8000/api/webhooks/ecpay-auth",
    "TotalAmount": "8999",
    "TradeDesc": "教練助手訂閱",
}

# 前端提交的 CheckMacValue
FRONTEND_CHECKMACVALUE = (
    "078E562DD03A770D49212408C786E02E1A6DFA54D357FC6FA6F92C05801FF776"
)

# ECPay 憑證
HASH_KEY = "pwFHCqoQZGmho4w6"
HASH_IV = "EkRm7iFT261dpevs"


def calculate_checkmacvalue_step_by_step(params, hash_key, hash_iv):
    """逐步計算 CheckMacValue"""

    print("🔍 逐步 CheckMacValue 計算")
    print("=" * 60)

    # 步驟 1: 移除 CheckMacValue
    filtered_params = {k: v for k, v in params.items() if k != "CheckMacValue"}
    print(f"步驟 1: 移除 CheckMacValue，剩餘 {len(filtered_params)} 個參數")

    # 步驟 2: 按 ASCII 排序
    sorted_items = sorted(filtered_params.items())
    print("步驟 2: 按 ASCII 排序完成")

    print("\n📋 排序後的參數列表:")
    for i, (key, value) in enumerate(sorted_items, 1):
        print(f"   {i:2d}. {key}: '{value}' (len: {len(str(value))})")

    # 步驟 3: URL 編碼每個值
    print("\n步驟 3: URL 編碼每個參數值")
    encoded_params = []

    for i, (key, value) in enumerate(sorted_items):
        str_value = str(value) if value is not None else ""
        encoded_value = urllib.parse.quote_plus(str_value, encoding="utf-8")
        param_str = f"{key}={encoded_value}"
        encoded_params.append(param_str)

        # 顯示需要編碼的值
        if str_value != encoded_value:
            print(f"   {i + 1:2d}. {key}: '{str_value}' -> '{encoded_value}'")

    # 步驟 4: 組成查詢字串
    query_string = "&".join(encoded_params)
    print("\n步驟 4: 組成查詢字串")
    print(f"   長度: {len(query_string)} 字元")
    print(f"   前 100 字元: {query_string[:100]}...")
    print(f"   後 100 字元: ...{query_string[-100:]}")

    # 步驟 5: 加入 HashKey 和 HashIV
    raw_string = f"HashKey={hash_key}&{query_string}&HashIV={hash_iv}"
    print("\n步驟 5: 加入 HashKey 和 HashIV")
    print(f"   HashKey: {hash_key}")
    print(f"   HashIV: {hash_iv}")
    print(f"   完整字串長度: {len(raw_string)} 字元")

    # 步驟 6: URL 編碼整個字串並轉小寫
    encoded_raw_string = urllib.parse.quote_plus(raw_string, encoding="utf-8").lower()
    print("\n步驟 6: URL 編碼並轉小寫")
    print(f"   編碼後長度: {len(encoded_raw_string)} 字元")
    print(f"   前 100 字元: {encoded_raw_string[:100]}...")
    print(f"   後 100 字元: ...{encoded_raw_string[-100:]}")

    # 步驟 7: SHA256 計算
    calculated_hash = (
        hashlib.sha256(encoded_raw_string.encode("utf-8")).hexdigest().upper()
    )
    print("\n步驟 7: SHA256 計算")
    print(f"   計算結果: {calculated_hash}")

    return calculated_hash


def compare_with_frontend():
    """與前端值進行比較"""

    print("\n🎯 與前端 CheckMacValue 比較")
    print("=" * 60)

    calculated_mac = calculate_checkmacvalue_step_by_step(
        EXACT_FRONTEND_PARAMS, HASH_KEY, HASH_IV
    )

    print("\n📊 CheckMacValue 比較結果:")
    print(f"   前端提交值: {FRONTEND_CHECKMACVALUE}")
    print(f"   我們計算值: {calculated_mac}")
    print(
        f"   是否一致: {'✅ 完全匹配！' if calculated_mac == FRONTEND_CHECKMACVALUE else '❌ 不匹配'}"
    )

    if calculated_mac == FRONTEND_CHECKMACVALUE:
        print("\n🎉 成功！CheckMacValue 計算完全正確")
        print("   這意味著我們的計算邏輯與 ECPay 規範完全一致")
        print("   問題可能出現在其他地方（例如網路、ECPay 測試環境等）")
    else:
        print("\n🚨 CheckMacValue 不匹配")

        # 逐字元比較
        print("\n🔍 逐字元差異分析:")
        for i, (c1, c2) in enumerate(zip(FRONTEND_CHECKMACVALUE, calculated_mac)):
            if c1 != c2:
                print(f"   位置 {i}: 前端='{c1}' vs 計算='{c2}'")
                break
        else:
            print(
                f"   長度差異: 前端={len(FRONTEND_CHECKMACVALUE)}, 計算={len(calculated_mac)}"
            )

    return calculated_mac == FRONTEND_CHECKMACVALUE


def suggest_next_steps(is_matching):
    """建議下一步行動"""

    print("\n💡 建議的下一步行動")
    print("=" * 60)

    if is_matching:
        print("✅ CheckMacValue 計算正確，建議檢查:")
        print("   1. ECPay 測試商店狀態是否正常")
        print("   2. 網路連線是否穩定")
        print("   3. ECPay 測試環境是否有服務問題")
        print("   4. 嘗試聯繫 ECPay 技術支援確認測試商店設定")
        print("   5. 檢查是否有 IP 白名單限制")

        print("\n🔧 可以嘗試的測試:")
        print("   1. 使用 ECPay 官方的參數檢測工具")
        print("   2. 嘗試不同的金額（例如 100 元）")
        print("   3. 使用公開的回調 URL (如 ngrok)")
        print("   4. 檢查 ECPay 官方文檔是否有更新")

    else:
        print("❌ CheckMacValue 計算有問題，需要檢查:")
        print("   1. URL 編碼方式是否正確")
        print("   2. 參數排序是否按 ASCII 順序")
        print("   3. 字串處理是否有遺漏")
        print("   4. HashKey 和 HashIV 是否正確")


def main():
    print("🔧 前端參數精確驗證工具")
    print("=" * 60)

    print(f"📋 驗證參數數量: {len(EXACT_FRONTEND_PARAMS)} 個")
    print(f"🎯 目標 CheckMacValue: {FRONTEND_CHECKMACVALUE}")

    is_matching = compare_with_frontend()
    suggest_next_steps(is_matching)

    return is_matching


if __name__ == "__main__":
    main()
