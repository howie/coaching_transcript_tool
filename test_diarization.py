#!/usr/bin/env python3
"""
測試說話者分離功能改善的腳本
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages/core-logic/src'))

from coaching_assistant.core.config import settings
from coaching_assistant.services.google_stt import GoogleSTTProvider

def test_diarization_config():
    """測試說話者分離配置"""
    print("🔍 測試說話者分離配置")
    print(f"ENABLE_SPEAKER_DIARIZATION: {settings.ENABLE_SPEAKER_DIARIZATION}")
    print(f"MAX_SPEAKERS: {settings.MAX_SPEAKERS}")
    print(f"MIN_SPEAKERS: {settings.MIN_SPEAKERS}")
    print(f"GOOGLE_STT_MODEL: {settings.GOOGLE_STT_MODEL}")
    print(f"GOOGLE_STT_LOCATION: {settings.GOOGLE_STT_LOCATION}")
    
def test_optimal_model_selection():
    """測試針對不同語言的最佳模型選擇"""
    print("\n🎯 測試最佳模型選擇")
    
    provider = GoogleSTTProvider()
    
    test_languages = [
        "cmn-Hant-TW",  # 繁體中文
        "en-US",        # 美式英語
        "en-GB",        # 英式英語
        "ja",           # 日語
        "ko",           # 韓語
    ]
    
    for lang in test_languages:
        location, model = provider._get_optimal_location_and_model(lang)
        print(f"  {lang}: location={location}, model={model}")
        
def test_diarization_validation():
    """測試說話者分離支援驗證"""
    print("\n✅ 測試說話者分離支援驗證")
    
    provider = GoogleSTTProvider()
    
    test_cases = [
        ("cmn-hant-tw", "chirp_2", True),       # 不支援 (asia-southeast1)
        ("en-us", "chirp_2", True),             # 檢查是否支援
        ("en-us", "latest_long", True),         # 檢查是否支援
        ("ja", "chirp_2", True),                # 不支援 (asia-southeast1)
    ]
    
    for language, model, enable_diarization in test_cases:
        is_supported = provider._validate_diarization_support(language, model, enable_diarization)
        status = "✅ 支援" if is_supported else "⚠️ 不支援 (會降級到 batch 模式)"
        print(f"  {status}: {language} + {model} in {settings.GOOGLE_STT_LOCATION}")

def test_diarization_fallback():
    """測試說話者分離降級機制"""
    print("\n🔄 測試說話者分離降級機制")
    
    provider = GoogleSTTProvider()
    
    print(f"當前設定: GOOGLE_STT_LOCATION={settings.GOOGLE_STT_LOCATION}")
    print("說明: 如果語言+模型+區域組合不支援說話者分離，系統會自動降級到批次模式")
    
    # 測試不同語言的處理邏輯
    languages = ["cmn-Hant-TW", "en-US", "ja"]
    for lang in languages:
        location, model = provider._get_optimal_location_and_model(lang)
        is_supported = provider._validate_diarization_support(lang, model, True)
        mode = "recognize API (with diarization)" if is_supported else "batchRecognize API (no diarization)"
        print(f"  {lang}: 將使用 {mode}")

if __name__ == "__main__":
    print("🧪 說話者分離功能測試")
    print("=" * 50)
    
    test_diarization_config()
    test_optimal_model_selection()
    test_diarization_validation()
    test_diarization_fallback()
    
    print("\n" + "=" * 50)
    print("✅ 測試完成")