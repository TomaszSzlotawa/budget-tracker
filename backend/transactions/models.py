from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = "INCOME", "Wpływ"
        EXPENSE = "EXPENSE", "Wydatek"

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="categories"
    )
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=20,
        choices=TransactionType.choices
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name", "type"],
                name="unique_category_per_userand_type"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = "INCOME", "Wpływ"
        EXPENSE = "EXPENSE", "Wydatek"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )
    date = models.DateField()
    description = models.CharField(
        max_length=255,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.amount} zł - {self.category.name}"