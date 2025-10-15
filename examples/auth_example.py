#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Authentication system example for SwanLab-Server

This example demonstrates how to:
1. Register a new account
2. Login with email and password
3. Get user information
4. Refresh access token
5. Logout
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:22224/api/v1"  # Change to your server URL


class SwanLabAuthClient:
    """Simple client for SwanLab authentication"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None

    def register(self, email: str, password: str, name: str):
        """Register a new account"""
        url = f"{self.base_url}/auth/register"
        data = {
            "email": email,
            "password": password,
            "name": name
        }

        response = requests.post(url, json=data)
        response.raise_for_status()

        result = response.json()
        self.access_token = result["access_token"]
        self.refresh_token = result["refresh_token"]

        print(f"✓ Registered successfully: {email}")
        return result

    def login(self, email: str, password: str):
        """Login with email and password"""
        url = f"{self.base_url}/auth/login"
        data = {
            "email": email,
            "password": password
        }

        response = requests.post(url, json=data)
        response.raise_for_status()

        result = response.json()
        self.access_token = result["access_token"]
        self.refresh_token = result["refresh_token"]

        print(f"✓ Logged in successfully: {email}")
        return result

    def get_profile(self):
        """Get current user profile"""
        if not self.access_token:
            raise ValueError("Not authenticated. Please login first.")

        url = f"{self.base_url}/auth/me"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        result = response.json()
        print(f"✓ Profile retrieved: {result['name']} ({result['email']})")
        return result

    def refresh(self):
        """Refresh access token"""
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        url = f"{self.base_url}/auth/refresh"
        data = {"refresh_token": self.refresh_token}

        response = requests.post(url, json=data)
        response.raise_for_status()

        result = response.json()
        self.access_token = result["access_token"]

        print("✓ Token refreshed successfully")
        return result

    def logout(self):
        """Logout (revoke refresh token)"""
        if not self.access_token or not self.refresh_token:
            raise ValueError("Not authenticated")

        url = f"{self.base_url}/auth/logout"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        data = {"refresh_token": self.refresh_token}

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        self.access_token = None
        self.refresh_token = None

        print("✓ Logged out successfully")
        return result


def main():
    """Main example function"""
    print("SwanLab Authentication Example")
    print("=" * 50)

    client = SwanLabAuthClient()

    try:
        # Example 1: Register a new account
        print("\n1. Registering new account...")
        client.register(
            email="test@example.com",
            password="test_password_123",
            name="Test User"
        )

        # Example 2: Get user profile
        print("\n2. Getting user profile...")
        profile = client.get_profile()
        print(f"   User ID: {profile['id']}")
        print(f"   Email: {profile['email']}")
        print(f"   Name: {profile['name']}")
        print(f"   Status: {profile['status']}")

        # Example 3: Refresh token
        print("\n3. Refreshing access token...")
        client.refresh()

        # Example 4: Logout
        print("\n4. Logging out...")
        client.logout()

        # Example 5: Login again
        print("\n5. Logging in again...")
        client.login(
            email="test@example.com",
            password="test_password_123"
        )

        # Example 6: Get profile again
        print("\n6. Getting profile after re-login...")
        profile = client.get_profile()

        print("\n" + "=" * 50)
        print("✓ All examples completed successfully!")

    except requests.exceptions.HTTPError as e:
        print(f"\n✗ HTTP Error: {e}")
        if e.response is not None:
            print(f"  Status: {e.response.status_code}")
            try:
                print(f"  Detail: {e.response.json()}")
            except:
                print(f"  Response: {e.response.text}")

    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()