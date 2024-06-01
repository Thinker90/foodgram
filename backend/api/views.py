from django.contrib.auth import get_user_model
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from djoser.views import viewsets as djoserviewsets

# еще тут должны быть фильтры/пермишны/пагинация?
from .serializers import (RecipesSerializer, TagSerializer,
                          IngredientSerializer, IngredientAmountSerializer,
                          CustomUserCreateSerializer)
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
class UserViewSet(djoserviewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserCreateSerializer
    pagination_class = LimitOffsetPagination
    http_method_names = ('get', 'post', 'patch', 'delete')



class RecipeViewSet(ModelViewSet):
    queryset = Recipes.objects.select_related("author")
    serializer_class = RecipesSerializer
    pagination_class = LimitOffsetPagination


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
