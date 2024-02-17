from rest_framework import viewsets
from .models import UserRequest, ProteinSequence
from .serializers import UserRequestSerializer, ProteinSequenceSerializer

class UserRequestViewSet(viewsets.ModelViewSet):
    queryset = UserRequest.objects.all()
    serializer_class = UserRequestSerializer

class ProteinSequenceViewSet(viewsets.ModelViewSet):
    queryset = ProteinSequence.objects.all()
    serializer_class = ProteinSequenceSerializer
