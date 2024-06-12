from django.contrib.auth import get_user_model
import django_filters

from urllib.parse import urljoin

from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, \
    IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

from djoser.views import UserViewSet

# еще тут должны быть фильтры/пермишны/пагинация?
from .serializers import (TagSerializer,
                          IngredientSerializer,
                          CreateRecipesSerializer,
                          RecipeSerializer,
                          UserProfileSerializer, SubscribeSerializer,
                          RecipeInCartSerializer, RecipeInFavoriteerializer,
                          UserInSubscribeSerializer,

                          )
from recipes.models import (Recipes,
                            Carts,
                            Ingredients,
                            Tags,
                            AmountIngredient,
                            Favorite)

from users.models import Subscribes

User = get_user_model()


# фиильтрацию надо вынести в отдельный файл
class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='istartswith')

    class Meta:
        model = Ingredients
        fields = ['name']

class RecipeFilter(FilterSet):
    author = filters.NumberFilter(field_name="author__id")
    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipes
        fields = ['author', 'tags']

    def filter_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(cart__user=self.request.user)
        print("User is anonymous or filter is not applied for favorites")
        return queryset

class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return obj.author == request.user


class SubscriptionsManager:
    def add_subscribe(self, serializer):
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_subscribe(self, model, filter_set, message: dict):
        subscription = model.objects.filter(**filter_set).first()
        if subscription:
            subscription.delete()
            return Response({'success': message['success']},
                            status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'message': message['error']},
                status=status.HTTP_400_BAD_REQUEST)


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


class CustomUserViewSet(UserViewSet, SubscriptionsManager):
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

    @action(detail=True,
            methods=['POST'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, *args, **kwargs):
        data = {'user': request.user.id, 'author': self.get_object().id}
        return self.add_subscribe(UserInSubscribeSerializer(data=data, context={'request': request}))

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        filter_set = {'user': request.user, 'author': self.get_object()}
        message = {'success': 'Подписка успешно удалена!',
                   'error': 'Вы небыли подписаны!'}
        return self.delete_subscribe(Subscribes, filter_set, message)

    @action(detail=False,
            methods=['GET'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        subscriptions = Subscribes.objects.filter(user=user)

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(subscriptions, request)

        serializer = UserInSubscribeSerializer(result_page, many=True,
                                               context={'request': request})
        return paginator.get_paginated_response(serializer.data)


# ------------------------------------------------------

class RecipeViewSet(ModelViewSet, SubscriptionsManager):
    queryset = Recipes.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly, ]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def check_item(self, model, id):
        if model.objects.filter(id=id).exists():
            return False
        return True

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

    @action(detail=True,
            methods=['POST'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, *args, **kwargs):
        if self.check_item(Recipes, kwargs.get('pk')):
            return Response({"Такого рецепта нет!"},
                            status=status.HTTP_404_NOT_FOUND)

        data = {'user': request.user.id, 'recipe': kwargs.get('pk')}
        return self.add_subscribe(RecipeInCartSerializer(data=data))

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, *args, **kwargs):
        if self.check_item(Recipes, kwargs.get('pk')):
            return Response({"Такого рецепта нет!"},
                            status=status.HTTP_404_NOT_FOUND)
        filter_set = {'user': request.user, 'recipe': kwargs.get('pk')}
        message = {'success': 'Рецепт удален из корзины!',
                   'error': 'В корзине нет такого рецепта!'}
        return self.delete_subscribe(Carts, filter_set, message)

    @action(detail=False,
            methods=['GET'])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = user.cart.select_related('recipe').all()
        if not shopping_cart:
            return ValidationError('Список покупок пуст!')

        ingredients_list = []
        for cart_item in shopping_cart:
            recipe = cart_item.recipe
            ingredients_list.append(f'>>>>>>>{recipe.name}<<<<<<<')
            ingredients_list.append(f'Ингридиенты: ')
            amount_ingredients = AmountIngredient.objects.filter(recipe=recipe)
            for amount_ingredient in amount_ingredients:
                ingredient = amount_ingredient.ingredient
                ingredients_list.append(
                    f" - {ingredient.name}: {amount_ingredient.amount} {ingredient.measurement_unit}")
        return Response(ingredients_list)


    @action(detail=True,
            methods=['POST'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, *args, **kwargs):
        if self.check_item(Recipes, kwargs.get('pk')):
            return Response({"Такого рецепта нет!"},
                            status=status.HTTP_404_NOT_FOUND)
        data = {'user': request.user.id, 'recipe': kwargs.get('pk')}
        return self.add_subscribe(RecipeInFavoriteerializer(data=data))

    @favorite.mapping.delete
    def delete_favorite(self, request, *args, **kwargs):
        if self.check_item(Recipes, kwargs.get('pk')):
            return Response({"Такого рецепта нет!"},
                            status=status.HTTP_404_NOT_FOUND)
        filter_set = {'user': request.user, 'recipe': kwargs.get('pk')}
        message = {'success': 'Рецепт удален из избранного!',
                   'error': 'В избранном нет такого рецепта!'}
        return self.delete_subscribe(Favorite, filter_set, message)

    @action(detail=True,
            url_path='get-link',
            methods=['GET'])
    def get_link(self, request, *args, **kwargs):
        recipe_id = kwargs.get('pk')
        domain = request.get_host()
        short_id = hash(recipe_id) % 1000
        short_link = urljoin(f"https://{domain}/s/", str(short_id))
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)
