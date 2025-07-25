#!/usr/bin/env python3
"""
Test script for the Coaching Transcript Tool API.

This script tests the API endpoints using the requests library.
"""
import sys
import requests
import json
from pathlib import Path

# Base URL of the API (update if running on a different host/port)
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health check endpoint."""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        print(f"✅ Health check passed: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False

def test_format_transcript(vtt_file_path, output_format="markdown"):
    """
    Test the /format endpoint with a VTT file.
    
    Args:
        vtt_file_path: Path to the VTT file to test with
        output_format: Output format (markdown or excel)
    """
    print(f"\nTesting /format endpoint with {vtt_file_path}...")
    
    try:
        with open(vtt_file_path, 'rb') as f:
            files = {'file': (Path(vtt_file_path).name, f, 'text/vtt')}
            params = {
                'output_format': output_format,
                'coach_name': 'John Doe',
                'client_name': 'Jane Smith',
                'convert_to_tc': 'false'
            }
            
            response = requests.post(
                f"{BASE_URL}/format",
                params=params,
                files=files
            )
            
            response.raise_for_status()
            
            # Save the output file
            output_file = f"output.{output_format}"
            with open(output_file, 'wb') as f_out:
                f_out.write(response.content)
                
            print(f"✅ Success! Output saved to {output_file}")
            return True
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return False

def main():
    """Run all tests."""
    if not test_health():
        print("\n⚠️  Health check failed. Is the API server running?")
        print("   Start the server with: uvicorn coaching_transcript_tool.api.app:app --reload")
        sys.exit(1)
    
    # Test with sample VTT files
    test_files = [
        "tests/data/sample_1.vtt",
        "tests/data/sample_2.vtt"
    ]
    
    all_passed = True
    for test_file in test_files:
        for output_format in ["markdown", "excel"]:
            success = test_format_transcript(test_file, output_format)
            all_passed = all_passed and success
    
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
