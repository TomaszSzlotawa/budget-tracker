from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthenticationTests(APITestCase):

    def test_user_can_register(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "strongpassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            User.objects.filter(username="testuser").exists()
        )

    def test_password_is_hashed(self):
        self.client.post(
            "/api/auth/register/",
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "strongpassword123",
            },
            format="json",
        )

        user = User.objects.get(username="testuser")

        self.assertNotEqual(
            user.password,
            "strongpassword123",
        )
        self.assertTrue(
            user.check_password("strongpassword123")
        )

    def test_user_can_obtain_jwt_token(self):
        User.objects.create_user(
            username="testuser",
            password="strongpassword123",
        )

        response = self.client.post(
            "/api/auth/token/",
            {
                "username": "testuser",
                "password": "strongpassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_user_can_refresh_jwt_token(self):
        User.objects.create_user(
            username="testuser",
            password="strongpassword123",
        )

        login_response = self.client.post(
            "/api/auth/token/",
            {
                "username": "testuser",
                "password": "strongpassword123",
            },
            format="json",
        )

        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            "/api/auth/token/refresh/",
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_unauthenticated_user_cannot_access_categories(self):
        response = self.client.get("/api/categories/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )