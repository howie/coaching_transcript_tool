#!/usr/bin/env python3
"""
Integration test to discover which language-model combinations are supported
in different Google Speech-to-Text v2 locations.
"""

import json
import base64
import os
import sys
from typing import Dict, List, Tuple
from google.cloud.speech_v2 import SpeechClient, RecognitionConfig, RecognitionFeatures
from google.api_core.client_options import ClientOptions
from google.oauth2 import service_account

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from coaching_assistant.core.config import settings

class STTLanguageModelTester:
    """Test STT language and model support across regions."""
    
    # Languages to test (using BCP-47 format for STT v2)
    TEST_LANGUAGES = [
        "zh-TW",  # Traditional Chinese
        "zh-CN",  # Simplified Chinese  
        "zh",     # Generic Chinese
        "cmn-Hant-TW",  # Traditional Chinese (BCP-47)
        "cmn-Hans-CN",  # Simplified Chinese (BCP-47)
        "en-US",  # English US
        "ja-JP",  # Japanese
        "ko-KR",  # Korean
    ]
    
    # Models to test
    TEST_MODELS = [
        "chirp",
        "chirp_v2",
        "latest_long", 
        "latest_short",
        "long",
        "short",
    ]
    
    # Locations to test
    TEST_LOCATIONS = [
        "us-central1",
        "asia-southeast1", 
        "asia-northeast1",
        "europe-west1",
        "global"
    ]
    
    def __init__(self):
        """Initialize the tester with credentials."""
        self.project_id = settings.GOOGLE_PROJECT_ID
        self._setup_credentials()
        
    def _setup_credentials(self):
        """Setup Google Cloud credentials."""
        if not settings.GOOGLE_APPLICATION_CREDENTIALS_JSON:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON not set")
            
        # Decode credentials
        try:
            decoded_json = base64.b64decode(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON).decode('utf-8')
            self.credentials_info = json.loads(decoded_json)
        except Exception as e:
            # Try as raw JSON
            self.credentials_info = json.loads(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON)
            
        self.credentials = service_account.Credentials.from_service_account_info(
            self.credentials_info
        )
        
    def _get_client_for_location(self, location: str) -> SpeechClient:
        """Get a Speech client for the specified location."""
        if location == "global":
            api_endpoint = "speech.googleapis.com"
        else:
            api_endpoint = f"{location}-speech.googleapis.com"
            
        client_options = ClientOptions(api_endpoint=api_endpoint)
        return SpeechClient(credentials=self.credentials, client_options=client_options)
        
    def test_language_model_support(self, location: str, language: str, model: str) -> Dict:
        """
        Test if a specific language-model combination is supported in a location.
        
        Returns:
            Dict with test result information
        """
        try:
            print(f"Testing: {location} | {language} | {model}")
            
            # Get client for location
            client = self._get_client_for_location(location)
            
            # Create a minimal recognition config to test support
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
            
            # Try to create a recognizer (this will fail if unsupported)
            recognizer_name = f"projects/{self.project_id}/locations/{location}/recognizers/_"
            
            # We don't actually need to process audio, just test the config
            # by attempting to create a request (this will validate the config)
            from google.cloud.speech_v2.types import OutputConfig
            
            request = {
                "recognizer": recognizer_name,
                "config": config,
                "config_mask": None,  # Use all config fields
                "files": [{"uri": "gs://dummy-bucket/dummy-file.wav"}],  # Dummy URI for validation
                "recognition_output_config": OutputConfig(
                    gcs_output_config=None,  # No GCS output needed for testing
                    inline_response_config={}  # Use inline response
                )
            }
            
            # This should fail with audio-related error if config is valid,
            # or with model/language error if invalid
            try:
                # We expect this to fail, but the error type tells us if the config is valid
                client.batch_recognize(request=request)
                result = "✅ SUPPORTED (unexpected success)"
            except Exception as e:
                error_message = str(e).lower()
                
                if "not supported" in error_message and ("model" in error_message or "language" in error_message):
                    result = "❌ NOT SUPPORTED"
                elif "bucket" in error_message or "file" in error_message or "audio" in error_message:
                    result = "✅ SUPPORTED (audio error as expected)"
                elif "permission" in error_message or "access" in error_message:
                    result = "🔒 PERMISSION ERROR"
                else:
                    result = f"❓ UNKNOWN ERROR: {str(e)[:100]}..."
                    
            return {
                "location": location,
                "language": language, 
                "model": model,
                "result": result,
                "success": result.startswith("✅")
            }
            
        except Exception as e:
            return {
                "location": location,
                "language": language,
                "model": model, 
                "result": f"💥 CLIENT ERROR: {str(e)[:100]}...",
                "success": False
            }
            
    def test_all_combinations(self) -> Dict[str, List[Dict]]:
        """Test all language-model combinations across all locations."""
        results = {}
        
        print(f"🧪 Testing STT Language-Model Support")
        print(f"📍 Locations: {', '.join(self.TEST_LOCATIONS)}")
        print(f"🌐 Languages: {', '.join(self.TEST_LANGUAGES)}")  
        print(f"🤖 Models: {', '.join(self.TEST_MODELS)}")
        print(f"🔬 Total combinations: {len(self.TEST_LOCATIONS) * len(self.TEST_LANGUAGES) * len(self.TEST_MODELS)}")
        print("=" * 80)
        
        for location in self.TEST_LOCATIONS:
            print(f"\n📍 Testing location: {location}")
            results[location] = []
            
            for language in self.TEST_LANGUAGES:
                for model in self.TEST_MODELS:
                    result = self.test_language_model_support(location, language, model)
                    results[location].append(result)
                    
                    # Print result immediately
                    status = result["result"]
                    print(f"   {language} + {model:12} → {status}")
                    
        return results
        
    def analyze_results(self, results: Dict[str, List[Dict]]):
        """Analyze and summarize the test results."""
        print("\n" + "=" * 80)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 80)
        
        # Find working combinations for zh-TW
        print(f"\n🎯 Working combinations for Traditional Chinese (zh-TW):")
        zh_tw_working = []
        for location, tests in results.items():
            for test in tests:
                if test["language"] == "zh-TW" and test["success"]:
                    zh_tw_working.append(f"{location} + {test['model']}")
                    print(f"   ✅ {location} + {test['model']}")
        
        if not zh_tw_working:
            print("   ❌ No working combinations found for zh-TW!")
            
        # Summary by location
        print(f"\n📍 Summary by location:")
        for location in self.TEST_LOCATIONS:
            if location in results:
                total = len(results[location])
                supported = sum(1 for r in results[location] if r["success"])
                print(f"   {location:15} → {supported:2}/{total} supported ({supported/total*100:.1f}%)")
        
        # Best models for each language
        print(f"\n🌐 Best models for each language:")
        for language in self.TEST_LANGUAGES:
            working_models = set()
            for location, tests in results.items():
                for test in tests:
                    if test["language"] == language and test["success"]:
                        working_models.add(test["model"])
            
            if working_models:
                print(f"   {language:6} → {', '.join(sorted(working_models))}")
            else:
                print(f"   {language:6} → ❌ No working models found")
                
        return zh_tw_working
        
    def generate_config_recommendations(self, results: Dict[str, List[Dict]]):
        """Generate configuration recommendations based on test results."""
        print(f"\n🔧 CONFIGURATION RECOMMENDATIONS")
        print("=" * 80)
        
        # Find the best model for each language in asia-southeast1
        asia_southeast1_results = results.get("asia-southeast1", [])
        language_model_map = {}
        
        for test in asia_southeast1_results:
            if test["success"]:
                lang = test["language"]
                model = test["model"]
                if lang not in language_model_map:
                    language_model_map[lang] = []
                language_model_map[lang].append(model)
        
        print(f"\nFor asia-southeast1 location, recommended language configs:")
        print("STT_LANGUAGE_CONFIGS='{")
        
        config_entries = []
        for lang, models in language_model_map.items():
            # Prefer chirp, then latest_long, then others
            preferred_order = ["chirp", "latest_long", "latest_short", "long", "short"]
            best_model = None
            for preferred in preferred_order:
                if preferred in models:
                    best_model = preferred
                    break
            if best_model is None and models:
                best_model = models[0]
                
            if best_model:
                config_entries.append(f'  "{lang}": {{"location": "asia-southeast1", "model": "{best_model}"}}')
        
        print(",\n".join(config_entries))
        print("}'")

def main():
    """Run the STT language-model support test."""
    try:
        tester = STTLanguageModelTester()
        results = tester.test_all_combinations()
        working_zh_tw = tester.analyze_results(results)
        tester.generate_config_recommendations(results)
        
        # If we found working combinations for zh-TW, suggest immediate fix
        if working_zh_tw:
            print(f"\n🚀 IMMEDIATE FIX SUGGESTION:")
            print(f"Based on test results, try updating your .env with:")
            best_combo = working_zh_tw[0]  # Use first working combination
            location, model = best_combo.split(" + ")
            print(f'GOOGLE_STT_LOCATION={location}')
            print(f'GOOGLE_STT_MODEL={model}')
            print(f'Or use: STT_LANGUAGE_CONFIGS=\'{{"zh-tw": {{"location": "{location}", "model": "{model}"}}}}\' ')
            
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()