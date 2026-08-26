from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from transactions.models import Category, Transaction
from transactions.services import get_financial_summary


class FinancialSummaryTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="tomasz",
            password="qwerty1234",
        )

        self.other_user = User.objects.create_user(
            username="jan",
            password="qwerty1234",
        )

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
            type=Category.TransactionType.EXPENSE,
        )

    def test_summary_calculates_income_expense_and_balance(self):
        Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            amount=Decimal("5000.00"),
            type=Transaction.TransactionType.INCOME,
            date=date(2026, 8, 1),
        )

        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount=Decimal("1200.00"),
            type=Transaction.TransactionType.EXPENSE,
            date=date(2026, 8, 5),
        )

        summary = get_financial_summary(self.user)

        self.assertEqual(
            summary["income"],
            Decimal("5000.00"),
        )

        self.assertEqual(
            summary["expenses"],
            Decimal("1200.00"),
        )

        self.assertEqual(
            summary["balance"],
            Decimal("3800.00"),
        )

    def test_summary_returns_zero_when_no_transactions(self):
        summary = get_financial_summary(self.user)

        self.assertEqual(
            summary["income"],
            Decimal("0.00"),
        )

        self.assertEqual(
            summary["expenses"],
            Decimal("0.00"),
        )

        self.assertEqual(
            summary["balance"],
            Decimal("0.00"),
        )

    def test_summary_ignores_other_users_transactions(self):
        Transaction.objects.create(
            user=self.other_user,
            category=self.other_category,
            amount=Decimal("9999.00"),
            type=Transaction.TransactionType.EXPENSE,
            date=date(2026, 8, 1),
        )

        summary = get_financial_summary(self.user)

        self.assertEqual(
            summary["income"],
            Decimal("0.00"),
        )

        self.assertEqual(
            summary["expenses"],
            Decimal("0.00"),
        )

        self.assertEqual(
            summary["balance"],
            Decimal("0.00"),
        )

    def test_summary_filters_by_date(self):
        Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            amount=Decimal("5000.00"),
            type=Transaction.TransactionType.INCOME,
            date=date(2026, 8, 1),
        )

        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount=Decimal("1000.00"),
            type=Transaction.TransactionType.EXPENSE,
            date=date(2026, 8, 20),
        )

        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            amount=Decimal("500.00"),
            type=Transaction.TransactionType.EXPENSE,
            date=date(2026, 9, 1),
        )

        summary = get_financial_summary(
            self.user,
            date_from=date(2026, 8, 1),
            date_to=date(2026, 8, 31),
        )

        self.assertEqual(
            summary["income"],
            Decimal("5000.00"),
        )

        self.assertEqual(
            summary["expenses"],
            Decimal("1000.00"),
        )

        self.assertEqual(
            summary["balance"],
            Decimal("4000.00"),
        )