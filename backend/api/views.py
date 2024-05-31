from django.contrib.auth import get_user_model
from django.db.migrations import serializer
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import filters, status, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import action
from djoser.views import viewsets as djoserviewsets


from .serializers import (UserProfileSerializer, CustomUserCreateSerializer,
                          )

User = get_user_model()


class UserViewSet(djoserviewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserCreateSerializer
    pagination_class = LimitOffsetPagination
    http_method_names = ('get', 'post', 'patch', 'delete')

