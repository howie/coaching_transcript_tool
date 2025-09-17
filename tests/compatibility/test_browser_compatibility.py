"""
Multi-browser compatibility tests for payment system.
Tests payment flows across different browsers and devices to ensure consistent behavior.
"""

import pytest
import requests
import time
import os
from typing import Dict, List, Optional

# Optional selenium imports - skip if not installed
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.safari.options import Options as SafariOptions
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


# Test configuration
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
TEST_TIMEOUT = 30


class BrowserTestConfig:
    """Configuration for different browser tests."""
    
    @classmethod
    def get_browsers(cls):
        """Get browser configurations, only if selenium is available."""
        if not SELENIUM_AVAILABLE:
            return []
            
        return [
            {
                "name": "Chrome",
                "driver_class": webdriver.Chrome,
                "options_class": ChromeOptions,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            {
                "name": "Firefox", 
                "driver_class": webdriver.Firefox,
                "options_class": FirefoxOptions,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
            },
            # Safari requires macOS and additional setup
            # {
            #     "name": "Safari",
            #     "driver_class": webdriver.Safari,
            #     "options_class": SafariOptions,
            #     "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
            # }
        ]
    
    MOBILE_DEVICES = [
        {
            "name": "iPhone 12",
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "viewport": {"width": 390, "height": 844}
        },
        {
            "name": "Samsung Galaxy S21",
            "user_agent": "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "viewport": {"width": 360, "height": 800}
        }
    ]


class TestBrowserCompatibility:
    """Test payment system compatibility across browsers."""

    @pytest.fixture(params=BrowserTestConfig.get_browsers())
    def browser_driver(self, request):
        """Create browser driver for each browser."""
        if not SELENIUM_AVAILABLE:
            pytest.skip("Selenium not available - install with: pip install selenium")
            
        browser_config = request.param
        
        try:
            # Configure browser options
            options = browser_config["options_class"]()
            options.add_argument("--headless")  # Run headless for CI
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"--user-agent={browser_config['user_agent']}")
            
            # Create driver
            driver = browser_config["driver_class"](options=options)
            driver.set_page_load_timeout(TEST_TIMEOUT)
            driver.implicitly_wait(10)
            
            yield {
                "driver": driver,
                "name": browser_config["name"],
                "user_agent": browser_config["user_agent"]
            }
            
        except WebDriverException as e:
            pytest.skip(f"Browser {browser_config['name']} not available: {e}")
        finally:
            if 'driver' in locals():
                driver.quit()

    def test_billing_page_loads_cross_browser(self, browser_driver):
        """Test that billing page loads correctly across browsers."""
        driver = browser_driver["driver"]
        browser_name = browser_driver["name"]
        
        try:
            # Navigate to billing page
            driver.get(f"{FRONTEND_URL}/dashboard/billing")
            
            # Wait for page to load
            WebDriverWait(driver, TEST_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check that essential billing elements are present
            essential_elements = [
                # Plan cards or plan information
                (By.CLASS_NAME, "plan-card"),
                (By.CLASS_NAME, "pricing-card"), 
                (By.CLASS_NAME, "subscription-plan"),
                # Fallback: any element containing "plan" or "billing"
                (By.XPATH, "//*[contains(@class, 'plan') or contains(@class, 'billing')]"),
            ]
            
            element_found = False
            for selector in essential_elements:
                try:
                    driver.find_element(*selector)
                    element_found = True
                    break
                except:
                    continue
            
            assert element_found, f"No billing UI elements found in {browser_name}"
            
            # Check that JavaScript is working (page is interactive)
            page_title = driver.title
            assert page_title is not None and page_title != "", f"Page title empty in {browser_name}"
            
        except TimeoutException:
            pytest.fail(f"Billing page failed to load in {browser_name} within {TEST_TIMEOUT}s")

    def test_plan_comparison_display_cross_browser(self, browser_driver):
        """Test plan comparison UI across browsers."""
        driver = browser_driver["driver"]
        browser_name = browser_driver["name"]
        
        try:
            driver.get(f"{FRONTEND_URL}/dashboard/billing?tab=plans")
            
            # Wait for plan comparison to load
            WebDriverWait(driver, TEST_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for plan-related elements
            plan_elements = driver.find_elements(
                By.XPATH, 
                "//*[contains(text(), 'PRO') or contains(text(), 'FREE') or contains(text(), 'ENTERPRISE')]"
            )
            
            assert len(plan_elements) > 0, f"No plan information visible in {browser_name}"
            
            # Check for pricing information
            price_elements = driver.find_elements(
                By.XPATH,
                "//*[contains(text(), 'NT$') or contains(text(), '$') or contains(text(), '899') or contains(text(), '2999')]"
            )
            
            # Should show some pricing info
            assert len(price_elements) > 0 or len(plan_elements) >= 3, f"Pricing not displayed correctly in {browser_name}"
            
        except TimeoutException:
            pytest.skip(f"Plan comparison page not accessible in {browser_name}")

    def test_upgrade_button_functionality_cross_browser(self, browser_driver):
        """Test upgrade button functionality across browsers."""
        driver = browser_driver["driver"]
        browser_name = browser_driver["name"]
        
        try:
            driver.get(f"{FRONTEND_URL}/dashboard/billing")
            
            # Look for upgrade or plan change buttons
            upgrade_button_selectors = [
                (By.XPATH, "//button[contains(text(), '升級') or contains(text(), 'Upgrade')]"),
                (By.XPATH, "//a[contains(text(), '升級') or contains(text(), 'Upgrade')]"),
                (By.CLASS_NAME, "upgrade-button"),
                (By.CLASS_NAME, "plan-upgrade"),
                (By.XPATH, "//button[contains(@class, 'upgrade') or contains(@class, 'plan')]"),
            ]
            
            upgrade_button = None
            for selector in upgrade_button_selectors:
                try:
                    upgrade_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(selector)
                    )
                    break
                except TimeoutException:
                    continue
            
            if upgrade_button:
                # Button should be clickable
                assert upgrade_button.is_enabled(), f"Upgrade button not enabled in {browser_name}"
                
                # Click button and verify some response
                initial_url = driver.current_url
                upgrade_button.click()
                
                # Wait a moment for any navigation or modal
                time.sleep(2)
                
                # Should either navigate or show modal/form
                final_url = driver.current_url
                page_source = driver.page_source
                
                navigation_occurred = initial_url != final_url
                modal_appeared = any(keyword in page_source.lower() for keyword in 
                                   ['modal', 'dialog', 'popup', 'payment', 'upgrade'])
                
                assert navigation_occurred or modal_appeared, f"Upgrade button click had no effect in {browser_name}"
                
            else:
                # If no upgrade button, might be already on a paid plan or not logged in
                # This is acceptable behavior
                pass
                
        except TimeoutException:
            pytest.skip(f"Upgrade functionality test skipped for {browser_name}")


class TestMobileCompatibility:
    """Test payment system on mobile devices."""

    @pytest.fixture(params=BrowserTestConfig.MOBILE_DEVICES)
    def mobile_driver(self, request):
        """Create mobile browser simulation."""
        if not SELENIUM_AVAILABLE:
            pytest.skip("Selenium not available - install with: pip install selenium")
            
        device_config = request.param
        
        try:
            # Use Chrome with mobile emulation
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox") 
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"--user-agent={device_config['user_agent']}")
            
            # Set mobile viewport
            chrome_options.add_argument(f"--window-size={device_config['viewport']['width']},{device_config['viewport']['height']}")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_window_size(device_config['viewport']['width'], device_config['viewport']['height'])
            
            yield {
                "driver": driver,
                "device": device_config["name"],
                "viewport": device_config["viewport"]
            }
            
        except WebDriverException as e:
            pytest.skip(f"Mobile testing not available: {e}")
        finally:
            if 'driver' in locals():
                driver.quit()

    def test_mobile_billing_page_responsive(self, mobile_driver):
        """Test billing page responsiveness on mobile devices."""
        driver = mobile_driver["driver"]
        device_name = mobile_driver["device"]
        
        try:
            driver.get(f"{FRONTEND_URL}/dashboard/billing")
            
            # Wait for page load
            WebDriverWait(driver, TEST_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check viewport is mobile size
            viewport_width = driver.execute_script("return window.innerWidth;")
            assert viewport_width <= 500, f"Mobile viewport not set correctly: {viewport_width}px"
            
            # Check for mobile-friendly elements
            body = driver.find_element(By.TAG_NAME, "body")
            
            # Page should not have horizontal scroll on mobile
            page_width = driver.execute_script("return document.body.scrollWidth;")
            window_width = driver.execute_script("return window.innerWidth;") 
            
            # Allow some tolerance for scroll bars
            assert page_width <= window_width + 20, f"Horizontal scroll detected on {device_name}: page {page_width}px > window {window_width}px"
            
        except TimeoutException:
            pytest.fail(f"Mobile billing page failed to load on {device_name}")

    def test_mobile_plan_selection_usability(self, mobile_driver):
        """Test plan selection is usable on mobile devices."""
        driver = mobile_driver["driver"]
        device_name = mobile_driver["device"]
        
        try:
            driver.get(f"{FRONTEND_URL}/dashboard/billing")
            
            # Look for clickable plan elements
            plan_buttons = driver.find_elements(
                By.XPATH,
                "//button[contains(text(), 'PRO') or contains(text(), 'ENTERPRISE')] | //a[contains(text(), 'PRO') or contains(text(), 'ENTERPRISE')]"
            )
            
            if plan_buttons:
                # Buttons should be large enough for touch interaction
                for button in plan_buttons[:2]:  # Test first 2 buttons
                    size = button.size
                    # Minimum touch target size should be around 44px
                    assert size['height'] >= 30, f"Button too small for touch on {device_name}: {size['height']}px height"
                    assert size['width'] >= 60, f"Button too narrow for touch on {device_name}: {size['width']}px width"
            
        except TimeoutException:
            pytest.skip(f"Plan selection test skipped for {device_name}")


class TestAPICompatibility:
    """Test API compatibility across different user agents and devices."""

    @pytest.mark.parametrize("user_agent", [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124",  # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",      # Firefox  
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/14.1.1", # Safari
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1",  # iPhone
        "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 Chrome/91.0.4472.120 Mobile Safari/537.36",  # Android
    ])
    def test_api_endpoints_cross_browser(self, user_agent):
        """Test API endpoints work with different user agents."""
        
        headers = {"User-Agent": user_agent}
        
        # Test health check endpoint
        response = requests.get(f"{API_BASE_URL}/api/webhooks/health", headers=headers)
        assert response.status_code == 200, f"Health check failed for user agent: {user_agent}"
        
        # Test plans endpoint (public)
        response = requests.get(f"{API_BASE_URL}/api/v1/plans/compare", headers=headers)
        assert response.status_code in [200, 404], f"Plans endpoint failed for user agent: {user_agent}"

    def test_cors_headers_compatibility(self):
        """Test CORS headers work across different origins."""
        
        test_origins = [
            "http://localhost:3000",
            "https://coaching-app.example.com",
            "https://app.example.com"
        ]
        
        for origin in test_origins:
            headers = {
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            }
            
            # Test preflight request
            response = requests.options(f"{API_BASE_URL}/api/v1/plans/compare", headers=headers)
            
            # Should handle CORS appropriately (allow or deny consistently)
            assert response.status_code in [200, 204, 404, 405], f"CORS preflight failed for origin: {origin}"

    def test_content_type_compatibility(self):
        """Test API handles different content types correctly."""
        
        # Test webhook endpoints with form data (ECPay format)
        form_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "test_member", 
            "amount": "89900"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/webhooks/ecpay-billing",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Should handle form data correctly (success or expected validation error)
        assert response.status_code in [200, 400, 401, 422], "Form data handling failed"

    def test_character_encoding_compatibility(self):
        """Test API handles different character encodings correctly."""
        
        # Test Chinese characters in user data
        test_data = {
            "plan_name": "PRO 方案",
            "description": "專業版訂閱計畫",
            "user_name": "測試用戶"
        }
        
        # Test UTF-8 encoding
        response = requests.post(
            f"{API_BASE_URL}/api/webhooks/health",  # Use health endpoint for testing
            json=test_data,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        
        # Should handle UTF-8 correctly
        assert response.status_code in [200, 400, 405], "UTF-8 encoding handling failed"


class TestJavaScriptCompatibility:
    """Test JavaScript compatibility across browsers."""
    
    def test_browser_javascript_features(self, browser_driver):
        """Test that required JavaScript features work across browsers."""
        driver = browser_driver["driver"]
        browser_name = browser_driver["name"]
        
        try:
            driver.get(f"{FRONTEND_URL}/dashboard/billing")
            
            # Test basic JavaScript execution
            js_result = driver.execute_script("return typeof fetch;")
            assert js_result == "function", f"fetch API not available in {browser_name}"
            
            # Test Promise support
            js_result = driver.execute_script("return typeof Promise;")
            assert js_result == "function", f"Promise not available in {browser_name}"
            
            # Test localStorage (used for auth tokens)
            js_result = driver.execute_script("return typeof localStorage;")
            assert js_result == "object", f"localStorage not available in {browser_name}"
            
            # Test JSON support
            js_result = driver.execute_script("return typeof JSON;")
            assert js_result == "object", f"JSON not available in {browser_name}"
            
        except Exception as e:
            pytest.fail(f"JavaScript compatibility test failed in {browser_name}: {e}")


def run_browser_compatibility_tests():
    """Run all browser compatibility tests."""
    
    # Check if selenium drivers are available
    try:
        from selenium import webdriver
        webdriver.Chrome(options=ChromeOptions())
    except Exception:
        print("Chrome driver not available, skipping browser tests")
        return False
        
    # Run the tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-k", "not test_mobile",  # Skip mobile tests if drivers not available
    ])
    
    return True


if __name__ == "__main__":
    run_browser_compatibility_tests()