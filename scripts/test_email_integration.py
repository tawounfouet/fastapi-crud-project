#!/usr/bin/env python3
"""
Email Integration Test via FastAPI Endpoints

This script tests email functionality through the actual FastAPI application endpoints.
It simulates real user interactions that trigger email sending.
"""

import sys
import requests
from pathlib import Path

# Add src to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

try:
    from src.core.config import settings

    print("✅ Successfully imported settings")
except ImportError as e:
    print("❌ Failed to import settings:", str(e))
    sys.exit(1)


def test_email_endpoint_with_admin():
    """Test the email endpoint using admin authentication."""
    print("\n🔐 Testing Email Endpoint with Admin Authentication...")

    base_url = "http://localhost:8001"

    try:
        # Login as admin to get token
        login_data = {
            "username": settings.FIRST_SUPERUSER,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
        }

        print("📧 Logging in as admin:", str(settings.FIRST_SUPERUSER))
        login_response = requests.post(
            f"{base_url}/api/v1/auth/login/access-token", data=login_data
        )

        if login_response.status_code != 200:
            print("❌ Admin login failed:", login_response.status_code)
            print("   Response:", login_response.text)
            return False

        token_data = login_response.json()
        access_token = token_data["access_token"]
        print("✅ Admin login successful")

        # Test email endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        email_test_url = f"{base_url}/api/v1/utils/test-email/"

        # Send test email to the admin email
        print("📤 Sending test email to:", str(settings.FIRST_SUPERUSER))
        email_response = requests.post(
            email_test_url,
            params={
                "email_to": str(settings.FIRST_SUPERUSER)
            },  # Send as query parameter
            headers=headers,
        )

        if email_response.status_code == 201:
            print("✅ Test email sent successfully via API endpoint!")
            print("   Response:", email_response.json())
            print("   Check inbox:", str(settings.FIRST_SUPERUSER))
            return True
        else:
            print("❌ Email endpoint failed:", email_response.status_code)
            print("   Response:", email_response.text)
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server")
        print("   Make sure the server is running: make dev")
        return False
    except Exception as e:
        print("❌ Email endpoint test failed:", str(e))
        return False


def test_password_reset_flow():
    """Test the password reset email flow."""
    print("\n🔄 Testing Password Reset Email Flow...")

    base_url = "http://localhost:8001"

    try:
        # Request password reset
        print("🔐 Requesting password reset for:", str(settings.FIRST_SUPERUSER))
        reset_response = requests.post(
            f"{base_url}/api/v1/auth/password-recovery",
            json={"email": settings.FIRST_SUPERUSER},
        )

        if reset_response.status_code == 200:
            print("✅ Password reset email sent successfully!")
            print("   Response:", reset_response.json())
            print("   Check inbox:", str(settings.FIRST_SUPERUSER))
            return True
        else:
            print("❌ Password reset failed:", reset_response.status_code)
            print("   Response:", reset_response.text)
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server")
        print("   Make sure the server is running: make dev")
        return False
    except Exception as e:
        print("❌ Password reset test failed:", str(e))
        return False


def check_server_status():
    """Check if the FastAPI server is running."""
    print("🔍 Checking FastAPI Server Status...")

    base_url = "http://localhost:8001"

    try:
        response = requests.get(f"{base_url}/api/v1/utils/health-check/")
        if response.status_code == 200:
            print("✅ FastAPI server is running")
            return True
        else:
            print("❌ Server health check failed:", response.status_code)
            return False
    except requests.exceptions.ConnectionError:
        print("❌ FastAPI server is not running")
        print("\n💡 To start the server, run: make dev")
        return False
    except Exception as e:
        print("❌ Server check failed:", str(e))
        return False


def main():
    """Run email integration tests."""
    print("🌐 Email Integration Testing via FastAPI")
    print("==================================================")
    print("This test sends emails through actual API endpoints")
    print("")

    # Check server status first
    if not check_server_status():
        print("\n❌ Cannot proceed without running server")
        return False

    # Check email configuration
    if not settings.emails_enabled:
        print("\n❌ Email is not enabled in configuration")
        print("   Please configure SMTP settings in .env file")
        return False

    print("\n📧 Email configuration:")
    print("   SMTP Host:", settings.SMTP_HOST)
    print("   From Email:", settings.EMAILS_FROM_EMAIL)
    print("   Emails Enabled:", settings.emails_enabled)

    # Get user confirmation
    try:
        confirm = (
            input("\nContinue with integration email testing? (y/N): ").strip().lower()
        )
        if confirm not in ["y", "yes"]:
            print("Integration testing cancelled.")
            return True
    except KeyboardInterrupt:
        print("\nIntegration testing cancelled.")
        return True

    print("")

    # Run integration tests
    tests_passed = 0
    total_tests = 2

    if test_email_endpoint_with_admin():
        tests_passed += 1

    if test_password_reset_flow():
        tests_passed += 1

    print("\n📊 Integration Test Results:")
    print("==============================")
    print("✅ Tests passed: {}/{}".format(tests_passed, total_tests))

    if tests_passed == total_tests:
        print("🎉 All integration tests passed!")
        print("\n💡 Your email system is fully integrated!")
        print("   - FastAPI server is running correctly")
        print("   - Email endpoints are functional")
        print("   - Authentication flow works")
        print("   - Email delivery is working")
    else:
        print("⚠️  Some tests failed: {} issues".format(total_tests - tests_passed))
        print("\n🔧 Check:")
        print("   - FastAPI server is running (make dev)")
        print("   - Email configuration is correct")
        print("   - Admin user exists in database")
        print("   - SMTP credentials are valid")

    return tests_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
