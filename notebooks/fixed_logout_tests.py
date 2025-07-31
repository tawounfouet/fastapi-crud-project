# Fixed logout test function with proper JSON body
def test_logout_fixed():
    global access_token, refresh_token

    if not access_token:
        print("❌ No access token available. Please run login first.")
        return None

    url = f"{AUTH_URL}/logout"
    headers = {"Authorization": f"Bearer {access_token}"}

    # FIXED: Send proper JSON body with LogoutRequest schema
    logout_data = {"all_devices": False}  # Set to True to logout from all devices

    response = requests.post(url, headers=headers, json=logout_data)

    print(f"POST {url}")
    print(f"Request Body: {logout_data}")
    print(f"Status Code: {response.status_code}")

    try:
        data = response.json()
    except Exception as e:
        print(f"Could not parse JSON: {e}")
        print(f"Raw response text: {response.text}")
        data = None

    if response.status_code == 200:
        print("✅ Logout successful!")
        print(f"Response: {data}")
        access_token = None
        refresh_token = None
        return data
    else:
        print("❌ Logout failed!")
        print(f"Error: {data}")
        return None


# Also fix the complete test suite logout test
def run_complete_auth_test_suite_fixed():
    print("🧪 Running Complete Authentication Test Suite (FIXED)")
    print("=" * 50)

    results = {"timestamp": datetime.now().isoformat(), "tests": {}}

    # Create new test user for complete suite
    suite_user = {
        "email": f"suite_test_{int(time.time())}@example.com",
        "password": "SuiteTestPassword123!",
        "first_name": "Suite",
        "last_name": "Test",
    }

    # 1. Signup
    print("\n1. Testing Signup...")
    signup_response = requests.post(f"{AUTH_URL}/signup", json=suite_user)
    results["tests"]["signup"] = {
        "status_code": signup_response.status_code,
        "success": signup_response.status_code == 201,
    }
    print(
        f"   Result: {'✅ PASS' if results['tests']['signup']['success'] else '❌ FAIL'}"
    )

    # 2. Login
    print("\n2. Testing Login...")
    login_data = {"username": suite_user["email"], "password": suite_user["password"]}
    login_response = requests.post(f"{AUTH_URL}/login/access-token", data=login_data)
    results["tests"]["login"] = {
        "status_code": login_response.status_code,
        "success": login_response.status_code == 200,
    }
    print(
        f"   Result: {'✅ PASS' if results['tests']['login']['success'] else '❌ FAIL'}"
    )

    # Get token for subsequent tests
    if results["tests"]["login"]["success"]:
        token_data = login_response.json()
        suite_token = token_data.get("access_token")
        headers = {"Authorization": f"Bearer {suite_token}"}

        # 3. Token validation
        print("\n3. Testing Token Validation...")
        token_response = requests.post(f"{AUTH_URL}/test-token", headers=headers)
        results["tests"]["token_validation"] = {
            "status_code": token_response.status_code,
            "success": token_response.status_code == 200,
        }
        print(
            f"   Result: {'✅ PASS' if results['tests']['token_validation']['success'] else '❌ FAIL'}"
        )

        # 4. Logout (FIXED with proper JSON body)
        print("\n4. Testing Logout...")
        logout_data = {"all_devices": False}
        logout_response = requests.post(
            f"{AUTH_URL}/logout", headers=headers, json=logout_data
        )
        results["tests"]["logout"] = {
            "status_code": logout_response.status_code,
            "success": logout_response.status_code == 200,
        }
        print(
            f"   Result: {'✅ PASS' if results['tests']['logout']['success'] else '❌ FAIL'}"
        )

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    total_tests = len(results["tests"])
    passed_tests = sum(1 for test in results["tests"].values() if test["success"])

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    return results


print("🔧 Fixed logout functions created!")
print(
    "📝 Use test_logout_fixed() and run_complete_auth_test_suite_fixed() for proper testing"
)
