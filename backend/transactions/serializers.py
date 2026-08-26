from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Category, Transaction

User = get_user_model()

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

    def validate(self, attrs):
        category = attrs.get("category")

        if category:
            transaction_type = attrs.get(
                "type",
                getattr(self.instance, "type", None),
            )

            if transaction_type != category.type:
                raise serializers.ValidationError(
                    {
                        "type": (
                            "Typ transakcji musi być zgodny "
                            "z typem kategorii."
                        )
                    }
                )

        return attrs

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )

class FinancialSummarySerializer(serializers.Serializer):
    income = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    expenses = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )