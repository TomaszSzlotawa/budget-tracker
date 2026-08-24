from rest_framework import serializers
from .models import Category, Transaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "type",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "category",
            "amount",
            "type",
            "date",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_category(self, category):
        request = self.context["request"]

        if category.user != request.user:
            raise serializers.ValidationError(
                "Nie możesz użyć kategorii innego użytkownika."
            )

        return category