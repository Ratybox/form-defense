from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FormEntryViewSet

router = DefaultRouter()
router.register(r'entries', FormEntryViewSet, basename='entry')

urlpatterns = [
    path('', include(router.urls)),
]
