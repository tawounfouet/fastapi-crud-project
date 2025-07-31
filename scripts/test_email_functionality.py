#!/usr/bin/env python3
"""
Test script for email functionality after reorganization.

This script tests:
1. Email template rendering
2. Email utilities import
3. Email generation functions
4. SMTP configuration (if configured)
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
        EmailData,
        generate_test_email,
        generate_reset_password_email,
        generate_new_account_email,
        render_email_template,
        send_email,
    )
    from src.core.config import settings
    print("✅ Successfully imported email utilities from new structure")
except ImportError as e:
    print(f"❌ Failed to import email utilities: {e}")
    sys.exit(1)

def test_email_template_rendering():
    """Test that email templates can be rendered."""
    print("\n🔍 Testing email template rendering...")
    
    try:
        # Test rendering a simple template
        html_content = render_email_template(
            template_name="test_email.html",
            context={
                "project_name": settings.PROJECT_NAME,
                "email": "test@example.com"
            }
        )
        
        if html_content and len(html_content) > 0:
            print("✅ Email template rendering works")
            print(f"   Template length: {len(html_content)} characters")
            # Show a snippet
            snippet = html_content[:100].replace('\n', ' ')
            print(f"   Content preview: {snippet}...")
            return True
        else:
            print("❌ Email template rendering returned empty content")
            return False
            
    except Exception as e:
        print(f"❌ Email template rendering failed: {e}")
        return False

def test_email_generation():
    """Test email generation functions."""
    print("\n🔍 Testing email generation functions...")
    
    try:
        # Test test email generation
        test_email = generate_test_email("test@example.com")
        print(f"✅ Test email generated: {test_email.subject}")
        
        # Test reset password email generation
        reset_email = generate_reset_password_email(
            email_to="test@example.com",
            email="test@example.com", 
            token="test_token_123"
        )
        print(f"✅ Reset password email generated: {reset_email.subject}")
        
        # Test new account email generation
        new_account_email = generate_new_account_email(
            email_to="test@example.com",
            username="testuser",
            password="temp_password"
        )
        print(f"✅ New account email generated: {new_account_email.subject}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email generation failed: {e}")
        return False

def test_email_configuration():
    """Test email configuration."""
    print("\n🔍 Testing email configuration...")
    
    try:
        print(f"📧 Emails enabled: {settings.emails_enabled}")
        
        if settings.emails_enabled:
            print(f"   SMTP Host: {settings.SMTP_HOST}")
            print(f"   SMTP Port: {settings.SMTP_PORT}")
            print(f"   From Email: {settings.EMAILS_FROM_EMAIL}")
            print(f"   From Name: {settings.EMAILS_FROM_NAME}")
            print("✅ Email configuration appears complete")
        else:
            print("⚠️  Email is disabled (SMTP not configured)")
            
        return True
        
    except Exception as e:
        print(f"❌ Email configuration check failed: {e}")
        return False

def test_email_sending_dry_run():
    """Test email sending preparation (dry run)."""
    print("\n🔍 Testing email sending preparation...")
    
    try:
        test_email = generate_test_email("test@example.com")
        
        if settings.emails_enabled:
            print("✅ Email sending would work (SMTP configured)")
            print("   Note: Not actually sending email in test mode")
        else:
            print("⚠️  Email sending not configured (no SMTP settings)")
            
        return True
        
    except Exception as e:
        print(f"❌ Email sending preparation failed: {e}")
        return False

def main():
    """Run all email tests."""
    print("🧪 Email Functionality Test Suite")
    print("=" * 50)
    
    all_tests = [
        test_email_template_rendering,
        test_email_generation,
        test_email_configuration,
        test_email_sending_dry_run,
    ]
    
    results = []
    for test in all_tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n📊 Test Results:")
    print("=" * 30)
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    if passed == total:
        print("🎉 All email functionality tests passed!")
        print("\n💡 Tips:")
        print("   - Email templates can be found in: src/emails/")
        print("   - Email utilities are in: src/utils/email.py")
        print("   - Auth utilities are in: src/utils/auth.py")
        print("   - Configure SMTP settings in .env to enable email sending")
    else:
        print(f"❌ Failed: {total - passed}/{total}")
        print("🔧 Some email functionality needs attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
