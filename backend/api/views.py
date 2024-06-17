from django.contrib.auth import get_user_model
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend

from djoser.views import UserViewSet

from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated)

from urllib.parse import urljoin

from .filters import RecipeFilter, IngredientFilter
from .mixins import SubscriptionsManagerMixin
from .permissions import IsAuthorOrReadOnly
from .serializers import (TagSerializer, IngredientSerializer,
                          CreateRecipesSerializer,
                          RecipeSerializer, RecipeInCartSerializer,
                          RecipeInFavoriteerializer, UserInSubscribeSerializer,
                          )
from recipes.models import (Recipe, Cart, Ingredient, Tag,
                            AmountIngredient, Favorite)

from users.models import Subscribe

User = get_user_model()


class IngredientsViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = 'name'
    pagination_class = None


class TagsViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class CustomUserViewSet(UserViewSet, SubscriptionsManagerMixin):
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
            return Response(request.data, status=status.HTTP_200_OK)
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
        return self.add_subscribe(
            UserInSubscribeSerializer(data=data, context={'request': request}))

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        filter_set = {'user': request.user, 'author': self.get_object()}
        message = {'success': 'Подписка успешно удалена!',
                   'error': 'Вы небыли подписаны!'}
        return self.delete_subscribe(Subscribe, filter_set, message)

    @action(detail=False,
            methods=['GET'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        subscriptions = Subscribe.objects.filter(user=user)

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(subscriptions, request)

        serializer = UserInSubscribeSerializer(result_page, many=True,
                                               context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class RecipeViewSet(ModelViewSet, SubscriptionsManagerMixin):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly, ]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def check_item(self, model, id):
        return model.objects.filter(id=id).exists()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return CreateRecipesSerializer
        return RecipeSerializer

    @action(detail=True,
            permission_classes=[IsAuthenticated, ])
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True,
            methods=['POST'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, *args, **kwargs):
        if not self.check_item(Recipe, kwargs.get('pk')):
            return Response({"Такого рецепта нет!"},
                            status=status.HTTP_404_NOT_FOUND)

        data = {'user': request.user.id, 'recipe': kwargs.get('pk')}
        return self.add_subscribe(RecipeInCartSerializer(data=data))

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, *args, **kwargs):
        if not self.check_item(Recipe, kwargs.get('pk')):
            return Response({"Такого рецепта нет!"},
                            status=status.HTTP_404_NOT_FOUND)
        filter_set = {'user': request.user, 'recipe': kwargs.get('pk')}
        message = {'success': 'Рецепт удален из корзины!',
                   'error': 'В корзине нет такого рецепта!'}
        return self.delete_subscribe(Cart, filter_set, message)

    @action(detail=False,
            methods=['GET'])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = user.cart.select_related('recipe').all()
        if not shopping_cart:
            return Response({"Корзина покупок пуста!"},
                            status=status.HTTP_404_NOT_FOUND)

        ingredients_data = AmountIngredient.objects.filter(
            recipe__in=[cart_item.recipe for cart_item in shopping_cart]
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).values_list(
            'ingredient__name', 'total_amount', 'ingredient__measurement_unit'
        )
        ingredients_list = []
        for name, total_amount, unit in ingredients_data:
            ingredients_list.append(
                f" - {name}: {total_amount} {unit}"
            )
        return Response(ingredients_list)

    @action(detail=True,
            methods=['POST'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, *args, **kwargs):
        if not self.check_item(Recipe, kwargs.get('pk')):
            return Response({"Такого рецепта нет!"},
                            status=status.HTTP_404_NOT_FOUND)
        data = {'user': request.user.id, 'recipe': kwargs.get('pk')}
        return self.add_subscribe(RecipeInFavoriteerializer(data=data))

    @favorite.mapping.delete
    def delete_favorite(self, request, *args, **kwargs):
        if not self.check_item(Recipe, kwargs.get('pk')):
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
