"""Environment variable validation for application startup."""

import os
import sys
from typing import List, Dict, Tuple
from enum import Enum
import json
import base64


class EnvVarStatus(Enum):
    """Status of environment variable."""

    VALID = "valid"
    MISSING = "missing"
    INVALID = "invalid"
    WARNING = "warning"


class EnvironmentValidator:
    """Validates required environment variables at startup."""

    # Required environment variables and their descriptions
    REQUIRED_VARS = {
        "DATABASE_URL": "PostgreSQL database connection URL",
        "SECRET_KEY": "Secret key for JWT token signing",
        "GOOGLE_PROJECT_ID": "Google Cloud project ID",
        "AUDIO_STORAGE_BUCKET": "Google Cloud Storage bucket for audio files",
        "TRANSCRIPT_STORAGE_BUCKET": "Google Cloud Storage bucket for transcript files",
        "GOOGLE_APPLICATION_CREDENTIALS_JSON": "Google service account credentials (JSON or base64)",
    }

    # Optional but recommended variables
    RECOMMENDED_VARS = {
        "REDIS_URL": "Redis connection URL for Celery (required for transcription)",
        "GOOGLE_CLIENT_ID": "Google OAuth client ID (required for Google login)",
        "GOOGLE_CLIENT_SECRET": "Google OAuth client secret (required for Google login)",
        "RECAPTCHA_SECRET": "reCAPTCHA secret key (recommended for production)",
        "SENTRY_DSN": "Sentry DSN for error tracking (recommended for production)",
    }

    # Variables that should not use default values in production
    PRODUCTION_REQUIRED = {
        "SECRET_KEY": "dev-secret-key",  # Should not use this default
        "RECAPTCHA_SECRET": "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe",  # Test key
    }

    def __init__(self, environment: str = None):
        """Initialize validator with environment."""
        self.environment = environment or os.getenv(
            "ENVIRONMENT", "development"
        )
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def validate_all(self) -> Tuple[bool, Dict[str, str]]:
        """
        Validate all environment variables.

        Returns:
            Tuple of (is_valid, validation_report)
        """
        report = {
            "environment": self.environment,
            "status": "checking",
            "required": {},
            "recommended": {},
            "errors": [],
            "warnings": [],
            "info": [],
        }

        # Check required variables
        print("🔍 Checking required environment variables...")
        for var_name, description in self.REQUIRED_VARS.items():
            value = os.getenv(var_name)

            if not value:
                self.errors.append(f"❌ {var_name}: {description}")
                report["required"][var_name] = "missing"
            else:
                # Validate specific variables
                is_valid, message = self._validate_var_content(var_name, value)
                if is_valid:
                    report["required"][var_name] = "valid"
                    print(f"✅ {var_name}: Found")
                else:
                    self.errors.append(f"❌ {var_name}: {message}")
                    report["required"][var_name] = "invalid"

        # Check recommended variables
        print("\n🔍 Checking recommended environment variables...")
        for var_name, description in self.RECOMMENDED_VARS.items():
            value = os.getenv(var_name)

            if not value:
                self.warnings.append(f"⚠️  {var_name}: {description}")
                report["recommended"][var_name] = "missing"
                print(f"⚠️  {var_name}: Not configured ({description})")
            else:
                report["recommended"][var_name] = "valid"
                print(f"✅ {var_name}: Found")

        # Check production-specific requirements
        if self.environment == "production":
            print("\n🔍 Checking production-specific requirements...")
            for var_name, default_value in self.PRODUCTION_REQUIRED.items():
                value = os.getenv(var_name)
                if value == default_value:
                    self.errors.append(
                        f"❌ {var_name}: Using default value in production is not allowed!"
                    )
                    report["required"][var_name] = "invalid"

        # Check for Celery/Redis requirements
        if os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL"):
            self.info.append(
                "ℹ️  Celery/Redis configured - transcription features enabled"
            )
        else:
            self.warnings.append(
                "⚠️  No Redis/Celery configured - transcription features disabled"
            )

        # Compile report
        report["errors"] = self.errors
        report["warnings"] = self.warnings
        report["info"] = self.info
        report["status"] = "valid" if not self.errors else "invalid"

        return len(self.errors) == 0, report

    def _validate_var_content(
        self, var_name: str, value: str
    ) -> Tuple[bool, str]:
        """
        Validate specific environment variable content.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if var_name == "DATABASE_URL":
            if not value.startswith(("postgresql://", "postgres://")):
                return (
                    False,
                    "Invalid database URL format (should start with postgresql://)",
                )
            return True, ""

        elif var_name == "GOOGLE_APPLICATION_CREDENTIALS_JSON":
            # Try to validate JSON structure
            try:
                # First try direct JSON parsing
                try:
                    creds = json.loads(value)
                except json.JSONDecodeError:
                    # Try base64 decoding
                    try:
                        decoded = base64.b64decode(value)
                        creds = json.loads(decoded)
                    except:
                        return (
                            False,
                            "Invalid credentials format (not valid JSON or base64)",
                        )

                # Check for required fields
                required_fields = [
                    "type",
                    "project_id",
                    "private_key",
                    "client_email",
                ]
                missing_fields = [f for f in required_fields if f not in creds]

                if missing_fields:
                    return (
                        False,
                        f"Missing fields in service account JSON: {', '.join(missing_fields)}",
                    )

                if creds.get("type") != "service_account":
                    return False, "Credentials type must be 'service_account'"

                # Check for placeholder values
                if "your-project" in creds.get("project_id", ""):
                    return (
                        False,
                        "Using placeholder project ID - please use real credentials",
                    )

                return True, ""

            except Exception as e:
                return False, f"Failed to validate credentials: {str(e)}"

        elif var_name in ["AUDIO_STORAGE_BUCKET", "TRANSCRIPT_STORAGE_BUCKET"]:
            # Validate bucket name format
            if not value:
                return False, "Bucket name cannot be empty"
            if len(value) < 3 or len(value) > 63:
                return False, "Bucket name must be 3-63 characters"
            if not value[0].isalnum() or not value[-1].isalnum():
                return (
                    False,
                    "Bucket name must start and end with alphanumeric character",
                )
            return True, ""

        elif var_name == "SECRET_KEY":
            if len(value) < 32:
                return (
                    False,
                    "Secret key should be at least 32 characters for security",
                )
            if value == "dev-secret-key":
                if self.environment == "production":
                    return False, "Cannot use default secret key in production"
                else:
                    self.warnings.append(
                        f"⚠️  Using default SECRET_KEY - only for development!"
                    )
            return True, ""

        return True, ""

    def print_report(self, is_valid: bool, report: Dict):
        """Print validation report to console."""
        print("\n" + "=" * 60)
        print("📊 ENVIRONMENT VALIDATION REPORT")
        print("=" * 60)
        print(f"Environment: {report['environment']}")
        print(f"Status: {'✅ VALID' if is_valid else '❌ INVALID'}")

        if self.errors:
            print("\n❌ ERRORS (Must fix before starting):")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS (Recommended to fix):")
            for warning in self.warnings:
                print(f"  {warning}")

        if self.info:
            print("\nℹ️  INFO:")
            for info in self.info:
                print(f"  {info}")

        if not is_valid:
            print("\n🛑 STARTUP BLOCKED: Please fix the errors above")
            print("\n📝 Quick Setup Guide:")
            print("1. Copy .env.example to .env")
            print("2. Fill in the required values")
            print(
                "3. Run scripts/setup_env/setup-gcs.sh for Google Cloud setup"
            )
            print("4. Restart the application")

        print("\n" + "=" * 60)

    def validate_and_exit_on_error(self) -> None:
        """
        Validate environment and exit if critical errors found.

        This is the main method to call during application startup.
        """
        is_valid, report = self.validate_all()
        self.print_report(is_valid, report)

        if not is_valid:
            print(
                "\n💥 Application startup aborted due to missing configuration!"
            )
            print("Please fix the errors and try again.")
            sys.exit(1)

        if self.warnings:
            print(
                "\n⚠️  Starting with warnings - some features may not work properly"
            )
        else:
            print("\n✅ All environment variables validated successfully!")


def validate_environment():
    """
    Convenience function to validate environment at startup.

    Call this from your main application startup.
    """
    validator = EnvironmentValidator()
    validator.validate_and_exit_on_error()
