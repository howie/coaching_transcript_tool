#!/usr/bin/env python3
"""
精確匹配後端實際生成的參數進行 CheckMacValue 計算
"""

import hashlib
import urllib.parse

# 從後端日誌中提取的精確參數
EXACT_BACKEND_PARAMS = {
    "BindingCard": "0",
    "ChoosePayment": "Credit",
    "ChooseSubPayment": "",
    "ClientBackURL": "http://localhost:3000/billing",
    "CustomField1": "PRO",  # 注意：是 PRO 不是 ENTERPRISE
    "CustomField2": "annual",
    "CustomField3": "9b9f9bdc",  # 注意：是小寫
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
    "MerchantMemberID": "USER9B9F9BDC1755525692",  # 從日誌中的精確值
    "MerchantTradeDate": "2025/08/18 22:01:32",  # 從日誌中的精確時間
    "MerchantTradeNo": "SUB5256929B9F9BDC",  # 從日誌中的精確值
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

# ECPay 憑證
HASH_KEY = "pwFHCqoQZGmho4w6"
HASH_IV = "EkRm7iFT261dpevs"


def generate_checkmacvalue_exact(params, hash_key, hash_iv):
    """精確重現後端的 CheckMacValue 計算"""

    print("🔍 精確後端參數檢查")
    print("=" * 60)

    # 移除 CheckMacValue (如果存在)
    filtered_params = {k: v for k, v in params.items() if k != "CheckMacValue"}

    print("📋 實際後端參數 (按 ASCII 排序):")
    for key in sorted(filtered_params.keys()):
        value = filtered_params[key]
        print(
            f"   {key}: '{value}' (type: {type(value).__name__}, len: {len(str(value))})"
        )

    # 按 ASCII 排序
    sorted_items = sorted(filtered_params.items())

    # URL 編碼每個值
    print("\n🔍 URL 編碼過程:")
    encoded_params = []
    for key, value in sorted_items:
        str_value = str(value) if value is not None else ""
        encoded_value = urllib.parse.quote_plus(str_value, encoding="utf-8")
        encoded_params.append(f"{key}={encoded_value}")

        # 顯示需要編碼的特殊值
        if (
            str_value != encoded_value
            or "教練" in str_value
            or "#" in str_value
            or "http" in str_value
        ):
            print(f"   {key}: '{str_value}' -> '{encoded_value}'")

    # 組成查詢字串
    query_string = "&".join(encoded_params)
    print(f"\n🔍 查詢字串 (長度: {len(query_string)}):")
    print(f"   前 100 字元: {query_string[:100]}...")
    print(f"   後 100 字元: ...{query_string[-100:]}")

    # 加入 HashKey 和 HashIV
    raw_string = f"HashKey={hash_key}&{query_string}&HashIV={hash_iv}"
    print(f"\n🔍 加入 Hash 後 (長度: {len(raw_string)}):")
    print(f"   前 50 字元: {raw_string[:50]}...")
    print(f"   後 50 字元: ...{raw_string[-50:]}")

    # URL 編碼整個字串並轉小寫
    encoded_raw_string = urllib.parse.quote_plus(raw_string, encoding="utf-8").lower()
    print(f"\n🔍 最終編碼字串 (長度: {len(encoded_raw_string)}):")
    print(f"   前 100 字元: {encoded_raw_string[:100]}...")
    print(f"   後 100 字元: ...{encoded_raw_string[-100:]}")

    # SHA256 計算
    calculated_hash = (
        hashlib.sha256(encoded_raw_string.encode("utf-8")).hexdigest().upper()
    )

    return calculated_hash, {
        "query_string": query_string,
        "raw_string": raw_string,
        "encoded_raw_string": encoded_raw_string,
    }


def compare_with_backend_output():
    """與後端實際輸出比較"""

    print("\n🎯 與後端實際輸出比較")
    print("=" * 60)

    # 後端實際計算出的 CheckMacValue
    backend_checkmacvalue = (
        "AA7D90BC9146ED1FC65CD9EC368FF1001673D1C6812F6FCCA467A6AA45DAFE95"
    )

    # 我們重新計算的值
    calculated_mac, details = generate_checkmacvalue_exact(
        EXACT_BACKEND_PARAMS, HASH_KEY, HASH_IV
    )

    print("\n📊 CheckMacValue 比較:")
    print(f"   後端實際計算: {backend_checkmacvalue}")
    print(f"   我們重新計算: {calculated_mac}")
    print(
        f"   是否一致: {'✅ 是' if calculated_mac == backend_checkmacvalue else '❌ 否'}"
    )

    if calculated_mac == backend_checkmacvalue:
        print("\n🎉 成功！我們的計算與後端完全一致")
        print("   問題可能在於前端傳送的參數與後端不一致")
    else:
        print("\n🚨 警告：計算結果不一致")
        print("   需要進一步檢查後端的計算邏輯")

    return calculated_mac == backend_checkmacvalue


def generate_frontend_debug_template():
    """生成前端除錯模板"""

    print("\n💻 前端除錯模板")
    print("=" * 60)

    print("請在前端 console 執行以下代碼來比較參數:")
    print("""
// 1. 列印完整的 form_data 參數
console.log('🔍 前端實際傳送的參數:', JSON.stringify(data.form_data, null, 2));

// 2. 按 ASCII 排序輸出
const sortedParams = Object.keys(data.form_data).sort().reduce((acc, key) => {
    acc[key] = data.form_data[key];
    return acc;
}, {});
console.log('📋 按 ASCII 排序的參數:', JSON.stringify(sortedParams, null, 2));

// 3. 檢查關鍵參數
const keyParams = ['MerchantTradeDate', 'CustomField1', 'CustomField3', 'MerchantMemberID', 'MerchantTradeNo'];
keyParams.forEach(key => {
    console.log(`🔍 ${key}: '${data.form_data[key]}' (type: ${typeof data.form_data[key]}, len: ${String(data.form_data[key]).length})`);
});

// 4. 檢查 CheckMacValue
console.log('🔐 前端 CheckMacValue:', data.form_data.CheckMacValue);
""")

    print("\n📋 期望的後端參數值:")
    for key in [
        "MerchantTradeDate",
        "CustomField1",
        "CustomField3",
        "MerchantMemberID",
        "MerchantTradeNo",
    ]:
        if key in EXACT_BACKEND_PARAMS:
            value = EXACT_BACKEND_PARAMS[key]
            print(f"   {key}: '{value}' (len: {len(str(value))})")


def main():
    print("🔧 精確後端參數 CheckMacValue 驗證工具")
    print("=" * 60)

    # 執行精確比較
    is_consistent = compare_with_backend_output()

    # 生成前端除錯模板
    generate_frontend_debug_template()

    print("\n🎯 總結:")
    if is_consistent:
        print("✅ 後端計算邏輯正確")
        print("❓ 需要檢查前端傳送的參數是否與後端一致")
        print("💡 請使用上面的前端除錯代碼來比較參數差異")
    else:
        print("❌ 後端計算可能有問題")
        print("🔍 需要檢查後端的 CheckMacValue 計算邏輯")

    return is_consistent


if __name__ == "__main__":
    main()
