#!/usr/bin/env python3
"""
Test Speech-to-Text v1 API support for zh-TW
"""

import json
import base64
import os
import sys
from google.cloud import speech_v1
from google.api_core.client_options import ClientOptions
from google.oauth2 import service_account

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from coaching_assistant.core.config import settings

def test_stt_v1_zh_tw():
    """Test Speech-to-Text v1 API support for zh-TW."""
    
    print("🧪 Testing Speech-to-Text v1 API for zh-TW")
    print("=" * 50)
    
    # Setup credentials
    if not settings.GOOGLE_APPLICATION_CREDENTIALS_JSON:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON not set")
        return
        
    try:
        decoded_json = base64.b64decode(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON).decode('utf-8')
        credentials_info = json.loads(decoded_json)
    except Exception as e:
        try:
            credentials_info = json.loads(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON)
        except Exception as e2:
            print(f"❌ Failed to decode credentials: {e}, {e2}")
            return
            
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    
    # Test different locations with v1 API
    locations_to_test = ["us-central1", "asia-southeast1", "global"]
    languages_to_test = ["zh-TW", "zh-CN", "cmn-Hant-TW", "cmn-Hans-CN"]
    
    working_combinations = []
    
    for location in locations_to_test:
        print(f"\n📍 Testing location: {location}")
        
        # Create client for location
        if location == "global":
            client = speech_v1.SpeechClient(credentials=credentials)
        else:
            api_endpoint = f"{location}-speech.googleapis.com"
            client_options = ClientOptions(api_endpoint=api_endpoint)
            client = speech_v1.SpeechClient(credentials=credentials, client_options=client_options)
        
        for language in languages_to_test:
            try:
                # Create a minimal recognition config
                config = speech_v1.RecognitionConfig(
                    encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code=language,
                    enable_automatic_punctuation=True,
                    enable_word_time_offsets=True,
                    diarization_config=speech_v1.SpeakerDiarizationConfig(
                        enable_speaker_diarization=True,
                        min_speaker_count=2,
                        max_speaker_count=4,
                    ),
                )
                
                # Create audio config (dummy)
                audio = speech_v1.RecognitionAudio(
                    uri="gs://coaching-audio-dev/dummy.wav"  # Use existing bucket
                )
                
                # Try long running recognize
                try:
                    operation = client.long_running_recognize(
                        config=config,
                        audio=audio
                    )
                    result = "✅ SUPPORTED (operation started)"
                    working_combinations.append(f"{location} + {language}")
                except Exception as e:
                    error_message = str(e).lower()
                    
                    if "language" in error_message and "not supported" in error_message:
                        result = "❌ LANGUAGE NOT SUPPORTED"
                    elif ("file" in error_message or "audio" in error_message or 
                          "bucket" in error_message or "object" in error_message or
                          "no such" in error_message or "not found" in error_message):
                        result = "✅ SUPPORTED (file error as expected)"  
                        working_combinations.append(f"{location} + {language}")
                    elif "permission" in error_message or "access" in error_message:
                        result = "🔒 PERMISSION ERROR"
                    elif "quota" in error_message or "limit" in error_message:
                        result = "📊 QUOTA ERROR (but config valid)"
                        working_combinations.append(f"{location} + {language}")
                    else:
                        result = f"❓ UNKNOWN: {str(e)[:80]}..."
                
                print(f"   {language:15} → {result}")
                
            except Exception as e:
                print(f"   {language:15} → 💥 CLIENT ERROR: {str(e)[:80]}...")
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    if working_combinations:
        print("✅ Working combinations found:")
        for combo in working_combinations:
            print(f"   • {combo}")
            
        # Find best combination for zh-TW
        zh_tw_combos = [c for c in working_combinations if "zh-TW" in c]
        if zh_tw_combos:
            print(f"\n🎯 Recommended for zh-TW:")
            for combo in zh_tw_combos:
                location, language = combo.split(" + ")
                print(f"   🚀 Use location: {location}")
                print(f"   🌐 Language: {language}")
                print(f"   📝 Note: This is Speech-to-Text v1, not v2")
                return True
        
        # If no zh-TW, check zh-CN
        zh_cn_combos = [c for c in working_combinations if "zh-CN" in c]
        if zh_cn_combos:
            print(f"\n🎯 Alternative (Simplified Chinese):")
            for combo in zh_cn_combos[:1]:  # Just show first one
                location, language = combo.split(" + ")
                print(f"   🚀 Use location: {location}")
                print(f"   🌐 Language: {language}")
                print(f"   📝 Note: This is Speech-to-Text v1, not v2")
    else:
        print("❌ No working combinations found!")
        print("   This suggests a fundamental configuration issue.")
    
    return len(working_combinations) > 0

if __name__ == "__main__":
    success = test_stt_v1_zh_tw()
    if success:
        print(f"\n💡 RECOMMENDATION:")
        print(f"Consider switching to Speech-to-Text v1 API for better language support.")
        print(f"You can update SPEECH_API_VERSION=v1 in your .env file.")
    else:
        print("\n💡 NEXT STEPS:")
        print("1. Verify GCP project has Speech-to-Text API enabled")
        print("2. Check service account permissions") 
        print("3. Try with a real audio file to eliminate dummy file issues")