#!/usr/bin/env python3
"""
Quick test to check if us-central1 supports zh-TW with different models.
"""

import json
import base64
import os
import sys
from google.cloud.speech_v2 import SpeechClient, RecognitionConfig, RecognitionFeatures
from google.api_core.client_options import ClientOptions
from google.oauth2 import service_account
# OutputConfig will be imported when needed

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from coaching_assistant.core.config import settings

def test_us_central1_zh_tw():
    """Test if us-central1 supports zh-TW with various models."""
    
    print("🧪 Testing us-central1 support for zh-TW")
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
    
    # Create client for us-central1
    api_endpoint = "us-central1-speech.googleapis.com"
    client_options = ClientOptions(api_endpoint=api_endpoint)
    client = SpeechClient(credentials=credentials, client_options=client_options)
    
    # Test different models
    models_to_test = ["chirp", "latest_long", "latest_short", "long", "short"]
    languages_to_test = ["zh-TW", "zh-CN", "cmn-Hant-TW", "cmn-Hans-CN"]
    
    print(f"📍 Location: us-central1")
    print(f"🌐 Languages: {', '.join(languages_to_test)}")
    print(f"🤖 Models: {', '.join(models_to_test)}")
    print()
    
    working_combinations = []
    
    for language in languages_to_test:
        print(f"Testing language: {language}")
        for model in models_to_test:
            try:
                # Create recognition config
                config = RecognitionConfig(
                    auto_decoding_config={},
                    language_codes=[language],
                    model=model,
                    features=RecognitionFeatures(
                        enable_automatic_punctuation=True,
                        enable_word_time_offsets=True,
                        enable_word_confidence=True
                    )
                )
                
                # Create request (this will validate the config)
                recognizer_name = f"projects/{settings.GOOGLE_PROJECT_ID}/locations/us-central1/recognizers/_"
                request = {
                    "recognizer": recognizer_name,
                    "config": config,
                    "files": [{"uri": "gs://coaching-audio-dev/dummy.wav"}]  # Use existing bucket
                }
                
                # Try the request (expect file error if config is valid)
                try:
                    client.batch_recognize(request=request)
                    result = "✅ SUPPORTED (unexpected success)"
                    working_combinations.append(f"{language} + {model}")
                except Exception as e:
                    error_message = str(e).lower()
                    
                    if "not supported" in error_message and ("model" in error_message or "language" in error_message):
                        result = "❌ NOT SUPPORTED"
                    elif ("file" in error_message or "audio" in error_message or 
                          "bucket" in error_message or "object" in error_message or
                          "no such" in error_message or "not found" in error_message):
                        result = "✅ SUPPORTED (file error as expected)"
                        working_combinations.append(f"{language} + {model}")
                    elif "permission" in error_message or "access" in error_message:
                        result = "🔒 PERMISSION ERROR"
                    elif "output" in error_message:
                        result = "⚙️ OUTPUT CONFIG ISSUE"
                    else:
                        result = f"❓ UNKNOWN: {str(e)[:80]}..."
                
                print(f"   {model:12} → {result}")
                
            except Exception as e:
                print(f"   {model:12} → 💥 CLIENT ERROR: {str(e)[:80]}...")
        
        print()
    
    print("=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    if working_combinations:
        print("✅ Working combinations found:")
        for combo in working_combinations:
            print(f"   • {combo}")
            
        # Find best combination for zh-TW
        zh_tw_combos = [c for c in working_combinations if c.startswith("zh-TW")]
        if zh_tw_combos:
            print(f"\n🎯 Recommended for zh-TW:")
            # Prefer chirp, then latest_long
            for preferred in ["chirp", "latest_long", "latest_short"]:
                for combo in zh_tw_combos:
                    if preferred in combo:
                        lang, model = combo.split(" + ")
                        print(f"   🚀 Use: GOOGLE_STT_MODEL={model}")
                        print(f"   📍 Location: us-central1 (current bucket location)")
                        return True
    else:
        print("❌ No working combinations found!")
        print("   This suggests there might be a fundamental issue with our test approach")
        print("   or Speech-to-Text v2 configuration.")
    
    return len(working_combinations) > 0

if __name__ == "__main__":
    success = test_us_central1_zh_tw()
    if not success:
        print("\n💡 SUGGESTIONS:")
        print("1. Try Speech-to-Text v1 API instead of v2")
        print("2. Check if your GCP project has Speech-to-Text v2 enabled")
        print("3. Verify service account permissions")
        print("4. Test with a minimal example from Google documentation")