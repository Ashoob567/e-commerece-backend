from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_user(self):
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post("/api/auth/register/", payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="login@example.com",
            password="testpass123",
            first_name="Login",
            last_name="User",
        )

    def test_login_user(self):
        payload = {
            "email": "login@example.com",
            "password": "testpass123",
        }
        response = self.client.post("/api/auth/login/", payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


class MeViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="me@example.com",
            password="testpass123",
            first_name="Me",
            last_name="User",
        )
        login_response = self.client.post(
            "/api/auth/login/",
            {"email": "me@example.com", "password": "testpass123"},
        )
        self.access_token = login_response.data["access"]

    def test_get_profile_with_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], self.user.email)
