from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from transactions.models import Category, Transaction


class TransactionIsolationTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="tomasz",
            password="qwerty1234",
        )

        self.other_user = User.objects.create_user(
            username="jan",
            password="qwerty1234",
        )

        self.category = Category.objects.create(
            user=self.user,
            name="Jedzenie",
            type=Category.TransactionType.EXPENSE,
        )

        self.other_category = Category.objects.create(
            user=self.other_user,
            name="Transport",
            type=Category.TransactionType.EXPENSE,
        )

        self.transaction = Transaction.objects.create(
            user=self.user,
            category=self.category,
            amount=Decimal("50.00"),
            type=Transaction.TransactionType.EXPENSE,
            date=date(2026, 8, 25),
            description="Obiad",
        )

        self.other_transaction = Transaction.objects.create(
            user=self.other_user,
            category=self.other_category,
            amount=Decimal("100.00"),
            type=Transaction.TransactionType.EXPENSE,
            date=date(2026, 8, 25),
            description="Paliwo",
        )

        self.client.force_authenticate(user=self.user)

    def test_user_sees_only_own_transactions(self):
        response = self.client.get("/api/transactions/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        transaction_ids = [
            transaction["id"]
            for transaction in response.data
        ]

        self.assertIn(self.transaction.id, transaction_ids)
        self.assertNotIn(self.other_transaction.id, transaction_ids)

    def test_user_can_create_transaction(self):
        data = {
            "category": self.category.id,
            "amount": "25.50",
            "type": "EXPENSE",
            "date": "2026-08-25",
            "description": "Kawa",
        }

        response = self.client.post(
            "/api/transactions/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        transaction = Transaction.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.amount, Decimal("25.50"))

    def test_user_cannot_use_other_users_category(self):
        data = {
            "category": self.other_category.id,
            "amount": "25.50",
            "type": "EXPENSE",
            "date": "2026-08-25",
            "description": "Test",
        }

        response = self.client.post(
            "/api/transactions/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_user_can_update_own_transaction(self):
        data = {
            "category": self.category.id,
            "amount": "75.00",
            "type": "EXPENSE",
            "date": "2026-08-25",
            "description": "Zmieniony opis",
        }

        response = self.client.put(
            f"/api/transactions/{self.transaction.id}/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.transaction.refresh_from_db()

        self.assertEqual(
            self.transaction.amount,
            Decimal("75.00"),
        )

    def test_user_cannot_access_other_users_transaction(self):
        response = self.client.get(
            f"/api/transactions/{self.other_transaction.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_user_cannot_update_other_users_transaction(self):
        data = {
            "category": self.category.id,
            "amount": "999.00",
            "type": "EXPENSE",
            "date": "2026-08-25",
            "description": "Hacked",
        }

        response = self.client.put(
            f"/api/transactions/{self.other_transaction.id}/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_user_cannot_delete_other_users_transaction(self):
        response = self.client.delete(
            f"/api/transactions/{self.other_transaction.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            Transaction.objects.filter(
                id=self.other_transaction.id
            ).exists()
        )

    def test_transaction_type_must_match_category_type(self):
        data = {
            "category": self.category.id,
            "amount": "25.50",
            "type": "INCOME",
            "date": "2026-08-25",
            "description": "Błędny typ",
        }

        response = self.client.post(
            "/api/transactions/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn("type", response.data)