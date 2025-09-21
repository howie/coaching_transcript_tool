#!/usr/bin/env python3
"""
Test Mode API Testing Script
測試模式 API 測試腳本

這個腳本示範如何在測試模式下測試所有主要 API 端點。
This script demonstrates how to test all major API endpoints in test mode.

使用方法 (Usage):
    python test-all-endpoints.py --base-url http://localhost:8000

要求 (Requirements):
    - TEST_MODE=true 環境變數已設定
    - API 伺服器正在運行
    - requests 套件已安裝: pip install requests
"""

import argparse
import json
import sys
import time
from typing import Dict, Any, Optional
import requests
from requests.exceptions import RequestException


class APITester:
    """API 測試器類別"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.test_results = []

    def log(self, message: str, level: str = "INFO"):
        """日誌記錄"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def test_endpoint(self, method: str, endpoint: str,
                     data: Optional[Dict] = None,
                     expected_status: int = 200,
                     description: str = "") -> bool:
        """測試單一端點"""
        url = f"{self.base_url}{endpoint}"

        try:
            self.log(f"測試 {method} {endpoint} - {description}")

            if method.upper() == 'GET':
                response = self.session.get(url, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=self.timeout)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, json=data, timeout=self.timeout)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=self.timeout)
            else:
                self.log(f"不支援的 HTTP 方法: {method}", "ERROR")
                return False

            # 檢查狀態碼
            if response.status_code == expected_status:
                self.log(f"✅ 成功 - 狀態碼: {response.status_code}", "SUCCESS")

                # 嘗試解析 JSON 回應
                try:
                    response_data = response.json()
                    self.log(f"回應資料: {json.dumps(response_data, indent=2, ensure_ascii=False)[:200]}...")
                except json.JSONDecodeError:
                    self.log(f"回應內容: {response.text[:100]}...")

                self.test_results.append({
                    "endpoint": endpoint,
                    "method": method,
                    "status": "PASS",
                    "status_code": response.status_code,
                    "description": description
                })
                return True
            else:
                self.log(f"❌ 失敗 - 預期狀態碼: {expected_status}, 實際: {response.status_code}", "ERROR")
                self.log(f"錯誤回應: {response.text[:200]}", "ERROR")

                self.test_results.append({
                    "endpoint": endpoint,
                    "method": method,
                    "status": "FAIL",
                    "status_code": response.status_code,
                    "description": description,
                    "error": response.text[:200]
                })
                return False

        except RequestException as e:
            self.log(f"❌ 網路錯誤: {str(e)}", "ERROR")
            self.test_results.append({
                "endpoint": endpoint,
                "method": method,
                "status": "ERROR",
                "description": description,
                "error": str(e)
            })
            return False

    def verify_test_mode(self) -> bool:
        """驗證測試模式是否已啟用"""
        self.log("🔍 驗證測試模式是否已啟用...")

        try:
            # 嘗試存取需要認證的端點，無需提供 Authorization header
            response = self.session.get(f"{self.base_url}/api/v1/auth/me", timeout=self.timeout)

            if response.status_code == 200:
                user_data = response.json()
                if user_data.get("email") == "test@example.com":
                    self.log("✅ 測試模式已正確啟用", "SUCCESS")
                    return True
                else:
                    self.log("⚠️  警告: API 可存取但用戶不是測試用戶", "WARNING")
                    return False
            elif response.status_code == 401:
                self.log("❌ 測試模式未啟用 - API 要求認證", "ERROR")
                return False
            else:
                self.log(f"❌ 未預期的回應狀態: {response.status_code}", "ERROR")
                return False

        except RequestException as e:
            self.log(f"❌ 無法連接到 API: {str(e)}", "ERROR")
            return False

    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """執行全面的 API 測試"""
        self.log("🚀 開始執行全面的 API 測試...")

        # 驗證測試模式
        if not self.verify_test_mode():
            self.log("❌ 測試模式驗證失敗，停止測試", "ERROR")
            return {"success": False, "error": "Test mode not enabled"}

        # 測試清單
        tests = [
            # 認證相關 API
            {
                "method": "GET",
                "endpoint": "/api/v1/auth/me",
                "expected_status": 200,
                "description": "獲取當前用戶資訊"
            },

            # 會話管理 API
            {
                "method": "GET",
                "endpoint": "/api/v1/sessions",
                "expected_status": 200,
                "description": "獲取會話列表"
            },
            {
                "method": "POST",
                "endpoint": "/api/v1/sessions",
                "data": {
                    "audio_language": "zh-TW",
                    "stt_provider": "google",
                    "title": "API 測試會話",
                    "description": "自動化測試創建的會話"
                },
                "expected_status": 201,
                "description": "創建新會話"
            },

            # 方案管理 API
            {
                "method": "GET",
                "endpoint": "/api/v1/plans/current",
                "expected_status": 200,
                "description": "獲取當前用戶方案"
            },

            # 使用統計 API
            {
                "method": "GET",
                "endpoint": "/api/v1/usage",
                "expected_status": 200,
                "description": "獲取使用統計"
            },
            {
                "method": "GET",
                "endpoint": "/api/v1/usage/history",
                "expected_status": 200,
                "description": "獲取使用歷史"
            },

            # 健康檢查
            {
                "method": "GET",
                "endpoint": "/health",
                "expected_status": 200,
                "description": "健康檢查端點"
            },
        ]

        # 執行測試
        passed_tests = 0
        total_tests = len(tests)
        created_session_id = None

        for test in tests:
            success = self.test_endpoint(
                method=test["method"],
                endpoint=test["endpoint"],
                data=test.get("data"),
                expected_status=test["expected_status"],
                description=test["description"]
            )

            if success:
                passed_tests += 1

                # 如果是創建會話的測試，保存會話 ID 用於後續測試
                if test["endpoint"] == "/api/v1/sessions" and test["method"] == "POST":
                    try:
                        response = self.session.post(
                            f"{self.base_url}{test['endpoint']}",
                            json=test["data"]
                        )
                        session_data = response.json()
                        created_session_id = session_data.get("id")
                        self.log(f"📝 會話 ID: {created_session_id}")
                    except:
                        pass

            # 短暫延遲避免過載
            time.sleep(0.5)

        # 如果有創建會話，測試會話相關的端點
        if created_session_id:
            session_tests = [
                {
                    "method": "GET",
                    "endpoint": f"/api/v1/sessions/{created_session_id}",
                    "expected_status": 200,
                    "description": "獲取特定會話詳情"
                },
                {
                    "method": "POST",
                    "endpoint": f"/api/v1/sessions/{created_session_id}/upload-url",
                    "data": {
                        "filename": "test-audio.mp3",
                        "content_type": "audio/mpeg"
                    },
                    "expected_status": 200,
                    "description": "獲取音檔上傳 URL"
                },
                {
                    "method": "PATCH",
                    "endpoint": f"/api/v1/sessions/{created_session_id}/speaker-roles",
                    "data": {
                        "speaker_roles": {
                            "speaker_1": "教練",
                            "speaker_2": "客戶"
                        }
                    },
                    "expected_status": 200,
                    "description": "更新說話者角色"
                },
            ]

            for test in session_tests:
                success = self.test_endpoint(
                    method=test["method"],
                    endpoint=test["endpoint"],
                    data=test.get("data"),
                    expected_status=test["expected_status"],
                    description=test["description"]
                )

                if success:
                    passed_tests += 1
                total_tests += 1
                time.sleep(0.5)

        # 生成測試報告
        self.log("📊 生成測試報告...")
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        report = {
            "success": passed_tests == total_tests,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "test_results": self.test_results,
            "created_session_id": created_session_id
        }

        return report

    def print_summary(self, report: Dict[str, Any]):
        """列印測試摘要"""
        print("\n" + "="*60)
        print("🎯 測試摘要 (Test Summary)")
        print("="*60)
        print(f"總測試數: {report['total_tests']}")
        print(f"通過測試: {report['passed_tests']}")
        print(f"失敗測試: {report['failed_tests']}")
        print(f"成功率: {report['success_rate']:.1f}%")

        if report['created_session_id']:
            print(f"創建的會話 ID: {report['created_session_id']}")

        print("\n📋 詳細結果:")
        for result in report['test_results']:
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_icon} {result['method']} {result['endpoint']} - {result['description']}")
            if result['status'] != 'PASS':
                print(f"   錯誤: {result.get('error', 'Unknown error')}")

        print("\n" + "="*60)

        if report['success']:
            print("🎉 所有測試通過！測試模式運作正常。")
        else:
            print("⚠️  部分測試失敗，請檢查 API 服務和配置。")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="Test Mode API Testing Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例用法:
  python test-all-endpoints.py --base-url http://localhost:8000
  python test-all-endpoints.py --base-url http://localhost:8000 --timeout 60
  python test-all-endpoints.py --base-url https://api-dev.example.com

注意:
  - 確保已設定 TEST_MODE=true 環境變數
  - 確保 API 伺服器正在運行
  - 建議在測試環境中執行此腳本
        """
    )

    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API 基礎 URL (預設: http://localhost:8000)"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="請求超時時間（秒）(預設: 30)"
    )

    parser.add_argument(
        "--output-file",
        help="將測試結果保存到檔案（JSON 格式）"
    )

    args = parser.parse_args()

    # 建立測試器
    tester = APITester(args.base_url, args.timeout)

    # 執行測試
    try:
        report = tester.run_comprehensive_tests()

        # 列印摘要
        tester.print_summary(report)

        # 保存結果到檔案（如果指定）
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n💾 測試結果已保存到: {args.output_file}")

        # 根據測試結果設定退出碼
        sys.exit(0 if report['success'] else 1)

    except KeyboardInterrupt:
        print("\n⏹️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試執行時發生錯誤: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()