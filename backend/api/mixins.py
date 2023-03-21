from django.db.models import Model, Q
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.status import (HTTP_201_CREATED, HTTP_204_NO_CONTENT,
                                   HTTP_400_BAD_REQUEST)


class AddDelViewMixin:
    add_serializer: ModelSerializer or None = None

    def get_queryset(self) -> Model:
        raise NotImplementedError

    def add_or_remove_object(
        self, obj_id: int or str, m2m_model: Model, q: Q
    ) -> Response:
        obj = get_object_or_404(self.get_queryset(), id=obj_id)
        serializer: ModelSerializer = self.add_serializer(obj)
        m2m_object = m2m_model.objects.filter(
            q, user=self.request.user
        ).first()

        if self.request.method == "POST":
            if not m2m_object:
                m2m_model.objects.create(obj=obj, user=self.request.user)
                return Response(serializer.data, status=HTTP_201_CREATED)

        elif self.request.method == "DELETE":
            if m2m_object:
                m2m_object.delete()
                return Response(status=HTTP_204_NO_CONTENT)

        return Response(status=HTTP_400_BAD_REQUEST)
