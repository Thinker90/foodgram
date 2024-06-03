from django.contrib.auth import get_user_model
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, \
    IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

from djoser.views import UserViewSet

# еще тут должны быть фильтры/пермишны/пагинация?
from .serializers import (RecipesSerializer, TagSerializer,
                          IngredientSerializer, IngredientAmountSerializer,
                          UserProfileSerializer)
from recipes.models import (Recipes,
                            Carts,
                            Ingredients,
                            Tags,
                            AmountIngredient)

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


# ------------------------------------------------------




class RecipeViewSet(ModelViewSet):
    queryset = Recipes.objects.select_related("author")
    serializer_class = RecipesSerializer
    pagination_class = LimitOffsetPagination
