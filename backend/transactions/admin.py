from django.contrib import admin
from .models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "user", "created_at")
    list_filter = ("type",)
    search_fields = ("name", "user__username")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "type",
        "category",
        "amount",
        "user",
        "description",
    )
    list_filter = ("type", "category", "date")
    search_fields = (
        "description",
        "category__name",
        "user__username",
    )
    date_hierarchy = "date"