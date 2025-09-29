#!/usr/bin/env python3
"""
Configuration Environment Checker - 配置環境檢查工具

專門用於檢查和比較本地開發配置與生產/測試環境配置的工具。
支援配置驗證、環境一致性檢查、安全性審核等功能。

使用方式:
    python config-checker.py --check-consistency --environments development,production
    python config-checker.py --security-audit --path .env
    python config-checker.py --validate-terraform --environment production
    python config-checker.py --generate-report --output config-report.md
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class ConfigIssue:
    """配置問題記錄"""

    severity: str  # "critical", "high", "medium", "low", "info"
    category: str  # "missing", "mismatch", "security", "deprecated", "invalid"
    environment: str
    key: str
    message: str
    recommendation: str
    file_path: Optional[str] = None
    current_value: Optional[str] = None
    expected_value: Optional[str] = None


@dataclass
class EnvironmentConfig:
    """環境配置數據"""

    name: str
    config_file: str
    variables: Dict[str, str] = field(default_factory=dict)
    file_exists: bool = True
    last_modified: Optional[datetime] = None


@dataclass
class ConfigValidationResult:
    """配置驗證結果"""

    environment: str
    total_variables: int
    valid_variables: int
    issues: List[ConfigIssue] = field(default_factory=list)
    missing_required: Set[str] = field(default_factory=set)
    deprecated_found: Set[str] = field(default_factory=set)
    security_warnings: List[str] = field(default_factory=list)


class ConfigurationChecker:
    """配置檢查器主類"""

    # 必需的環境變數定義
    REQUIRED_VARIABLES = {
        # 資料庫配置 - 所有環境都需要
        "DATABASE_URL": {
            "environments": ["development", "staging", "production"],
            "pattern": r"^postgresql://.+",
            "description": "PostgreSQL database connection URL",
        },
        "REDIS_URL": {
            "environments": ["development", "staging", "production"],
            "pattern": r"^redis://.+",
            "description": "Redis connection URL for caching and task queue",
        },
        # 應用程式密鑰
        "SECRET_KEY": {
            "environments": ["development", "staging", "production"],
            "pattern": r".{32,}",  # 至少32字符
            "description": "Application secret key for JWT and cryptography",
        },
        # Google Cloud Platform
        "GCP_PROJECT_ID": {
            "environments": ["development", "staging", "production"],
            "pattern": r"^[a-z][-a-z0-9]{5,29}$",
            "description": "Google Cloud Platform project ID",
        },
        "GOOGLE_APPLICATION_CREDENTIALS_JSON": {
            "environments": ["development", "staging", "production"],
            "pattern": r'^\{.*"type".*"service_account".*\}$',
            "description": "GCP service account credentials in JSON format",
        },
        # 存儲配置
        "AUDIO_STORAGE_BUCKET": {
            "environments": ["development", "staging", "production"],
            "pattern": r"^coaching-audio-(dev|staging|prod)(-[a-z0-9-]+)?$",
            "description": "GCS bucket for audio file storage",
        },
        "TRANSCRIPT_STORAGE_BUCKET": {
            "environments": ["development", "staging", "production"],
            "pattern": r"^coaching-transcript-(dev|staging|prod)(-[a-z0-9-]+)?$",
            "description": "GCS bucket for transcript storage",
        },
        # 驗證服務
        "GOOGLE_CLIENT_ID": {
            "environments": ["development", "staging", "production"],
            "pattern": r"^.+\.apps\.googleusercontent\.com$",
            "description": "Google OAuth client ID",
        },
        "GOOGLE_CLIENT_SECRET": {
            "environments": ["development", "staging", "production"],
            "pattern": r"^[A-Za-z0-9_-]{24}$",
            "description": "Google OAuth client secret",
        },
        # reCAPTCHA
        "RECAPTCHA_SITE_KEY": {
            "environments": ["development", "staging", "production"],
            "pattern": r"^[A-Za-z0-9_-]{40}$",
            "description": "reCAPTCHA site key for frontend",
        },
        "RECAPTCHA_SECRET": {
            "environments": ["development", "staging", "production"],
            "pattern": r"^[A-Za-z0-9_-]{40}$",
            "description": "reCAPTCHA secret key for backend validation",
        },
        # STT 配置
        "STT_PROVIDER": {
            "environments": ["development", "staging", "production"],
            "pattern": r"^(google|assemblyai|auto)$",
            "description": "Speech-to-Text provider selection",
        },
        "GOOGLE_STT_MODEL": {
            "environments": ["development", "staging", "production"],
            "pattern": r"^(chirp|chirp_2|latest_long|latest_short)$",
            "description": "Google STT model selection",
        },
        "GOOGLE_STT_LOCATION": {
            "environments": ["development", "staging", "production"],
            "pattern": r"^(us-central1|asia-southeast1|asia-northeast1|europe-west1)$",
            "description": "Google STT processing location",
        },
        # 支付系統 (僅生產環境需要)
        "ECPAY_MERCHANT_ID": {
            "environments": ["production"],
            "pattern": r"^[0-9A-Za-z]+$",
            "description": "ECPay merchant identifier",
        },
    }

    # 已棄用的環境變數
    DEPRECATED_VARIABLES = {
        "GOOGLE_STORAGE_BUCKET": "AUDIO_STORAGE_BUCKET",
        "STORAGE_BUCKET": "AUDIO_STORAGE_BUCKET",
    }

    # 敏感變數 (用於安全檢查)
    SENSITIVE_VARIABLES = {
        "SECRET_KEY",
        "DATABASE_PASSWORD",
        "REDIS_PASSWORD",
        "GOOGLE_CLIENT_SECRET",
        "RECAPTCHA_SECRET",
        "ASSEMBLYAI_API_KEY",
        "ECPAY_HASH_KEY",
        "ECPAY_HASH_IV",
        "ADMIN_WEBHOOK_TOKEN",
        "SENTRY_DSN",
        "GOOGLE_APPLICATION_CREDENTIALS_JSON",
    }

    # Terraform 變數映射 (從 env-to-tfvars.py 復用)
    ENV_TO_TF_MAPPING = {
        "CLOUDFLARE_API_TOKEN": "cloudflare_api_token",
        "RENDER_API_KEY": "render_api_key",
        "CLOUDFLARE_ZONE_ID": "cloudflare_zone_id",
        "CLOUDFLARE_ACCOUNT_ID": "cloudflare_account_id",
        "DOMAIN": "domain",
        "FRONTEND_SUBDOMAIN": "frontend_subdomain",
        "API_SUBDOMAIN": "api_subdomain",
        "PROJECT_NAME": "project_name",
        "APP_VERSION": "app_version",
        "BUILD_ID": "build_id",
        "COMMIT_SHA": "commit_sha",
        "GITHUB_OWNER": "github_owner",
        "GITHUB_REPO": "github_repo",
        "GITHUB_REPO_URL": "github_repo_url",
        "GCP_PROJECT_ID": "gcp_project_id",
        "GCP_REGION": "gcp_region",
        "RENDER_REGION": "render_region",
        "API_SECRET_KEY": "api_secret_key",
        "DATABASE_PASSWORD": "database_password",
        "GOOGLE_CLIENT_ID": "google_client_id",
        "GOOGLE_CLIENT_SECRET": "google_client_secret",
        "GOOGLE_CLIENT_ID_STAGING": "google_client_id_staging",
        "RECAPTCHA_SITE_KEY": "recaptcha_site_key",
        "RECAPTCHA_SITE_KEY_STAGING": "recaptcha_site_key_staging",
        "RECAPTCHA_SECRET": "recaptcha_secret",
        "STT_PROVIDER": "stt_provider",
        "GOOGLE_STT_MODEL": "google_stt_model",
        "GOOGLE_STT_LOCATION": "google_stt_location",
        "ASSEMBLYAI_API_KEY": "assemblyai_api_key",
        "WEB_ANALYTICS_TAG": "web_analytics_tag",
        "WEB_ANALYTICS_TOKEN": "web_analytics_token",
        "MONITORING_EMAIL": "monitoring_email",
        "SENTRY_DSN": "sentry_dsn",
        "ENABLE_FLOWER_MONITORING": "enable_flower_monitoring",
        "FLOWER_AUTH": "flower_auth",
        "ECPAY_MERCHANT_ID": "ecpay_merchant_id",
        "ECPAY_HASH_KEY": "ecpay_hash_key",
        "ECPAY_HASH_IV": "ecpay_hash_iv",
        "ECPAY_ENVIRONMENT": "ecpay_environment",
        "ADMIN_WEBHOOK_TOKEN": "admin_webhook_token",
    }

    def __init__(self, project_root: str = None):
        """初始化配置檢查器"""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.terraform_root = self.project_root / "terraform"
        self.environments: Dict[str, EnvironmentConfig] = {}
        self.validation_results: Dict[str, ConfigValidationResult] = {}

        # 建立日誌系統
        self.logger = self._setup_logging()

    def _setup_logging(self):
        """設置日誌記錄"""
        import logging

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def discover_config_files(self) -> Dict[str, str]:
        """自動發現配置文件"""
        config_files = {}

        # 常見的配置檔案位置
        search_patterns = [
            # 開發環境
            ".env",
            ".env.local",
            ".env.development",
            ".env.dev",
            # 測試環境
            ".env.staging",
            ".env.test",
            # 生產環境
            ".env.production",
            ".env.prod",
            # Terraform 配置
            "terraform/environments/*/terraform.tfvars",
            "terraform/gcp/terraform.tfvars.*",
        ]

        for pattern in search_patterns:
            if "*" in pattern:
                # 使用 glob 模式
                for path in self.project_root.glob(pattern):
                    if path.is_file():
                        # 從路徑推斷環境名稱
                        env_name = self._infer_environment_name(str(path))
                        config_files[env_name] = str(path)
            else:
                path = self.project_root / pattern
                if path.exists():
                    env_name = self._infer_environment_name(str(path))
                    config_files[env_name] = str(path)

        return config_files

    def _infer_environment_name(self, file_path: str) -> str:
        """從檔案路徑推斷環境名稱"""
        path_lower = file_path.lower()

        if "production" in path_lower or "prod" in path_lower:
            return "production"
        elif "staging" in path_lower or "stage" in path_lower:
            return "staging"
        elif "development" in path_lower or "dev" in path_lower:
            return "development"
        elif "test" in path_lower:
            return "test"
        elif ".env.local" in path_lower:
            return "local"
        else:
            return "development"  # 預設為開發環境

    def load_environment_config(
        self, env_name: str, config_file: str
    ) -> EnvironmentConfig:
        """載入環境配置"""
        config = EnvironmentConfig(name=env_name, config_file=config_file)
        config_path = Path(config_file)

        if not config_path.exists():
            config.file_exists = False
            return config

        config.last_modified = datetime.fromtimestamp(config_path.stat().st_mtime)

        # 根據檔案類型選擇解析方法
        if config_file.endswith(".tfvars"):
            config.variables = self._parse_tfvars_file(config_file)
        else:
            config.variables = self._parse_env_file(config_file)

        return config

    def _parse_env_file(self, file_path: str) -> Dict[str, str]:
        """解析 .env 格式檔案"""
        variables = {}

        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # 移除引號
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]

                    variables[key] = value

        return variables

    def _parse_tfvars_file(self, file_path: str) -> Dict[str, str]:
        """解析 terraform.tfvars 格式檔案"""
        variables = {}

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

            # 簡單的 tfvars 解析 (處理基本的 key = "value" 格式)
            pattern = r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"?([^"]*)"?'

            for line in content.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                match = re.match(pattern, line)
                if match:
                    key, value = match.groups()
                    # 轉換 terraform 變數名為環境變數名
                    env_key = self._tf_to_env_key(key)
                    if env_key:
                        variables[env_key] = value

        return variables

    def _tf_to_env_key(self, tf_key: str) -> Optional[str]:
        """將 Terraform 變數名轉換為環境變數名"""
        # 反向映射
        reverse_mapping = {v: k for k, v in self.ENV_TO_TF_MAPPING.items()}
        return reverse_mapping.get(tf_key)

    def validate_environment(self, env_name: str) -> ConfigValidationResult:
        """驗證特定環境的配置"""
        if env_name not in self.environments:
            raise ValueError(f"Environment '{env_name}' not loaded")

        config = self.environments[env_name]
        result = ConfigValidationResult(
            environment=env_name,
            total_variables=len(config.variables),
            valid_variables=0,
        )

        if not config.file_exists:
            result.issues.append(
                ConfigIssue(
                    severity="critical",
                    category="missing",
                    environment=env_name,
                    key="config_file",
                    message=f"Configuration file does not exist: {config.config_file}",
                    recommendation="Create the missing configuration file",
                    file_path=config.config_file,
                )
            )
            return result

        # 檢查必需變數
        for var_name, var_config in self.REQUIRED_VARIABLES.items():
            if env_name not in var_config["environments"]:
                continue

            if var_name not in config.variables:
                result.missing_required.add(var_name)
                result.issues.append(
                    ConfigIssue(
                        severity="high",
                        category="missing",
                        environment=env_name,
                        key=var_name,
                        message=f"Required variable '{var_name}' is missing",
                        recommendation=f"Add {var_name} to your configuration. {var_config['description']}",
                        file_path=config.config_file,
                    )
                )
            else:
                # 驗證變數格式
                value = config.variables[var_name]
                pattern = var_config.get("pattern")

                if pattern and not re.match(pattern, value):
                    result.issues.append(
                        ConfigIssue(
                            severity="medium",
                            category="invalid",
                            environment=env_name,
                            key=var_name,
                            message=f"Variable '{var_name}' has invalid format",
                            recommendation=f"Fix the format of {var_name}. Expected pattern: {pattern}",
                            file_path=config.config_file,
                            current_value=value[:20] + "..."
                            if len(value) > 20
                            else value,
                        )
                    )
                else:
                    result.valid_variables += 1

        # 檢查已棄用變數
        for deprecated_var, replacement in self.DEPRECATED_VARIABLES.items():
            if deprecated_var in config.variables:
                result.deprecated_found.add(deprecated_var)
                result.issues.append(
                    ConfigIssue(
                        severity="low",
                        category="deprecated",
                        environment=env_name,
                        key=deprecated_var,
                        message=f"Variable '{deprecated_var}' is deprecated",
                        recommendation=f"Replace {deprecated_var} with {replacement}",
                        file_path=config.config_file,
                        current_value=config.variables[deprecated_var],
                    )
                )

        # 安全性檢查
        self._perform_security_checks(config, result)

        return result

    def _perform_security_checks(
        self, config: EnvironmentConfig, result: ConfigValidationResult
    ):
        """執行安全性檢查"""
        for var_name, value in config.variables.items():
            if var_name in self.SENSITIVE_VARIABLES:
                # 檢查是否為預設值或測試值
                if self._is_default_or_test_value(var_name, value):
                    result.security_warnings.append(
                        f"{var_name} appears to use default/test value"
                    )
                    result.issues.append(
                        ConfigIssue(
                            severity="high",
                            category="security",
                            environment=config.name,
                            key=var_name,
                            message=f"Sensitive variable '{var_name}' may be using default/test value",
                            recommendation=f"Update {var_name} with a secure production value",
                            file_path=config.config_file,
                        )
                    )

                # 檢查長度 (針對金鑰類變數)
                if "KEY" in var_name or "SECRET" in var_name:
                    if len(value) < 20:
                        result.issues.append(
                            ConfigIssue(
                                severity="medium",
                                category="security",
                                environment=config.name,
                                key=var_name,
                                message=f"Variable '{var_name}' might be too short for security",
                                recommendation=f"Ensure {var_name} has sufficient entropy (recommended: 32+ characters)",
                                file_path=config.config_file,
                            )
                        )

    def _is_default_or_test_value(self, var_name: str, value: str) -> bool:
        """檢查是否為預設或測試值"""
        default_patterns = [
            "your-",
            "test-",
            "dev-",
            "example",
            "sample",
            "localhost",
            "changeme",
            "password",
            "123456",
            "secret",
            "token",
            "key",
        ]

        value_lower = value.lower()
        return any(pattern in value_lower for pattern in default_patterns)

    def compare_environments(self, env1: str, env2: str) -> List[ConfigIssue]:
        """比較兩個環境的配置差異"""
        if env1 not in self.environments or env2 not in self.environments:
            raise ValueError("Both environments must be loaded")

        config1 = self.environments[env1]
        config2 = self.environments[env2]

        differences = []
        all_keys = set(config1.variables.keys()) | set(config2.variables.keys())

        for key in all_keys:
            val1 = config1.variables.get(key)
            val2 = config2.variables.get(key)

            if val1 is None:
                differences.append(
                    ConfigIssue(
                        severity="medium",
                        category="missing",
                        environment=env1,
                        key=key,
                        message=f"Variable '{key}' exists in {env2} but not in {env1}",
                        recommendation=f"Consider adding {key} to {env1} configuration",
                        file_path=config1.config_file,
                        expected_value=val2,
                    )
                )
            elif val2 is None:
                differences.append(
                    ConfigIssue(
                        severity="info",
                        category="missing",
                        environment=env2,
                        key=key,
                        message=f"Variable '{key}' exists in {env1} but not in {env2}",
                        recommendation=f"Consider whether {key} is needed in {env2}",
                        file_path=config2.config_file,
                        current_value=val1,
                    )
                )
            elif val1 != val2:
                # 某些變數在不同環境中應該不同
                if self._should_differ_between_environments(key):
                    continue

                differences.append(
                    ConfigIssue(
                        severity="low",
                        category="mismatch",
                        environment=f"{env1}↔{env2}",
                        key=key,
                        message=f"Variable '{key}' has different values between {env1} and {env2}",
                        recommendation="Verify if the difference is intentional",
                        current_value=val1[:30] + "..." if len(val1) > 30 else val1,
                        expected_value=val2[:30] + "..." if len(val2) > 30 else val2,
                    )
                )

        return differences

    def _should_differ_between_environments(self, var_name: str) -> bool:
        """判斷變數是否應該在不同環境中有不同值"""
        environment_specific = {
            "DATABASE_URL",
            "REDIS_URL",
            "AUDIO_STORAGE_BUCKET",
            "TRANSCRIPT_STORAGE_BUCKET",
            "DOMAIN",
            "API_HOST",
            "GOOGLE_CLIENT_ID",
            "RECAPTCHA_SITE_KEY",
            "ECPAY_ENVIRONMENT",
        }

        return var_name in environment_specific

    def validate_terraform_consistency(self, env_name: str) -> List[ConfigIssue]:
        """檢查環境變數與 Terraform 配置的一致性"""
        if env_name not in self.environments:
            raise ValueError(f"Environment '{env_name}' not loaded")

        config = self.environments[env_name]
        issues = []

        # 尋找對應的 terraform.tfvars 檔案
        tfvars_path = (
            self.terraform_root / "environments" / env_name / "terraform.tfvars"
        )

        if not tfvars_path.exists():
            issues.append(
                ConfigIssue(
                    severity="medium",
                    category="missing",
                    environment=env_name,
                    key="terraform_config",
                    message=f"No corresponding Terraform configuration found for {env_name}",
                    recommendation=f"Create Terraform configuration at {tfvars_path}",
                    file_path=str(tfvars_path),
                )
            )
            return issues

        # 載入 Terraform 配置
        tf_config = EnvironmentConfig(
            name=f"{env_name}-terraform", config_file=str(tfvars_path)
        )
        tf_config.variables = self._parse_tfvars_file(str(tfvars_path))

        # 比較可映射的變數
        for env_key, tf_key in self.ENV_TO_TF_MAPPING.items():
            env_value = config.variables.get(env_key)
            tf_env_value = tf_config.variables.get(env_key)  # 從 tfvars 轉換來的值

            if env_value and not tf_env_value:
                issues.append(
                    ConfigIssue(
                        severity="medium",
                        category="mismatch",
                        environment=env_name,
                        key=env_key,
                        message=f"Variable '{env_key}' exists in env but not in Terraform",
                        recommendation=f'Add {tf_key} = "{env_value}" to {tfvars_path}',
                        file_path=str(tfvars_path),
                        current_value=env_value,
                    )
                )
            elif tf_env_value and not env_value:
                issues.append(
                    ConfigIssue(
                        severity="low",
                        category="mismatch",
                        environment=env_name,
                        key=env_key,
                        message=f"Variable '{env_key}' exists in Terraform but not in env",
                        recommendation=f"Consider adding {env_key}={tf_env_value} to environment config",
                        file_path=config.config_file,
                        expected_value=tf_env_value,
                    )
                )
            elif env_value and tf_env_value and env_value != tf_env_value:
                issues.append(
                    ConfigIssue(
                        severity="high",
                        category="mismatch",
                        environment=env_name,
                        key=env_key,
                        message=f"Variable '{env_key}' has different values in env and Terraform",
                        recommendation="Synchronize the values between environment and Terraform config",
                        file_path=config.config_file,
                        current_value=env_value[:30] + "..."
                        if len(env_value) > 30
                        else env_value,
                        expected_value=tf_env_value[:30] + "..."
                        if len(tf_env_value) > 30
                        else tf_env_value,
                    )
                )

        return issues

    def generate_markdown_report(self, output_path: str = None) -> str:
        """生成 Markdown 格式的配置檢查報告"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"config-check-report-{timestamp}.md"

        report_lines = []

        # 報告標題
        report_lines.extend(
            [
                "# 🔍 Configuration Environment Check Report",
                "",
                f"**Generated at:** {datetime.now().isoformat()}",
                f"**Project Root:** `{self.project_root}`",
                "",
                "## 📊 Executive Summary",
                "",
            ]
        )

        # 執行摘要
        total_environments = len(self.environments)
        total_issues = sum(
            len(result.issues) for result in self.validation_results.values()
        )
        critical_issues = sum(
            1
            for result in self.validation_results.values()
            for issue in result.issues
            if issue.severity == "critical"
        )
        high_issues = sum(
            1
            for result in self.validation_results.values()
            for issue in result.issues
            if issue.severity == "high"
        )

        report_lines.extend(
            [
                f"- **Environments Checked:** {total_environments}",
                f"- **Total Issues Found:** {total_issues}",
                f"- **Critical Issues:** {critical_issues} 🔴",
                f"- **High Priority Issues:** {high_issues} 🟠",
                "",
            ]
        )

        # 環境狀態概覽
        report_lines.extend(
            [
                "## 🌍 Environment Status Overview",
                "",
                "| Environment | Config File | Status | Variables | Issues | Last Modified |",
                "|-------------|-------------|--------|-----------|--------|---------------|",
            ]
        )

        for env_name, config in self.environments.items():
            status = (
                "✅ Healthy"
                if env_name in self.validation_results
                and len(
                    [
                        i
                        for i in self.validation_results[env_name].issues
                        if i.severity in ["critical", "high"]
                    ]
                )
                == 0
                else "⚠️ Issues"
            )

            if not config.file_exists:
                status = "❌ Missing"

            var_count = len(config.variables)
            default_result = ConfigValidationResult("", 0, 0)
            default_result.issues = []
            issue_count = len(
                self.validation_results.get(env_name, default_result).issues
            )
            last_mod = (
                config.last_modified.strftime("%Y-%m-%d %H:%M")
                if config.last_modified
                else "N/A"
            )

            report_lines.append(
                f"| {env_name} | `{config.config_file}` | {status} | {var_count} | {issue_count} | {last_mod} |"
            )

        report_lines.append("")

        # 詳細環境報告
        for env_name, result in self.validation_results.items():
            report_lines.extend([f"## 🔧 {env_name.title()} Environment Details", ""])

            config = self.environments[env_name]

            # 基本資訊
            report_lines.extend(
                [
                    f"**Configuration File:** `{config.config_file}`",
                    f"**File Exists:** {'✅ Yes' if config.file_exists else '❌ No'}",
                    f"**Total Variables:** {result.total_variables}",
                    f"**Valid Variables:** {result.valid_variables}",
                    f"**Missing Required:** {len(result.missing_required)}",
                    f"**Deprecated Found:** {len(result.deprecated_found)}",
                    f"**Security Warnings:** {len(result.security_warnings)}",
                    "",
                ]
            )

            # 問題按嚴重性分組
            issues_by_severity = {}
            for issue in result.issues:
                if issue.severity not in issues_by_severity:
                    issues_by_severity[issue.severity] = []
                issues_by_severity[issue.severity].append(issue)

            # 顯示問題
            severity_icons = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🔵",
                "info": "ℹ️",
            }

            if result.issues:
                report_lines.append("### Issues Found")
                report_lines.append("")

                for severity in ["critical", "high", "medium", "low", "info"]:
                    if severity in issues_by_severity:
                        report_lines.append(
                            f"#### {severity_icons.get(severity, '•')} {severity.title()} Issues"
                        )
                        report_lines.append("")

                        for issue in issues_by_severity[severity]:
                            report_lines.extend(
                                [
                                    f"**{issue.key}** ({issue.category})",
                                    f"- **Problem:** {issue.message}",
                                    f"- **Recommendation:** {issue.recommendation}",
                                    f"- **File:** `{issue.file_path or 'N/A'}`",
                                ]
                            )

                            if issue.current_value:
                                report_lines.append(
                                    f"- **Current Value:** `{issue.current_value}`"
                                )
                            if issue.expected_value:
                                report_lines.append(
                                    f"- **Expected Value:** `{issue.expected_value}`"
                                )

                            report_lines.append("")
            else:
                report_lines.extend(
                    [
                        "### ✅ No Issues Found",
                        "",
                        "This environment configuration appears to be healthy!",
                        "",
                    ]
                )

        # 安全建議
        report_lines.extend(
            [
                "## 🔒 Security Recommendations",
                "",
                "1. **Environment Separation**: Ensure production secrets are never used in development",
                "2. **Secret Rotation**: Regularly rotate API keys and passwords",
                "3. **Access Control**: Limit who can access production configuration files",
                "4. **Backup**: Keep secure backups of configuration files",
                "5. **Monitoring**: Set up alerts for configuration drift",
                "",
                "## 🛠️ Next Steps",
                "",
                "1. Address all critical and high-priority issues first",
                "2. Update deprecated environment variables",
                "3. Ensure Terraform and environment configurations are synchronized",
                "4. Set up automated configuration validation in CI/CD pipeline",
                "5. Document environment-specific configuration requirements",
                "",
                "---",
                f"*Report generated by Configuration Checker v1.0 - {datetime.now().isoformat()}*",
            ]
        )

        # 儲存報告
        report_content = "\n".join(report_lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        return output_path

    def run_comprehensive_check(
        self, environments: List[str] = None, generate_report: bool = True
    ) -> Dict[str, any]:
        """執行全面的配置檢查"""

        self.logger.info("🚀 Starting comprehensive configuration check...")

        # 自動發現配置檔案
        discovered_configs = self.discover_config_files()
        self.logger.info(f"📁 Discovered {len(discovered_configs)} configuration files")

        # 篩選要檢查的環境
        if environments:
            configs_to_check = {
                k: v for k, v in discovered_configs.items() if k in environments
            }
        else:
            configs_to_check = discovered_configs

        # 載入環境配置
        for env_name, config_file in configs_to_check.items():
            self.logger.info(f"📖 Loading {env_name} configuration from {config_file}")
            self.environments[env_name] = self.load_environment_config(
                env_name, config_file
            )

        # 驗證每個環境
        for env_name in self.environments:
            self.logger.info(f"🔍 Validating {env_name} environment...")
            self.validation_results[env_name] = self.validate_environment(env_name)

        # 環境比較 (如果有多個環境)
        comparison_results = []
        env_names = list(self.environments.keys())

        if len(env_names) > 1:
            # 比較開發環境與生產環境
            if "development" in env_names and "production" in env_names:
                self.logger.info("🔄 Comparing development vs production...")
                comparison_results.extend(
                    self.compare_environments("development", "production")
                )

        # Terraform 一致性檢查
        terraform_issues = []
        for env_name in self.environments:
            if env_name in ["development", "staging", "production"]:
                self.logger.info(f"⚙️ Checking Terraform consistency for {env_name}...")
                terraform_issues.extend(self.validate_terraform_consistency(env_name))

        # 生成報告
        report_path = None
        if generate_report:
            self.logger.info("📝 Generating comprehensive report...")
            report_path = self.generate_markdown_report()
            self.logger.info(f"✅ Report saved to: {report_path}")

        # 返回結果摘要
        results = {
            "environments_checked": len(self.environments),
            "total_issues": sum(
                len(r.issues) for r in self.validation_results.values()
            ),
            "critical_issues": sum(
                1
                for r in self.validation_results.values()
                for issue in r.issues
                if issue.severity == "critical"
            ),
            "high_issues": sum(
                1
                for r in self.validation_results.values()
                for issue in r.issues
                if issue.severity == "high"
            ),
            "validation_results": self.validation_results,
            "comparison_results": comparison_results,
            "terraform_issues": terraform_issues,
            "report_path": report_path,
        }

        # 輸出摘要
        self.logger.info("🎉 Configuration check completed!")
        self.logger.info(f"📊 Environments: {results['environments_checked']}")
        self.logger.info(f"📊 Total Issues: {results['total_issues']}")
        self.logger.info(
            f"📊 Critical: {results['critical_issues']} | High: {results['high_issues']}"
        )

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Configuration Environment Checker - 檢查和比較配置環境",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 全面檢查所有環境
  python config-checker.py --comprehensive

  # 檢查特定環境
  python config-checker.py --environments development,production

  # 安全審核
  python config-checker.py --security-audit

  # 只驗證 Terraform 一致性
  python config-checker.py --validate-terraform --environment production

  # 生成詳細報告
  python config-checker.py --generate-report --output config-audit.md
        """,
    )

    parser.add_argument(
        "--comprehensive", action="store_true", help="執行全面配置檢查 (推薦)"
    )

    parser.add_argument(
        "--environments",
        "-e",
        help="指定要檢查的環境 (逗號分隔，例如: development,production)",
    )

    parser.add_argument(
        "--security-audit", action="store_true", help="專注於安全性檢查"
    )

    parser.add_argument(
        "--validate-terraform", action="store_true", help="驗證 Terraform 配置一致性"
    )

    parser.add_argument("--environment", help="單一環境檢查 (用於 Terraform 驗證)")

    parser.add_argument(
        "--generate-report", action="store_true", help="生成詳細的 Markdown 報告"
    )

    parser.add_argument("--output", "-o", help="報告輸出檔案路徑")

    parser.add_argument("--project-root", help="專案根目錄路徑 (預設: 當前目錄)")

    args = parser.parse_args()

    # 初始化檢查器
    checker = ConfigurationChecker(project_root=args.project_root)

    try:
        if args.comprehensive:
            # 全面檢查
            environments = args.environments.split(",") if args.environments else None
            results = checker.run_comprehensive_check(
                environments=environments, generate_report=True
            )

            # 根據結果設置退出碼
            if results["critical_issues"] > 0:
                sys.exit(2)  # 有嚴重問題
            elif results["high_issues"] > 0:
                sys.exit(1)  # 有高優先級問題
            else:
                sys.exit(0)  # 正常

        elif args.security_audit:
            # 安全審核模式
            print("🔒 Security Audit Mode - 實作中...")
            # TODO: 實作專門的安全審核功能

        elif args.validate_terraform:
            # Terraform 驗證模式
            if not args.environment:
                print("❌ --environment required for Terraform validation")
                sys.exit(1)

            print(f"⚙️ Terraform Validation Mode for {args.environment} - 實作中...")
            # TODO: 實作 Terraform 專用驗證

        else:
            # 預設: 顯示使用說明
            parser.print_help()
            print("\n💡 建議使用 --comprehensive 執行全面檢查")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
