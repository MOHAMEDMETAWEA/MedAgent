"""
Multi-User Registration Unit Test — verifies the auth bug fix.
Tests that multiple users can register and login without server running.
"""

import os
import sys

# Set env vars before any imports
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-testing-12345")
os.environ.setdefault("DATA_ENCRYPTION_KEY", "")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.authentication_agent import AuthenticationAgent
from agents.persistence_agent import PersistenceAgent


def test_multi_user_registration():
    """Test that multiple users can register sequentially."""
    pers = PersistenceAgent()

    users_created = []
    for i in range(5):
        uid = pers.register_user(
            username=f"testuser_{i}_{os.getpid()}",
            email=f"test_{i}_{os.getpid()}@example.com",
            phone=f"+1000000{i}{os.getpid()}",
            password=f"StrongPass{i}!",
            full_name=f"Test User {i}",
            role="patient",
            gender="Male",
            age=25 + i,
            country="TestLand",
        )
        assert uid is not None, f"User {i} registration failed (returned None)"
        users_created.append(uid)
        print(f"  ✅ User {i} registered: {uid}")

    assert len(set(users_created)) == 5, "Not all user IDs are unique"
    print(f"  ✅ All 5 users registered with unique IDs")


def test_duplicate_registration():
    """Test that duplicate usernames are rejected."""
    pers = PersistenceAgent()

    unique = f"dup_{os.getpid()}"
    uid1 = pers.register_user(
        username=unique,
        email=f"{unique}@example.com",
        phone=f"+1{unique}",
        password="Pass1!",
        full_name="Dup Test",
        role="patient",
    )
    assert uid1 is not None, "First registration should succeed"

    uid2 = pers.register_user(
        username=unique,
        email=f"{unique}_2@example.com",
        phone=f"+2{unique}",
        password="Pass2!",
        full_name="Dup Test 2",
        role="patient",
    )
    assert uid2 is None, "Duplicate username registration should fail"
    print("  ✅ Duplicate registration correctly rejected")


def test_multi_user_login():
    """Test that multiple registered users can all login."""
    auth = AuthenticationAgent()

    users = []
    for i in range(3):
        pid = os.getpid()
        un = f"logintest_{i}_{pid}"
        em = f"login_{i}_{pid}@example.com"
        pw = f"LoginPass{i}!"

        uid = auth.persistence.register_user(
            username=un,
            email=em,
            phone=f"+3{i}{pid}",
            password=pw,
            full_name=f"Login User {i}",
            role="patient",
        )
        assert uid is not None, f"Registration of login user {i} failed"
        users.append((em, pw))

    # Now login each
    for i, (em, pw) in enumerate(users):
        result, error = auth.validate_login(em, pw, ip="127.0.0.1")
        assert error is None, f"Login for user {i} failed: {error}"
        assert result is not None, f"Login for user {i} returned None result"
        assert "token" in result, f"Login for user {i} missing token"
        print(f"  ✅ User {i} logged in successfully")


def test_session_isolation():
    """Test that different users get different session IDs and tokens."""
    auth = AuthenticationAgent()

    sessions = []
    for i in range(2):
        pid = os.getpid()
        un = f"session_{i}_{pid}"
        auth.persistence.register_user(
            username=un,
            email=f"s_{i}_{pid}@ex.com",
            phone=f"+4{i}{pid}",
            password=f"SessPass{i}!",
            full_name=f"Sess User {i}",
            role="patient",
        )
        result, _ = auth.validate_login(un, f"SessPass{i}!", ip="127.0.0.1")
        sessions.append(result)

    assert (
        sessions[0]["session_id"] != sessions[1]["session_id"]
    ), "Session IDs should differ"
    assert sessions[0]["token"] != sessions[1]["token"], "Tokens should differ"
    print("  ✅ Sessions are properly isolated")


if __name__ == "__main__":
    print("\n=== Multi-User Registration Unit Test ===\n")

    print("[1] Testing multi-user registration...")
    test_multi_user_registration()

    print("\n[2] Testing duplicate registration rejection...")
    test_duplicate_registration()

    print("\n[3] Testing multi-user login...")
    test_multi_user_login()

    print("\n[4] Testing session isolation...")
    test_session_isolation()

    print("\n=== ALL TESTS PASSED ✅ ===")
