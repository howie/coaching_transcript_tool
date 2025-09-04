#!/usr/bin/env python3
"""
Payment System Quality Assurance Test Runner
Executes comprehensive testing and quality assurance for the payment system.

Usage:
    python tests/run_payment_qa_tests.py [options]
    
Options:
    --suite [all|e2e|regression|browser|monitoring|webhook]  # Test suite to run
    --verbose                                                # Verbose output
    --report                                                 # Generate test report
    --parallel                                               # Run tests in parallel
    --coverage                                               # Generate coverage report
"""

import os
import sys
import subprocess
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class PaymentQATestRunner:
    """Test runner for payment system quality assurance."""
    
    def __init__(self):
        self.test_suites = {
            "e2e": {
                "name": "End-to-End Tests",
                "files": [
                    "tests/e2e/test_payment_comprehensive_e2e.py",
                    "tests/e2e/test_ecpay_authorization_flow.py", 
                    "tests/e2e/test_plan_upgrade_e2e.py"
                ],
                "description": "Complete payment flow testing from UI to database"
            },
            "regression": {
                "name": "Regression Tests", 
                "files": [
                    "tests/regression/test_payment_error_scenarios.py"
                ],
                "description": "Prevent previously fixed bugs from reoccurring"
            },
            "browser": {
                "name": "Browser Compatibility Tests",
                "files": [
                    "tests/compatibility/test_browser_compatibility.py"
                ],
                "description": "Multi-browser and device compatibility testing"
            },
            "monitoring": {
                "name": "Monitoring & Metrics Tests",
                "files": [
                    "tests/monitoring/test_payment_success_monitoring.py"
                ],
                "description": "Payment success rate and monitoring validation"
            },
            "webhook": {
                "name": "Webhook Retry & Failure Tests",
                "files": [
                    "tests/integration/test_webhook_retry_scenarios.py",
                    "tests/unit/test_enhanced_webhook_processing.py"
                ],
                "description": "Webhook processing, retries, and failure scenarios"
            }
        }
        
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_test_suite(self, suite_name: str, verbose: bool = False, coverage: bool = False) -> Dict:
        """Run a specific test suite."""
        
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")
        
        suite = self.test_suites[suite_name]
        print(f"\n🧪 Running {suite['name']}")
        print(f"📝 {suite['description']}")
        print("=" * 60)
        
        suite_results = {
            "name": suite["name"],
            "files": [],
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "duration": 0
        }
        
        suite_start = time.time()
        
        for test_file in suite["files"]:
            if not os.path.exists(test_file):
                print(f"⚠️  Test file not found: {test_file}")
                continue
                
            print(f"\n📄 Running {test_file}")
            file_result = self._run_pytest_file(test_file, verbose, coverage)
            suite_results["files"].append(file_result)
            
            # Aggregate results
            suite_results["total_tests"] += file_result["total_tests"]
            suite_results["passed"] += file_result["passed"]
            suite_results["failed"] += file_result["failed"] 
            suite_results["skipped"] += file_result["skipped"]
            suite_results["errors"].extend(file_result["errors"])
        
        suite_results["duration"] = time.time() - suite_start
        
        # Print suite summary
        self._print_suite_summary(suite_results)
        
        return suite_results

    def _run_pytest_file(self, test_file: str, verbose: bool = False, coverage: bool = False) -> Dict:
        """Run pytest on a specific file and parse results."""
        
        cmd = ["python", "-m", "pytest", test_file, "--tb=short", "-v" if verbose else "-q"]
        
        if coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])
        
        # Add JSON report for parsing if plugin available
        json_report_file = f"/tmp/pytest_report_{int(time.time())}.json"
        try:
            import pytest_json_report
            cmd.extend(["--json-report", f"--json-report-file={json_report_file}"])
        except ImportError:
            json_report_file = None
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 min timeout
            duration = time.time() - start_time
            
            # Parse JSON report if available
            test_stats = self._parse_pytest_json_report(json_report_file)
            
            file_result = {
                "file": test_file,
                "exit_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "total_tests": test_stats.get("total", 0),
                "passed": test_stats.get("passed", 0),
                "failed": test_stats.get("failed", 0),
                "skipped": test_stats.get("skipped", 0),
                "errors": test_stats.get("errors", [])
            }
            
            # Print result
            status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
            print(f"   {status} - {test_stats.get('total', 0)} tests in {duration:.2f}s")
            
            if result.returncode != 0 and not verbose:
                print(f"   🔍 Use --verbose for detailed error output")
            
            return file_result
            
        except subprocess.TimeoutExpired:
            return {
                "file": test_file,
                "exit_code": -1,
                "duration": 300,
                "stdout": "",
                "stderr": "Test execution timed out",
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": ["Test execution timeout"]
            }
        finally:
            # Cleanup JSON report file
            if json_report_file and os.path.exists(json_report_file):
                os.remove(json_report_file)

    def _parse_pytest_json_report(self, json_file: str) -> Dict:
        """Parse pytest JSON report for test statistics."""
        
        if not json_file or not os.path.exists(json_file):
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": []}
        
        try:
            with open(json_file, 'r') as f:
                report = json.load(f)
            
            summary = report.get("summary", {})
            
            return {
                "total": summary.get("total", 0),
                "passed": summary.get("passed", 0), 
                "failed": summary.get("failed", 0),
                "skipped": summary.get("skipped", 0),
                "errors": [test.get("call", {}).get("longrepr", "") 
                          for test in report.get("tests", []) 
                          if test.get("outcome") == "failed"]
            }
        except (json.JSONDecodeError, KeyError):
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": []}

    def _print_suite_summary(self, suite_results: Dict):
        """Print summary for a test suite."""
        
        print(f"\n📊 {suite_results['name']} Summary")
        print("-" * 40)
        print(f"Total Tests: {suite_results['total_tests']}")
        print(f"✅ Passed:   {suite_results['passed']}")
        print(f"❌ Failed:   {suite_results['failed']}")
        print(f"⏭️  Skipped:  {suite_results['skipped']}")
        print(f"⏱️  Duration: {suite_results['duration']:.2f}s")
        
        if suite_results['failed'] > 0:
            print(f"\n❌ Failures in {suite_results['name']}:")
            for i, error in enumerate(suite_results['errors'][:3], 1):  # Show first 3 errors
                print(f"   {i}. {error[:100]}{'...' if len(error) > 100 else ''}")
            
            if len(suite_results['errors']) > 3:
                print(f"   ... and {len(suite_results['errors']) - 3} more")

    def run_all_suites(self, verbose: bool = False, coverage: bool = False, parallel: bool = False) -> Dict:
        """Run all test suites."""
        
        print("🚀 Starting Payment System Quality Assurance Testing")
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        self.start_time = time.time()
        all_results = {}
        
        if parallel:
            print("🔄 Running test suites in parallel...")
            all_results = self._run_suites_parallel(verbose, coverage)
        else:
            print("📝 Running test suites sequentially...")
            for suite_name in self.test_suites.keys():
                suite_result = self.run_test_suite(suite_name, verbose, coverage)
                all_results[suite_name] = suite_result
        
        self.end_time = time.time()
        self.results = all_results
        
        # Print overall summary
        self._print_overall_summary(all_results)
        
        return all_results

    def _run_suites_parallel(self, verbose: bool, coverage: bool) -> Dict:
        """Run test suites in parallel (simplified implementation)."""
        
        import concurrent.futures
        import threading
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_suite = {
                executor.submit(self.run_test_suite, suite_name, verbose, coverage): suite_name
                for suite_name in self.test_suites.keys()
            }
            
            for future in concurrent.futures.as_completed(future_to_suite):
                suite_name = future_to_suite[future]
                try:
                    result = future.result()
                    results[suite_name] = result
                except Exception as exc:
                    print(f'❌ Suite {suite_name} generated an exception: {exc}')
                    results[suite_name] = {
                        "name": self.test_suites[suite_name]["name"],
                        "error": str(exc),
                        "total_tests": 0,
                        "passed": 0,
                        "failed": 1,
                        "skipped": 0
                    }
        
        return results

    def _print_overall_summary(self, all_results: Dict):
        """Print overall testing summary."""
        
        print("\n" + "=" * 80)
        print("🎯 PAYMENT SYSTEM QA - OVERALL SUMMARY")
        print("=" * 80)
        
        total_tests = sum(result.get("total_tests", 0) for result in all_results.values())
        total_passed = sum(result.get("passed", 0) for result in all_results.values())
        total_failed = sum(result.get("failed", 0) for result in all_results.values())
        total_skipped = sum(result.get("skipped", 0) for result in all_results.values())
        total_duration = self.end_time - self.start_time if self.start_time and self.end_time else 0
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Total Tests:    {total_tests}")
        print(f"✅ Passed:        {total_passed}")
        print(f"❌ Failed:        {total_failed}")
        print(f"⏭️  Skipped:       {total_skipped}")
        print(f"🎯 Success Rate:  {success_rate:.1f}%")
        print(f"⏱️  Total Time:    {total_duration:.2f}s")
        
        # Suite-by-suite results
        print(f"\n📋 Suite Results:")
        for suite_name, result in all_results.items():
            status = "✅ PASS" if result.get("failed", 0) == 0 else "❌ FAIL"
            tests = result.get("total_tests", 0)
            duration = result.get("duration", 0)
            print(f"   {status} {result.get('name', suite_name):30} ({tests:3d} tests, {duration:6.2f}s)")
        
        # Overall status
        overall_status = "✅ ALL TESTS PASSED" if total_failed == 0 else "❌ SOME TESTS FAILED"
        print(f"\n🏆 {overall_status}")
        
        if total_failed > 0:
            print(f"\n⚠️  {total_failed} test(s) failed. Review the output above for details.")
            print("💡 Use --verbose for detailed error information.")
        
        print(f"\n📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def generate_report(self, output_file: str = "payment_qa_report.html"):
        """Generate HTML test report."""
        
        if not self.results:
            print("❌ No test results available. Run tests first.")
            return
        
        html_report = self._generate_html_report()
        
        with open(output_file, 'w') as f:
            f.write(html_report)
        
        print(f"📄 Test report generated: {output_file}")

    def _generate_html_report(self) -> str:
        """Generate HTML report content."""
        
        # Simplified HTML report
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Payment System QA Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .suite {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }}
        .suite-header {{ background: #e9e9e9; padding: 10px; font-weight: bold; }}
        .suite-content {{ padding: 10px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .skipped {{ color: orange; }}
    </style>
</head>
<body>
    <h1>Payment System QA Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: {sum(r.get('total_tests', 0) for r in self.results.values())}</p>
        <p class="passed">Passed: {sum(r.get('passed', 0) for r in self.results.values())}</p>
        <p class="failed">Failed: {sum(r.get('failed', 0) for r in self.results.values())}</p>
        <p class="skipped">Skipped: {sum(r.get('skipped', 0) for r in self.results.values())}</p>
    </div>
    
    <h2>Test Suites</h2>
"""
        
        for suite_name, result in self.results.items():
            status_class = "passed" if result.get("failed", 0) == 0 else "failed"
            html += f"""
    <div class="suite">
        <div class="suite-header {status_class}">
            {result.get('name', suite_name)} - {result.get('total_tests', 0)} tests
        </div>
        <div class="suite-content">
            <p>Duration: {result.get('duration', 0):.2f}s</p>
            <p class="passed">Passed: {result.get('passed', 0)}</p>
            <p class="failed">Failed: {result.get('failed', 0)}</p>
            <p class="skipped">Skipped: {result.get('skipped', 0)}</p>
        </div>
    </div>
"""
        
        html += """
</body>
</html>
"""
        return html


def main():
    """Main entry point for the test runner."""
    
    parser = argparse.ArgumentParser(description="Payment System Quality Assurance Test Runner")
    parser.add_argument("--suite", choices=["all", "e2e", "regression", "browser", "monitoring", "webhook"],
                       default="all", help="Test suite to run")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--report", action="store_true", help="Generate HTML test report")
    parser.add_argument("--parallel", action="store_true", help="Run test suites in parallel") 
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    
    args = parser.parse_args()
    
    runner = PaymentQATestRunner()
    
    try:
        if args.suite == "all":
            results = runner.run_all_suites(args.verbose, args.coverage, args.parallel)
        else:
            results = {args.suite: runner.run_test_suite(args.suite, args.verbose, args.coverage)}
            runner.results = results
        
        if args.report:
            runner.generate_report()
        
        # Exit with appropriate code
        total_failed = sum(r.get("failed", 0) for r in results.values())
        sys.exit(1 if total_failed > 0 else 0)
        
    except KeyboardInterrupt:
        print("\n❌ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()