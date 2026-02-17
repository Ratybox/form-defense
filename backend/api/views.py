from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import FormEntry
from .serializers import FormEntrySerializer


class FormEntryViewSet(viewsets.ModelViewSet):
    queryset = FormEntry.objects.all()
    serializer_class = FormEntrySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {'status': 'success', 'message': 'Données enregistrées avec succès', 'data': serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )
