from decimal import Decimal

from django.db.models import Sum

from .models import Transaction


def get_financial_summary(user, date_from=None, date_to=None):
    transactions = Transaction.objects.filter(
        user=user,
    )

    if date_from:
        transactions = transactions.filter(
            date__gte=date_from,
        )

    if date_to:
        transactions = transactions.filter(
            date__lte=date_to,
        )

    income = transactions.filter(
        type=Transaction.TransactionType.INCOME,
    ).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    expense = transactions.filter(
        type=Transaction.TransactionType.EXPENSE,
    ).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    return {
        "income": income,
        "expenses": expense,
        "balance": income - expense,
    }