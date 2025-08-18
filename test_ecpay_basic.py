#!/usr/bin/env python3
"""
ECPay 基本連線測試
"""

import hashlib
import urllib.parse
from datetime import datetime
import requests

# ECPay 測試商店資訊
MERCHANT_ID = "3002607"
HASH_KEY = "pwFHCqoQZGmho4w6"
HASH_IV = "EkRm7iFT261dpevs"

def create_simple_test_order():
    """建立最簡單的測試訂單"""
    
    print("🧪 建立 ECPay 最簡單測試訂單")
    print("=" * 60)
    
    # 最基本的參數組合
    basic_params = {
        "MerchantID": MERCHANT_ID,
        "MerchantTradeNo": "TEST" + str(int(datetime.now().timestamp()))[-10:],
        "MerchantTradeDate": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "PaymentType": "aio",
        "TotalAmount": "100",  # 最小金額測試
        "TradeDesc": "Test Order",
        "ItemName": "Test Item",
        "ReturnURL": "https://httpbin.org/post",  # 公開測試 URL
        "ChoosePayment": "Credit",
        "EncryptType": "1",
    }
    
    print("📋 基本參數:")
    for key, value in sorted(basic_params.items()):
        print(f"   {key}: '{value}'")
    
    # 計算 CheckMacValue
    mac_value = generate_check_mac_value(basic_params, HASH_KEY, HASH_IV)
    basic_params["CheckMacValue"] = mac_value
    
    print(f"\n🔐 CheckMacValue: {mac_value}")
    
    return basic_params

def generate_check_mac_value(data, hash_key, hash_iv):
    """標準 CheckMacValue 計算"""
    
    # 移除 CheckMacValue
    filtered_data = {k: v for k, v in data.items() if k != "CheckMacValue"}
    
    # 按 ASCII 排序
    sorted_items = sorted(filtered_data.items())
    
    # URL 編碼
    encoded_params = []
    for key, value in sorted_items:
        encoded_value = urllib.parse.quote_plus(str(value), encoding='utf-8')
        encoded_params.append(f"{key}={encoded_value}")
    
    # 組成查詢字串
    query_string = "&".join(encoded_params)
    
    # 加入 HashKey 和 HashIV
    raw_string = f"HashKey={hash_key}&{query_string}&HashIV={hash_iv}"
    
    # URL 編碼並轉小寫
    encoded_string = urllib.parse.quote_plus(raw_string, encoding='utf-8').lower()
    
    # SHA256
    return hashlib.sha256(encoded_string.encode('utf-8')).hexdigest().upper()

def test_ecpay_connectivity():
    """測試 ECPay 連線"""
    
    print("\n🌐 測試 ECPay 連線")
    print("=" * 60)
    
    test_url = "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"
    
    try:
        # 簡單的連線測試
        response = requests.get(test_url, timeout=10)
        print(f"✅ ECPay 測試環境可連接")
        print(f"   狀態碼: {response.status_code}")
        print(f"   回應長度: {len(response.content)} bytes")
        
        if response.status_code == 200:
            return True
        else:
            print(f"❌ 非預期狀態碼: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ 連線失敗: {e}")
        return False

def analyze_error_possibilities():
    """分析可能的錯誤原因"""
    
    print("\n🔍 CheckMacValue 錯誤可能原因分析")
    print("=" * 60)
    
    possibilities = [
        {
            "原因": "商店未開啟收款服務",
            "說明": "ECPay 測試商店 3002607 可能未啟用",
            "檢查方法": "聯繫 ECPay 確認測試商店狀態",
            "可能性": "高"
        },
        {
            "原因": "Hash Key/IV 不正確",
            "說明": "測試環境的 Hash Key 或 IV 可能已更改",
            "檢查方法": "確認 ECPay 文檔中的最新測試憑證",
            "可能性": "中"
        },
        {
            "原因": "交易金額限制",
            "說明": "8999 元可能超過測試商店限制",
            "檢查方法": "嘗試更小的金額 (如 100 元)",
            "可能性": "中"
        },
        {
            "原因": "參數格式差異",
            "說明": "前後端計算 CheckMacValue 的方式不同",
            "檢查方法": "逐步比對參數值和編碼方式",
            "可能性": "低"
        },
        {
            "原因": "網路限制",
            "說明": "localhost 回調 URL 在 ECPay 測試環境可能被阻擋",
            "檢查方法": "使用 ngrok 或公開 URL",
            "可能性": "低"
        }
    ]
    
    for i, possibility in enumerate(possibilities, 1):
        print(f"{i}. {possibility['原因']} (可能性: {possibility['可能性']})")
        print(f"   說明: {possibility['說明']}")
        print(f"   檢查: {possibility['檢查方法']}")
        print()

def recommended_solutions():
    """建議的解決方案"""
    
    print("💡 建議解決方案")
    print("=" * 60)
    
    solutions = [
        {
            "步驟": 1,
            "行動": "驗證 ECPay 測試商店狀態",
            "說明": "聯繫 ECPay 技術支援確認測試商店 3002607 是否正常運作",
            "優先級": "最高"
        },
        {
            "步驟": 2,
            "行動": "測試小額交易",
            "說明": "先用 100 元測試，確保不是金額限制問題",
            "優先級": "高"
        },
        {
            "步驟": 3,
            "行動": "使用 ECPay 官方工具",
            "說明": "使用 ECPay 提供的參數檢測工具驗證 CheckMacValue",
            "優先級": "高"
        },
        {
            "步驟": 4,
            "行動": "設定公開回調 URL",
            "說明": "使用 ngrok 將本地服務暴露給 ECPay",
            "優先級": "中"
        },
        {
            "步驟": 5,
            "行動": "重新檢查官方文檔",
            "說明": "確認 Hash Key/IV 和 API 端點是否有更新",
            "優先級": "中"
        }
    ]
    
    for solution in solutions:
        print(f"步驟 {solution['步驟']} - {solution['行動']} (優先級: {solution['優先級']})")
        print(f"   {solution['說明']}")
        print()

if __name__ == "__main__":
    print("🔧 ECPay 基本診斷工具")
    print("=" * 60)
    
    # 1. 測試連線
    connectivity_ok = test_ecpay_connectivity()
    
    # 2. 建立簡單測試訂單
    if connectivity_ok:
        test_params = create_simple_test_order()
        
        print("\n📤 可以嘗試用這些參數手動測試:")
        print("   前往: https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5")
        print("   使用 POST 方法提交以下參數:")
        for key, value in test_params.items():
            print(f"   {key}={value}")
    
    # 3. 分析錯誤可能性
    analyze_error_possibilities()
    
    # 4. 提供解決方案
    recommended_solutions()
    
    print("\n🎯 總結:")
    print("CheckMacValue 錯誤最可能的原因是測試商店狀態問題。")
    print("建議先確認 ECPay 測試商店 3002607 是否仍然可用。")