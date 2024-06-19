from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (AmountIngredient, Cart, Favorite, Ingredient,
                            Recipe, Tag)
from users.models import Subscribe

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password')
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
        }


class UserProfileSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password', 'is_subscribed', 'avatar')
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
        }

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Subscribe.objects.filter(user=user, author=obj).exists()
        return False

    def validate_avatar(self, data):
        if not data:
            raise ValidationError('Необходимо загрузить изображение.')
        return data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id', 'image', 'name', 'cooking_time'
        )


class RecipeInFavoriteerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        recipe = ShortRecipeSerializer(instance.recipe,
                                       context=self.context).data
        return recipe


class RecipeInCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return ShortRecipeSerializer(instance.recipe,
                                     context=self.context).data


class UserInSubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = ('user', 'author')

    def to_representation(self, instance):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = instance.author.recipes.all()
        if recipes_limit:
            recipes_limit = recipes[:int(recipes_limit)]

        user_data = UserProfileSerializer(instance.author,
                                          context=self.context).data

        user_data['recipes'] = ShortRecipeSerializer(
            recipes_limit, many=True,
            context=self.context).data
        user_data['recipes_count'] = len(user_data['recipes'])
        return user_data


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = AmountIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True,
                                               read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(favorites__user=user, id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(cart__user=user, id=obj.id).exists()


class CreateRecipesSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    ingredients = serializers.ListField(child=serializers.DictField())
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text',
            'cooking_time', 'author'
        )

    def create_ingredients(self, recipe, ingredients_data):
        ingredient_objects = [
            AmountIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ]
        AmountIngredient.objects.bulk_create(ingredient_objects)

    def validate_image(self, data):
        if not data:
            raise ValidationError('Необходимо загрузить изображение.')
        return data

    def validate(self, data):
        if 'ingredients' not in data:
            raise ValidationError('Вы не указали ингредиенты')

        if 'tags' not in data:
            raise ValidationError('Вы не указали тэги')

        tags = data.get('tags')
        ingredients = data.get('ingredients')
        ingredients_ids = [ingredient['id'] for ingredient in ingredients]

        if not tags:
            raise ValidationError('Поле тегов не может быть пустым')
        if len(tags) != len(set(tags)):
            raise ValidationError('Теги не должны повторятся')

        if not ingredients:
            raise ValidationError('Поле ингредиентов не может быть пустым')
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise ValidationError('ингредиенты не должны повторятся')

        existing_ingredient_ids = list(
            Ingredient.objects.filter(
                id__in=ingredients_ids
            ).values_list('id', flat=True))
        missing_ingredient_ids = set(ingredients_ids) - set(
            existing_ingredient_ids)
        if missing_ingredient_ids:
            raise serializers.ValidationError(
                f"Ингредиенты с id={missing_ingredient_ids} не существуют.")

        for ingredient in ingredients:
            amount = ingredient.get('amount')
            if amount is None or int(amount) < 1:
                raise ValidationError(
                    'Количество ингредиентов не может быть меньше 1')

        return data

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        updated_instance = super().update(instance, validated_data)
        updated_instance.tags.set(tags_data)

        AmountIngredient.objects.filter(recipe=updated_instance).delete()

        self.create_ingredients(updated_instance, ingredients_data)
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class SubscribeSerializer(serializers.Serializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar', 'recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return ShortRecipeSerializer(recipes, many=True,
                                     context=self.context).data
