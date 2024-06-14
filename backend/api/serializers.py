from django.contrib.auth import get_user_model
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Recipes,
                            Carts,
                            Ingredients,
                            Tags,
                            Favorite,
                            AmountIngredient)
from rest_framework.exceptions import ValidationError
from users.models import Subscribes

User = get_user_model()


# ------------------------------------------------------
# ------------------check and complete-----------------
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
            return Subscribes.objects.filter(user=user, author=obj).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = '__all__'


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipes
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
        model = Carts
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        recipe = ShortRecipeSerializer(instance.recipe,
                                       context=self.context).data
        return recipe


class UserInSubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribes
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


# ------------------------------------------------------

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
    ingredients = IngredientInRecipeSerializer(source='ingredient', many=True,
                                               read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Recipes.objects.filter(favorites__user=user, id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Recipes.objects.filter(cart__user=user, id=obj.id).exists()


class CreateRecipesSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tags.objects.all(),
                                              many=True)
    ingredients = serializers.ListField(child=serializers.DictField())
    image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text',
            'cooking_time', 'author'
        )

    def create_or_update(self, recipe, ingredients_data):
        for ingredient_data in ingredients_data:
            ingredient = Ingredients.objects.get(id=ingredient_data['id'])
            AmountIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )

    def validate_image(self, data):
        if not data:
            raise ValidationError('Необходимо загрузить изображение.')
        return data

    def validate(self, data):
        if 'ingredients' not in data:
            raise ValidationError('Вы не указали ингридиенты')

        if 'tags' not in data:
            raise ValidationError('Вы не указали тэги')

        tags = data.get('tags')
        ingredients = data.get('ingredients')
        ingredients_id = [ingredient['id'] for ingredient in ingredients]

        if not tags:
            raise ValidationError('Поле тегов не может быть пустым')
        if len(tags) != len(set(tags)):
            raise ValidationError('Теги не должны повторятся')

        if not ingredients:
            raise ValidationError('Поле ингридиентов не может быть пустым')
        if len(ingredients_id) != len(set(ingredients_id)):
            raise ValidationError('Ингридиенты не должны повторятся')

        ingredients = data.get('ingredients')
        ingredients_id = [ingredient['id'] for ingredient in ingredients]
        existing_ingredient_ids = list(
            Ingredients.objects.filter(
                id__in=ingredients_id
            ).values_list('id', flat=True))
        missing_ingredient_ids = set(ingredients_id) - set(
            existing_ingredient_ids)
        if missing_ingredient_ids:
            raise serializers.ValidationError(
                f"Ингредиенты с id={missing_ingredient_ids} не существуют.")

        for ingredient in ingredients:
            amount = ingredient.get('amount')
            if amount is None or int(amount) < 1:
                raise ValidationError(
                    'Количество ингридиентов не может быть меньше 1')

        return data

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipes.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_or_update(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)

        instance.tags.set(tags_data)

        AmountIngredient.objects.filter(recipe=instance).delete()
        for ingredient_data in ingredients_data:
            ingredient = Ingredients.objects.get(id=ingredient_data['id'])
            AmountIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )

        instance.save()
        return instance

    def to_representation(self, instance):
        serializer = RecipeSerializer(instance, context=self.context)
        return serializer.data


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
