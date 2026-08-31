from datetime import date, timedelta
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

class SummaryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="summary_user",
            password="testpassword123",
        )

        self.other_user = User.objects.create_user(
            username="other_summary_user",
            password="testpassword123",
        )

        self.client.force_authenticate(user=self.user)

        self.income_category = Category.objects.create(
            user=self.user,
            name="Wynagrodzenie",
            type=Category.TransactionType.INCOME,
        )

        self.expense_category = Category.objects.create(
            user=self.user,
            name="Jedzenie",
            type=Category.TransactionType.EXPENSE,
        )

        self.other_category = Category.objects.create(
            user=self.other_user,
            name="Inne",
            type=Category.TransactionType.INCOME,
        )

    def create_transaction(
        self,
        category,
        amount,
        transaction_type,
        transaction_date,
        description="",
        user=None,
    ):
        return Transaction.objects.create(
            user=user or self.user,
            category=category,
            amount=Decimal(str(amount)),
            type=transaction_type,
            date=transaction_date,
            description=description,
        )

    def test_summary_returns_correct_totals(self):
        self.create_transaction(
            self.income_category,
            "5000.00",
            Transaction.TransactionType.INCOME,
            date(2026, 1, 10),
        )

        self.create_transaction(
            self.expense_category,
            "150.00",
            Transaction.TransactionType.EXPENSE,
            date(2026, 1, 11),
        )

        self.create_transaction(
            self.expense_category,
            "350.00",
            Transaction.TransactionType.EXPENSE,
            date(2026, 1, 12),
        )

        response = self.client.get(
            "/api/summary/?date_from=2026-01-01&date_to=2026-01-31"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["income"], "5000.00")
        self.assertEqual(response.data["expenses"], "500.00")
        self.assertEqual(response.data["balance"], "4500.00")

    def test_summary_filters_by_date(self):
        self.create_transaction(
            self.income_category,
            "5000.00",
            Transaction.TransactionType.INCOME,
            date(2026, 1, 10),
        )

        self.create_transaction(
            self.expense_category,
            "200.00",
            Transaction.TransactionType.EXPENSE,
            date(2026, 2, 10),
        )

        response = self.client.get(
            "/api/summary/?date_from=2026-01-01&date_to=2026-01-31"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["income"], "5000.00")
        self.assertEqual(response.data["expenses"], "0.00")
        self.assertEqual(response.data["balance"], "5000.00")

    def test_summary_uses_only_current_users_transactions(self):
        self.create_transaction(
            self.income_category,
            "1000.00",
            Transaction.TransactionType.INCOME,
            date(2026, 1, 10),
        )

        self.create_transaction(
            self.other_category,
            "9999.00",
            Transaction.TransactionType.INCOME,
            date(2026, 1, 10),
            user=self.other_user,
        )

        response = self.client.get(
            "/api/summary/?date_from=2026-01-01&date_to=2026-01-31"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["income"], "1000.00")
        self.assertEqual(response.data["expenses"], "0.00")
        self.assertEqual(response.data["balance"], "1000.00")

    def test_summary_returns_zero_when_there_are_no_transactions(self):
        response = self.client.get(
            "/api/summary/?date_from=2026-01-01&date_to=2026-01-31"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["income"], "0.00")
        self.assertEqual(response.data["expenses"], "0.00")
        self.assertEqual(response.data["balance"], "0.00")

    def test_summary_rejects_invalid_date_from(self):
        response = self.client.get(
            "/api/summary/?date_from=abc"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "Nieprawidłowy format date_from. Użyj YYYY-MM-DD.",
        )

    def test_summary_rejects_invalid_date_to(self):
        response = self.client.get(
            "/api/summary/?date_to=abc"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "Nieprawidłowy format date_to. Użyj YYYY-MM-DD.",
        )

    def test_summary_rejects_invalid_date_range(self):
        response = self.client.get(
            "/api/summary/?date_from=2026-02-01&date_to=2026-01-01"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "date_from nie może być późniejsze niż date_to.",
        )

class TransactionFilterTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="tomasz",
            password="qwerty1234",
        )

        self.other_user = User.objects.create_user(
            username="jan",
            password="qwerty1234",
        )

        self.expense_category = Category.objects.create(
            user=self.user,
            name="Jedzenie",
            type=Category.TransactionType.EXPENSE,
        )

        self.income_category = Category.objects.create(
            user=self.user,
            name="Pensja",
            type=Category.TransactionType.INCOME,
        )

        self.other_category = Category.objects.create(
            user=self.other_user,
            name="Transport",
            type=Category.TransactionType.EXPENSE,
        )

        self.expense_transaction = Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount=Decimal("50.00"),
            type=Transaction.TransactionType.EXPENSE,
            date=date(2026, 8, 25),
            description="Obiad",
        )

        self.income_transaction = Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            amount=Decimal("3000.00"),
            type=Transaction.TransactionType.INCOME,
            date=date(2026, 8, 25),
            description="Pensja",
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

    def test_filter_transactions_by_type(self):
        response = self.client.get(
            "/api/transactions/?type=EXPENSE"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        transaction_ids = [
            transaction["id"]
            for transaction in response.data
        ]

        self.assertIn(
            self.expense_transaction.id,
            transaction_ids,
        )

        self.assertNotIn(
            self.income_transaction.id,
            transaction_ids,
        )

        self.assertNotIn(
            self.other_transaction.id,
            transaction_ids,
        )

    def test_filter_transactions_by_income_type(self):
        response = self.client.get(
            "/api/transactions/?type=INCOME"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        transaction_ids = [
            transaction["id"]
            for transaction in response.data
        ]

        self.assertIn(
            self.income_transaction.id,
            transaction_ids,
        )

        self.assertNotIn(
            self.expense_transaction.id,
            transaction_ids,
        )

        self.assertNotIn(
            self.other_transaction.id,
            transaction_ids,
        )

    def test_filter_transactions_by_category(self):
        response = self.client.get(
            f"/api/transactions/?category={self.expense_category.id}"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        transaction_ids = [
            transaction["id"]
            for transaction in response.data
        ]

        self.assertIn(
            self.expense_transaction.id,
            transaction_ids,
        )

        self.assertNotIn(
            self.income_transaction.id,
            transaction_ids,
        )

        self.assertNotIn(
            self.other_transaction.id,
            transaction_ids,
        )

    def test_combine_type_and_category_filters(self):
        response = self.client.get(
            f"/api/transactions/?type=EXPENSE&category={self.expense_category.id}"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        transaction_ids = [
            transaction["id"]
            for transaction in response.data
        ]

        self.assertEqual(
            transaction_ids,
            [self.expense_transaction.id],
        )
    def test_filter_transactions_by_date_from(self):
        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount=Decimal("20.00"),
            type=Transaction.TransactionType.EXPENSE,
            date=date(2026, 8, 20),
            description="Starsza",
        )

        response = self.client.get(
            "/api/transactions/?date_from=2026-08-25"
        )

        transaction_ids = [
            transaction["id"]
            for transaction in response.data
        ]

        self.assertIn(
            self.expense_transaction.id,
            transaction_ids,
        )

        self.assertIn(
            self.income_transaction.id,
            transaction_ids,
        )

        self.assertEqual(len(transaction_ids), 2)

    def test_filter_transactions_by_date_to(self):
        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount=Decimal("20.00"),
            type=Transaction.TransactionType.EXPENSE,
            date=date(2026, 8, 30),
            description="Nowsza",
        )

        response = self.client.get(
            "/api/transactions/?date_to=2026-08-25"
        )

        transaction_ids = [
            transaction["id"]
            for transaction in response.data
        ]

        self.assertIn(
            self.expense_transaction.id,
            transaction_ids,
        )

        self.assertIn(
            self.income_transaction.id,
            transaction_ids,
        )

        self.assertEqual(len(transaction_ids), 2)

    def test_filter_transactions_by_date_range(self):
        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount=Decimal("20.00"),
            type=Transaction.TransactionType.EXPENSE,
            date=date(2026, 8, 15),
            description="Za wcześnie",
        )

        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount=Decimal("30.00"),
            type=Transaction.TransactionType.EXPENSE,
            date=date(2026, 8, 28),
            description="Za późno",
        )

        response = self.client.get(
            "/api/transactions/?date_from=2026-08-20&date_to=2026-08-26"
        )

        transaction_ids = [
            transaction["id"]
            for transaction in response.data
        ]

        self.assertEqual(
            sorted(transaction_ids),
            sorted([
                self.expense_transaction.id,
                self.income_transaction.id,
            ]),
        )

    def test_combine_all_filters(self):
        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount=Decimal("40.00"),
            type=Transaction.TransactionType.EXPENSE,
            date=date(2026, 8, 15),
            description="Inna",
        )

        response = self.client.get(
            f"/api/transactions/?type=EXPENSE"
            f"&category={self.expense_category.id}"
            f"&date_from=2026-08-20"
            f"&date_to=2026-08-30"
        )

        transaction_ids = [
            transaction["id"]
            for transaction in response.data
        ]

        self.assertEqual(
            transaction_ids,
            [self.expense_transaction.id],
        )