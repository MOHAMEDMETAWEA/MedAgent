import os
import sys
import time
import unittest
import uuid

from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.append("d:\\MedAgent")

from api.main import app


class TestMedAgentAuthFlow(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.username = f"testuser_{uuid.uuid4().hex[:8]}"
        self.password = "SecurePass123!"
        self.email = f"{self.username}@example.com"
        self.phone = f"1234{uuid.uuid4().hex[:6]}"

    def test_full_auth_cycle(self):
        """Test registration -> login -> profile -> delete account."""
        # 1. Register
        reg_payload = {
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "password": self.password,
            "full_name": "Test User",
            "role": "patient",
        }
        response = self.client.post("/auth/register", json=reg_payload)
        self.assertEqual(
            response.status_code, 200, f"Registration failed: {response.text}"
        )

        # 2. Login
        login_payload = {"login_id": self.username, "password": self.password}
        response = self.client.post("/auth/login", json=login_payload)
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Get /auth/me
        response = self.client.get("/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], self.username)

        # 4. Delete Account
        response = self.client.delete("/auth/account", headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_concurrent_sessions(self):
        """Simulate multiple users logging in."""
        for i in range(5):
            u = f"user_{i}_{uuid.uuid4().hex[:4]}"
            p = "pass123!"
            e = f"{u}@test.com"
            ph = f"555{uuid.uuid4().hex[:4]}"

            # Register
            self.client.post(
                "/auth/register",
                json={
                    "username": u,
                    "email": e,
                    "phone": ph,
                    "password": p,
                    "full_name": u,
                },
            )

            # Login
            resp = self.client.post("/auth/login", json={"login_id": u, "password": p})
            self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
