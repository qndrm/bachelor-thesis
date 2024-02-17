from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import UserRequestViewSet, ProteinSequenceViewSet

router = DefaultRouter()
router.register(r'userrequests', UserRequestViewSet)
router.register(r'proteinsequences', ProteinSequenceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
