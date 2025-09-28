#!/usr/bin/env python3
"""
環境變數轉換工具 - 將 .env.prod 轉換為 terraform.tfvars

使用方式:
    python env-to-tfvars.py --env-file .env.prod --output terraform.tfvars
    python env-to-tfvars.py --env-file .env.prod --environment production
"""

import argparse
import os
from pathlib import Path
from typing import Dict, Optional


class EnvToTerraformConverter:
    """環境變數到 Terraform 變數轉換器"""

    # 環境變數到 Terraform 變數的映射
    ENV_TO_TF_MAPPING = {
        # Provider Credentials
        "CLOUDFLARE_API_TOKEN": "cloudflare_api_token",
        "RENDER_API_KEY": "render_api_key",
        # Cloudflare Configuration
        "CLOUDFLARE_ZONE_ID": "cloudflare_zone_id",
        "CLOUDFLARE_ACCOUNT_ID": "cloudflare_account_id",
        "DOMAIN": "domain",
        "FRONTEND_SUBDOMAIN": "frontend_subdomain",
        "API_SUBDOMAIN": "api_subdomain",
        # Project Configuration
        "PROJECT_NAME": "project_name",
        "APP_VERSION": "app_version",
        "BUILD_ID": "build_id",
        "COMMIT_SHA": "commit_sha",
        # GitHub Configuration
        "GITHUB_OWNER": "github_owner",
        "GITHUB_REPO": "github_repo",
        "GITHUB_REPO_URL": "github_repo_url",
        # GCP Configuration
        "GOOGLE_PROJECT_ID": "gcp_project_id",  # 修正：從 .env.prod 實際變數名
        "GCP_PROJECT_ID": "gcp_project_id",  # 保留原有作為備用
        "GCP_REGION": "gcp_region",
        # Render Configuration
        "RENDER_REGION": "render_region",
        # Application Secrets
        "API_SECRET_KEY": "api_secret_key",
        "SECRET_KEY": "api_secret_key",  # 從 .env.prod 實際變數名映射到同樣的 terraform 變數
        "DATABASE_PASSWORD": "database_password",
        # Google OAuth
        "GOOGLE_CLIENT_ID": "google_client_id",
        "GOOGLE_CLIENT_SECRET": "google_client_secret",
        "GOOGLE_CLIENT_ID_STAGING": "google_client_id_staging",
        # reCAPTCHA
        "RECAPTCHA_SITE_KEY": "recaptcha_site_key",
        "RECAPTCHA_SITE_KEY_STAGING": "recaptcha_site_key_staging",
        "RECAPTCHA_SECRET": "recaptcha_secret",
        # STT Configuration
        "STT_PROVIDER": "stt_provider",
        "GOOGLE_STT_MODEL": "google_stt_model",
        "GOOGLE_STT_LOCATION": "google_stt_location",
        "ASSEMBLYAI_API_KEY": "assemblyai_api_key",
        # Analytics
        "WEB_ANALYTICS_TAG": "web_analytics_tag",
        "WEB_ANALYTICS_TOKEN": "web_analytics_token",
        # Monitoring
        "MONITORING_EMAIL": "monitoring_email",
        "SENTRY_DSN": "sentry_dsn",
        # Feature Flags
        "ENABLE_FLOWER_MONITORING": "enable_flower_monitoring",
        "FLOWER_AUTH": "flower_auth",
        # ECPay Configuration
        "ECPAY_MERCHANT_ID": "ecpay_merchant_id",
        "ECPAY_HASH_KEY": "ecpay_hash_key",
        "ECPAY_HASH_IV": "ecpay_hash_iv",
        "ECPAY_ENVIRONMENT": "ecpay_environment",
        # Admin Security
        "ADMIN_WEBHOOK_TOKEN": "admin_webhook_token",
        # Additional API Server Variables
        "DATABASE_URL": "database_url",
        "REDIS_URL": "redis_url",
        "AUDIO_STORAGE_BUCKET": "audio_storage_bucket",
        "TRANSCRIPT_STORAGE_BUCKET": "transcript_storage_bucket",
        "GOOGLE_APPLICATION_CREDENTIALS_JSON": "google_application_credentials_json",
    }

    # 需要布林值轉換的變數
    BOOLEAN_VARS = {"enable_flower_monitoring"}

    # 不需要引號的變數 (數字、布林值等)
    UNQUOTED_VARS = {"enable_flower_monitoring"}

    def __init__(self):
        self.env_vars: Dict[str, str] = {}
        self.tf_vars: Dict[str, str] = {}

    def load_env_file(self, env_file: str) -> None:
        """載入環境變數檔案"""
        env_path = Path(env_file)
        if not env_path.exists():
            raise FileNotFoundError(f"環境檔案不存在: {env_file}")

        print(f"📖 讀取環境檔案: {env_file}")

        with open(env_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # 跳過註釋和空行
                if not line or line.startswith("#"):
                    continue

                # 解析 KEY=VALUE 格式
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # 移除引號
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]

                    self.env_vars[key] = value
                    print(
                        f"  ✅ {key}={value[:20]}..."
                        if len(value) > 20
                        else f"  ✅ {key}={value}"
                    )
                else:
                    print(f"  ⚠️  第 {line_num} 行格式不正確: {line}")

        print(f"📊 總共載入 {len(self.env_vars)} 個環境變數")

    def convert_to_terraform_vars(self) -> None:
        """轉換環境變數為 Terraform 變數"""
        print("\n🔄 轉換環境變數為 Terraform 變數...")

        converted_count = 0

        for env_key, tf_key in self.ENV_TO_TF_MAPPING.items():
            if env_key in self.env_vars:
                value = self.env_vars[env_key]

                # 布林值轉換
                if tf_key in self.BOOLEAN_VARS:
                    if value.lower() in ("true", "1", "yes", "on"):
                        value = "true"
                    elif value.lower() in ("false", "0", "no", "off"):
                        value = "false"
                    else:
                        print(f"  ⚠️  布林值 {tf_key} 的值不明確: {value}, 使用原值")

                self.tf_vars[tf_key] = value
                converted_count += 1
                print(f"  ✅ {env_key} → {tf_key}")

        print(f"📊 成功轉換 {converted_count} 個變數")

        # 檢查未對應的環境變數
        unmapped_vars = set(self.env_vars.keys()) - set(self.ENV_TO_TF_MAPPING.keys())
        if unmapped_vars:
            print(f"\n⚠️  未對應的環境變數 ({len(unmapped_vars)} 個):")
            for var in sorted(unmapped_vars):
                print(f"  - {var}")

    def generate_terraform_tfvars(self, template_file: Optional[str] = None) -> str:
        """生成 terraform.tfvars 內容"""
        print("\n📝 生成 terraform.tfvars 內容...")

        content_lines = []

        # 如果有模板檔案，先讀取模板結構
        template_structure = []
        current_section = ""

        if template_file and Path(template_file).exists():
            print(f"📄 使用模板檔案: {template_file}")
            with open(template_file, "r", encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line.startswith("#"):
                        current_section = stripped_line
                        template_structure.append(("comment", line))
                    elif "=" in stripped_line and not stripped_line.startswith("#"):
                        key = stripped_line.split("=")[0].strip()
                        template_structure.append(("var", key, current_section))
                    else:
                        template_structure.append(("other", line))

        # 根據模板結構生成內容
        if template_structure:
            current_section = ""
            for item in template_structure:
                if item[0] == "comment":
                    if current_section != item[1]:
                        current_section = item[1]
                        content_lines.append(item[1])
                elif item[0] == "var":
                    var_name = item[1]
                    section = item[2] if len(item) > 2 else ""

                    if var_name in self.tf_vars:
                        value = self.tf_vars[var_name]
                        if var_name in self.UNQUOTED_VARS:
                            content_lines.append(f"{var_name} = {value}")
                        else:
                            content_lines.append(f'{var_name} = "{value}"')
                    else:
                        content_lines.append(f'# {var_name} = "TODO: 填入實際值"')
                elif item[0] == "other":
                    content_lines.append(item[1].rstrip())
        else:
            # 如果沒有模板，按分類生成
            sections = {
                "# Provider Credentials": ["cloudflare_api_token", "render_api_key"],
                "# Cloudflare Configuration": [
                    "cloudflare_zone_id",
                    "cloudflare_account_id",
                    "domain",
                    "frontend_subdomain",
                    "api_subdomain",
                ],
                "# Project Configuration": [
                    "project_name",
                    "app_version",
                    "build_id",
                    "commit_sha",
                ],
                "# GitHub Configuration": [
                    "github_owner",
                    "github_repo",
                    "github_repo_url",
                ],
                "# GCP Configuration": ["gcp_project_id", "gcp_region"],
                "# Application Secrets": ["api_secret_key", "database_password"],
                "# Google OAuth": [
                    "google_client_id",
                    "google_client_secret",
                    "google_client_id_staging",
                ],
                "# reCAPTCHA": [
                    "recaptcha_site_key",
                    "recaptcha_site_key_staging",
                    "recaptcha_secret",
                ],
                "# STT Configuration": [
                    "stt_provider",
                    "google_stt_model",
                    "google_stt_location",
                    "assemblyai_api_key",
                ],
                "# ECPay Configuration": [
                    "ecpay_merchant_id",
                    "ecpay_hash_key",
                    "ecpay_hash_iv",
                    "ecpay_environment",
                ],
                "# Admin Security": ["admin_webhook_token"],
                "# Monitoring": ["monitoring_email", "sentry_dsn"],
                "# Feature Flags": ["enable_flower_monitoring", "flower_auth"],
            }

            for section_title, var_names in sections.items():
                content_lines.append("")
                content_lines.append(section_title)

                for var_name in var_names:
                    if var_name in self.tf_vars:
                        value = self.tf_vars[var_name]
                        if var_name in self.UNQUOTED_VARS:
                            content_lines.append(f"{var_name} = {value}")
                        else:
                            content_lines.append(f'{var_name} = "{value}"')
                    else:
                        content_lines.append(f'# {var_name} = "TODO: 填入實際值"')

        return "\n".join(content_lines)

    def save_terraform_tfvars(self, output_file: str, content: str) -> None:
        """儲存 terraform.tfvars 檔案"""
        print(f"\n💾 儲存到檔案: {output_file}")

        # 備份現有檔案
        output_path = Path(output_file)
        if output_path.exists():
            backup_file = f"{output_file}.backup.{os.getpid()}"
            output_path.rename(backup_file)
            print(f"📦 現有檔案已備份為: {backup_file}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ 檔案已儲存: {output_file}")
        print(f"📊 檔案大小: {output_path.stat().st_size} bytes")

    def process(
        self, env_file: str, output_file: str, template_file: Optional[str] = None
    ) -> None:
        """完整處理流程"""
        print("🚀 環境變數轉 Terraform 變數轉換工具")
        print("=" * 50)

        try:
            # 載入環境變數檔案
            self.load_env_file(env_file)

            # 轉換為 Terraform 變數
            self.convert_to_terraform_vars()

            # 生成 terraform.tfvars 內容
            content = self.generate_terraform_tfvars(template_file)

            # 儲存檔案
            self.save_terraform_tfvars(output_file, content)

            print("\n🎉 轉換完成!")
            print(f"📁 輸入檔案: {env_file}")
            print(f"📁 輸出檔案: {output_file}")
            print(f"📊 轉換變數: {len(self.tf_vars)} 個")

        except Exception as e:
            print(f"\n❌ 轉換失敗: {str(e)}")
            raise


def main():
    parser = argparse.ArgumentParser(
        description="將 .env 檔案轉換為 terraform.tfvars",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 基本轉換
  python env-to-tfvars.py --env-file .env.prod --output terraform.tfvars
  
  # 指定環境
  python env-to-tfvars.py --env-file .env.prod --environment production
  
  # 使用模板檔案
  python env-to-tfvars.py --env-file .env.prod --template terraform.tfvars.example --output terraform.tfvars
        """,
    )

    parser.add_argument(
        "--env-file", "-e", required=True, help="輸入的環境變數檔案 (例如: .env.prod)"
    )

    parser.add_argument("--output", "-o", help="輸出的 terraform.tfvars 檔案路徑")

    parser.add_argument(
        "--environment",
        choices=["development", "staging", "production"],
        help="目標環境 (會自動設定輸出路徑)",
    )

    parser.add_argument(
        "--template", "-t", help="模板檔案 (例如: terraform.tfvars.example)"
    )

    args = parser.parse_args()

    # 決定輸出檔案路徑
    if args.output:
        output_file = args.output
    elif args.environment:
        output_file = f"environments/{args.environment}/terraform.tfvars"
    else:
        output_file = "terraform.tfvars"

    # 決定模板檔案
    template_file = args.template
    if not template_file and args.environment:
        template_candidate = f"environments/{args.environment}/terraform.tfvars.example"
        if Path(template_candidate).exists():
            template_file = template_candidate

    # 執行轉換
    converter = EnvToTerraformConverter()
    converter.process(args.env_file, output_file, template_file)


if __name__ == "__main__":
    main()
