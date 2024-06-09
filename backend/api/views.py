from django.contrib.auth import get_user_model
import django_filters
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, \
    IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

from djoser.views import UserViewSet
from shortener import shortener

# еще тут должны быть фильтры/пермишны/пагинация?
from .serializers import (TagSerializer,
                          IngredientSerializer,
                          CreateRecipesSerializer,
                          RecipeSerializer,
                          UserProfileSerializer
                          )
from recipes.models import (Recipes,
                            Carts,
                            Ingredients,
                            Tags,
                            AmountIngredient)

from users.models import Subscribes

User = get_user_model()


# фиильтрацию надо вынести в отдельный файл
class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='istartswith')

    class Meta:
        model = Ingredients
        fields = ['name']


# ------------------------------------------------------
# ------------------check and complete-----------------
class IngredientsViewSet(ReadOnlyModelViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = 'name'
    pagination_class = None


class TagsViewSet(ReadOnlyModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class CustomUserViewSet(UserViewSet):
    pagination_class = LimitOffsetPagination

    @action(detail=False,
            methods=['GET'],
            permission_classes=[IsAuthenticated, ])
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(detail=False,
            methods=['PUT', 'PATH'],
            url_path='me/avatar',
            permission_classes=[IsAuthenticated, ])
    def avatar(self, request, *args, **kwargs):
        user = request.user
        avatar_file = request.data.get('avatar')

        if avatar_file:
            user.avatar = avatar_file
            user.save()
            return Response(request.data,
                            status=status.HTTP_200_OK)
        else:
            return Response({"Вы не загрузили аватар!"},
                            status=status.HTTP_400_BAD_REQUEST)

    @avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        user = request.user
        user.avatar = None
        user.save()
        return Response({"Аватар успешно удален!"},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        author = self.get_object()
        if user == author:
            return Response({
                'errors': 'Вы не можете подписываться на самого себя'
            }, status=status.HTTP_400_BAD_REQUEST)

        subscription, created = Subscribes.objects.get_or_create(user=user,
                                                                 author=author)
        if created:
            user_serializer = UserProfileSerializer(author, context={
                'request': request})
            return Response(user_serializer.data,
                            status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'message': 'Вы уже подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['DELETE'],
            permission_classes=[IsAuthenticated])
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()

        subscription = Subscribes.objects.filter(user=user,
                                                 author=author).first()
        if subscription:
            subscription.delete()
            return Response({'success': 'Подписка успешно удалена'},
                            status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'message': 'Вы не были подписаны на этого пользователя'},
                status=status.HTTP_200_OK)

    @action(detail=True, methods=['DELETE'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        pass


# ------------------------------------------------------

class RecipeViewSet(ModelViewSet):
    queryset = Recipes.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, ]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return CreateRecipesSerializer
        return RecipeSerializer

    @action(detail=True,
            permission_classes=[IsAuthenticated, ])
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
