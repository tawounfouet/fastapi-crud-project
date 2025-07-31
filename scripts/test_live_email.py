#!/usr/bin/env python3
"""
Live Email Testing Script

This script sends actual test emails to verify SMTP configuration is working.
Use this after configuring SMTP settings to test real email delivery.

⚠️  WARNING: This script sends real emails! Use with caution.
"""

import sys
from pathlib import Path

# Add src to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

try:
    from src.utils import (
        generate_test_email,
        generate_reset_password_email,
        generate_new_account_email,
        send_email,
    )
    from src.utils.auth import generate_password_reset_token
    from src.core.config import settings

    print("✅ Successfully imported email utilities")
except ImportError as e:
    print(f"❌ Failed to import utilities: {e}")
    sys.exit(1)


def send_test_email_to_self():
    """Send a test email to the configured sender email."""
    print("\\n🧪 Testing Live Email Sending...")

    if not settings.emails_enabled:
        print("❌ Email is not enabled. Please configure SMTP settings.")
        return False

    try:
        # Generate test email
        test_email_data = generate_test_email(settings.EMAILS_FROM_EMAIL)

        print(f"📧 Sending test email to: {settings.EMAILS_FROM_EMAIL}")
        print(f"📋 Subject: {test_email_data.subject}")

        # Actually send the email
        send_email(
            email_to=settings.EMAILS_FROM_EMAIL,
            subject=test_email_data.subject,
            html_content=test_email_data.html_content,
        )

        print("✅ Test email sent successfully!")
        print(f"   Check your inbox at: {settings.EMAILS_FROM_EMAIL}")
        print("   Note: Check spam folder if you don't see it in inbox")
        return True

    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        print("   Common issues:")
        print("   - Incorrect SMTP credentials")
        print("   - Gmail requires App Password (not regular password)")
        print("   - SMTP server blocking connection")
        print("   - Firewall blocking SMTP port")
        return False


def send_password_reset_email_test():
    """Send a password reset email test."""
    print("\\n🔐 Testing Password Reset Email...")

    if not settings.emails_enabled:
        print("❌ Email is not enabled. Skipping password reset test.")
        return False

    try:
        # Generate a real password reset token
        test_email = settings.EMAILS_FROM_EMAIL
        reset_token = generate_password_reset_token(test_email)

        # Generate password reset email
        reset_email_data = generate_reset_password_email(
            email_to=test_email, email=test_email, token=reset_token
        )

        print(f"📧 Sending password reset email to: {test_email}")
        print(f"📋 Subject: {reset_email_data.subject}")

        # Send the email
        send_email(
            email_to=test_email,
            subject=reset_email_data.subject,
            html_content=reset_email_data.html_content,
        )

        print("✅ Password reset email sent successfully!")
        print("   Check your inbox for the password reset email")
        print("   Note: The reset link is real and functional")
        return True

    except Exception as e:
        print(f"❌ Failed to send password reset email: {e}")
        return False


def send_welcome_email_test():
    """Send a new account welcome email test."""
    print("\\n👋 Testing Welcome Email...")

    if not settings.emails_enabled:
        print("❌ Email is not enabled. Skipping welcome email test.")
        return False

    try:
        test_email = settings.EMAILS_FROM_EMAIL

        # Generate welcome email
        welcome_email_data = generate_new_account_email(
            email_to=test_email, username="testuser", password="temporary-password-123"
        )

        print(f"📧 Sending welcome email to: {test_email}")
        print(f"📋 Subject: {welcome_email_data.subject}")

        # Send the email
        send_email(
            email_to=test_email,
            subject=welcome_email_data.subject,
            html_content=welcome_email_data.html_content,
        )

        print("✅ Welcome email sent successfully!")
        print("   Check your inbox for the welcome email")
        return True

    except Exception as e:
        print(f"❌ Failed to send welcome email: {e}")
        return False


def verify_smtp_configuration():
    """Verify SMTP configuration before testing."""
    print("🔍 Verifying SMTP Configuration...")

    config_issues = []

    if not settings.SMTP_HOST:
        config_issues.append("SMTP_HOST not configured")

    if not settings.SMTP_USER:
        config_issues.append("SMTP_USER not configured")

    if not settings.SMTP_PASSWORD:
        config_issues.append("SMTP_PASSWORD not configured")

    if not settings.EMAILS_FROM_EMAIL:
        config_issues.append("EMAILS_FROM_EMAIL not configured")

    if config_issues:
        print("❌ SMTP Configuration Issues:")
        for issue in config_issues:
            print(f"   - {issue}")
        print("\\n💡 Please configure these settings in your .env file:")
        print("   SMTP_HOST=smtp.gmail.com")
        print("   SMTP_USER=your-email@gmail.com")
        print("   SMTP_PASSWORD=your-app-password")
        print("   EMAILS_FROM_EMAIL=your-email@gmail.com")
        return False

    print("✅ SMTP Configuration looks good")
    print(f"   Host: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
    print(f"   User: {settings.SMTP_USER}")
    print(f"   From: {settings.EMAILS_FROM_EMAIL}")
    print(f"   TLS: {settings.SMTP_TLS}")
    return True


def main():
    """Run live email tests."""
    print("🎯 Live Email Testing Suite")
    print("==================================================")
    print("⚠️  WARNING: This script sends real emails!")
    print("   Make sure you want to test with real email delivery")
    print("")

    # Get user confirmation
    try:
        confirm = input("Continue with live email testing? (y/N): ").strip().lower()
        if confirm not in ["y", "yes"]:
            print("Email testing cancelled.")
            return True
    except KeyboardInterrupt:
        print("\\nEmail testing cancelled.")
        return True

    print("")

    # Verify configuration
    if not verify_smtp_configuration():
        return False

    print("")

    # Run tests
    tests_passed = 0
    total_tests = 3

    if send_test_email_to_self():
        tests_passed += 1

    if send_password_reset_email_test():
        tests_passed += 1

    if send_welcome_email_test():
        tests_passed += 1

    print("\\n📊 Live Email Test Results:")
    print("==============================")
    print(f"✅ Tests passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("🎉 All email tests passed!")
        print("\\n💡 Your email system is working correctly!")
        print("   - SMTP configuration is valid")
        print("   - Email templates render properly")
        print("   - Email delivery is functional")
    else:
        print(f"⚠️  Some tests failed: {total_tests - tests_passed} issues")
        print("\\n🔧 Troubleshooting tips:")
        print("   - Check Gmail App Password (not regular password)")
        print("   - Verify SMTP credentials in .env file")
        print("   - Check internet connection")
        print("   - Review email provider settings")

    return tests_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
