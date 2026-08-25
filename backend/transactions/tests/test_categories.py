from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from transactions.models import Category

User = get_user_model()


class CategoryIsolationTests(APITestCase):

    def setUp(self):
        self.user_a = User.objects.create_user(
            username="user_a",
            password="strongpassword123",
        )

        self.user_b = User.objects.create_user(
            username="user_b",
            password="strongpassword123",
        )

        self.category_a = Category.objects.create(
            user=self.user_a,
            name="Jedzenie",
            type="expense",
        )

        self.category_b = Category.objects.create(
            user=self.user_b,
            name="Transport",
            type="expense",
        )

    def authenticate(self, user):
        response = self.client.post(
            "/api/auth/token/",
            {
                "username": user.username,
                "password": "strongpassword123",
            },
            format="json",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )

    def test_user_sees_only_own_categories(self):
        self.authenticate(self.user_a)

        response = self.client.get("/api/categories/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        category_ids = [
            category["id"]
            for category in response.data
        ]

        self.assertIn(self.category_a.id, category_ids)
        self.assertNotIn(self.category_b.id, category_ids)

    def test_user_can_create_category(self):
        self.authenticate(self.user_a)

        response = self.client.post(
            "/api/categories/",
            {
                "name": "Rozrywka",
                "type": "EXPENSE",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        category = Category.objects.get(
            name="Rozrywka"
        )

        self.assertEqual(
            category.user,
            self.user_a,
        )

    def test_user_cannot_modify_other_users_category(self):
        self.authenticate(self.user_a)

        response = self.client.patch(
            f"/api/categories/{self.category_b.id}/",
            {
                "name": "Zmieniona kategoria",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.category_b.refresh_from_db()

        self.assertEqual(
            self.category_b.name,
            "Transport",
        )

    def test_user_cannot_delete_other_users_category(self):
        self.authenticate(self.user_a)

        response = self.client.delete(
            f"/api/categories/{self.category_b.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            Category.objects.filter(
                id=self.category_b.id
            ).exists()
        )