from datetime import date

from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Transaction
from .serializers import CategorySerializer, TransactionSerializer, RegisterSerializer, FinancialSummarySerializer
from .services import get_financial_summary


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(
            user=self.request.user
        ).select_related("category")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class FinancialSummaryView(APIView):

    def get(self, request):
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        if date_from:
            try:
                date_from = date.fromisoformat(date_from)
            except ValueError:
                return Response(
                    {"detail": "Nieprawidłowy format date_from. Użyj YYYY-MM-DD."},
                    status=400,
                )

        if date_to:
            try:
                date_to = date.fromisoformat(date_to)
            except ValueError:
                return Response(
                    {"detail": "Nieprawidłowy format date_to. Użyj YYYY-MM-DD."},
                    status=400,
                )

        if date_from and date_to and date_from > date_to:
            return Response(
                {"detail": "date_from nie może być późniejsze niż date_to."},
                status=400,
            )

        summary = get_financial_summary(
            request.user,
            date_from=date_from,
            date_to=date_to,
        )
        serializer = FinancialSummarySerializer(summary)

        return Response(serializer.data)