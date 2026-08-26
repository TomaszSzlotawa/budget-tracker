from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TransactionViewSet, RegisterView, FinancialSummaryView


router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("transactions", TransactionViewSet, basename="transaction")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "auth/register/",
        RegisterView.as_view(),
        name="register",
    ),
    path(
        "summary/",
        FinancialSummaryView.as_view(),
        name="financial-summary",
    ),
]