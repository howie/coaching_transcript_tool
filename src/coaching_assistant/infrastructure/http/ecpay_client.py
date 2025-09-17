"""ECPay HTTP client for payment API integration."""

import hashlib
import urllib.parse
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ECPayAPIClient:
    """HTTP client for ECPay API operations following Clean Architecture."""

    def __init__(self, merchant_id: str, hash_key: str, hash_iv: str, environment: str = "sandbox"):
        self.merchant_id = merchant_id
        self.hash_key = hash_key
        self.hash_iv = hash_iv
        self.environment = environment

        # Set API URLs based on environment
        if environment == "sandbox":
            self.credit_detail_url = "https://payment-stage.ecpay.com.tw/CreditDetail/DoAction"
            self.aio_url = "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"
        else:
            self.credit_detail_url = "https://payment.ecpay.com.tw/CreditDetail/DoAction"
            self.aio_url = "https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5"

    def _generate_check_mac_value(self, params: Dict[str, Any]) -> str:
        """Generate ECPay CheckMacValue for API authentication."""
        # Sort parameters by key
        sorted_params = sorted(params.items())

        # Build query string
        query_string = "&".join(f"{key}={value}" for key, value in sorted_params)

        # Add hash key and IV
        raw_string = f"HashKey={self.hash_key}&{query_string}&HashIV={self.hash_iv}"

        # URL encode
        encoded_string = urllib.parse.quote_plus(raw_string, safe="")

        # Convert to lowercase
        encoded_string = encoded_string.lower()

        # Generate MD5 hash
        check_mac_value = hashlib.md5(encoded_string.encode("utf-8")).hexdigest().upper()

        return check_mac_value

    async def cancel_credit_authorization(self, auth_code: str, merchant_trade_no: str) -> Dict[str, Any]:
        """Cancel ECPay credit card authorization."""
        logger.info(f"🔄 Cancelling ECPay authorization: {auth_code}")

        params = {
            "MerchantID": self.merchant_id,
            "MerchantTradeNo": merchant_trade_no,
            "Action": "C",  # Cancel
            "TotalAmount": "0",  # Amount to cancel (0 for full cancellation)
            "TimeStamp": str(int(datetime.now().timestamp()))
        }

        # Generate CheckMacValue
        params["CheckMacValue"] = self._generate_check_mac_value(params)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.credit_detail_url, data=params)
                response.raise_for_status()

                result = response.text
                logger.info(f"✅ ECPay cancel response: {result}")

                # Parse response (ECPay returns 1|OK for success)
                if "1|OK" in result:
                    return {"success": True, "message": "Authorization cancelled successfully"}
                else:
                    return {"success": False, "message": f"Cancel failed: {result}"}

        except httpx.RequestError as e:
            logger.error(f"❌ ECPay cancel request failed: {e}")
            return {"success": False, "message": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ ECPay cancel unexpected error: {e}")
            return {"success": False, "message": f"Unexpected error: {str(e)}"}

    async def retry_payment(self, auth_code: str, merchant_trade_no: str, amount: int) -> Dict[str, Any]:
        """Retry payment for failed ECPay transaction."""
        logger.info(f"🔄 Retrying ECPay payment: {merchant_trade_no}, amount: {amount}")

        params = {
            "MerchantID": self.merchant_id,
            "MerchantTradeNo": merchant_trade_no,
            "Action": "R",  # Retry
            "TotalAmount": str(amount),
            "TimeStamp": str(int(datetime.now().timestamp()))
        }

        # Generate CheckMacValue
        params["CheckMacValue"] = self._generate_check_mac_value(params)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.credit_detail_url, data=params)
                response.raise_for_status()

                result = response.text
                logger.info(f"✅ ECPay retry response: {result}")

                # Parse response (ECPay returns 1|OK for success)
                if "1|OK" in result:
                    return {"success": True, "message": "Payment retry successful"}
                else:
                    return {"success": False, "message": f"Retry failed: {result}"}

        except httpx.RequestError as e:
            logger.error(f"❌ ECPay retry request failed: {e}")
            return {"success": False, "message": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ ECPay retry unexpected error: {e}")
            return {"success": False, "message": f"Unexpected error: {str(e)}"}

    async def process_payment(self, merchant_trade_no: str, amount: int, item_name: str) -> Dict[str, Any]:
        """Process new payment via ECPay."""
        logger.info(f"💳 Processing ECPay payment: {merchant_trade_no}, amount: {amount}")

        params = {
            "MerchantID": self.merchant_id,
            "MerchantTradeNo": merchant_trade_no,
            "MerchantTradeDate": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "PaymentType": "aio",
            "TotalAmount": str(amount),
            "TradeDesc": "Subscription Payment",
            "ItemName": item_name,
            "ReturnURL": "https://your-domain.com/ecpay/callback",
            "ChoosePayment": "Credit",
            "EncryptType": "1"
        }

        # Generate CheckMacValue
        params["CheckMacValue"] = self._generate_check_mac_value(params)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.aio_url, data=params)
                response.raise_for_status()

                result = response.text
                logger.info(f"✅ ECPay payment response received")

                return {"success": True, "response": result, "payment_url": self.aio_url}

        except httpx.RequestError as e:
            logger.error(f"❌ ECPay payment request failed: {e}")
            return {"success": False, "message": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ ECPay payment unexpected error: {e}")
            return {"success": False, "message": f"Unexpected error: {str(e)}"}

    def calculate_refund_amount(self, original_amount: int, days_used: int, total_days: int) -> int:
        """Calculate prorated refund amount."""
        if days_used >= total_days:
            return 0

        days_remaining = total_days - days_used
        refund_ratio = days_remaining / total_days
        refund_amount = int(original_amount * refund_ratio)

        logger.info(f"💰 Refund calculation: {days_remaining}/{total_days} days = ${refund_amount}")
        return refund_amount