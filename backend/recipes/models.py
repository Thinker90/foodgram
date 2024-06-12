from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

User = get_user_model()


class Ingredients(models.Model):
    name = models.CharField(
        verbose_name='Ингридиент',
        max_length=64
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=24
    )

    class Meta:
        verbose_name = "Ингридиент"
        verbose_name_plural = "Ингридиенты"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("name", "measurement_unit"),
                name="unique_for_ingredient",
            )
        ]

        def __str__(self):
            return f"{self.name} - {self.measurement_unit}"


class Tags(models.Model):
    name = models.CharField(
        verbose_name="Тэг",
        max_length=150,
        unique=True,
    )
    slug = models.CharField(
        verbose_name="Слаг тэга",
        max_length=150,
        unique=True,
        db_index=False,
    )

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Recipes(models.Model):
    name = models.CharField(
        verbose_name="Название блюда",
        max_length=150,
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор рецепта",
        related_name="recipes",
        on_delete=models.SET_NULL,
        null=True,
    )
    tags = models.ManyToManyField(
        Tags,
        verbose_name="Тег",
        related_name="recipes",
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        verbose_name="Ингредиенты блюда",
        related_name="recipes",
        through="AmountIngredient",
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации",
        auto_now_add=True,
        editable=False,
    )
    image = models.ImageField(
        verbose_name="Изображение блюда",
        upload_to="recipe_images/",
    )
    text = models.TextField(
        verbose_name="Описание блюда",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления",
        validators=(
            MinValueValidator(
                1,
                "Ваше блюдо уже готово!",
            ),
            MaxValueValidator(
                200,
                "Очень долго ждать...",
            ),
        ),
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)
        constraints = [
            models.UniqueConstraint(
                fields=("name", "author"),
                name="unique_for_author",
            ),
        ]

    def __str__(self):
        return f"{self.name}. Автор: {self.author.username}"


class AmountIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipes,
        verbose_name="В каких рецептах",
        related_name="ingredient",
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredients,
        verbose_name="Связанные ингредиенты",
        related_name="ingredient_recipes",
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=[MinValueValidator(1, 'Количество ингридиентов не может быть меньше 1')]
    )
    class Meta:
        verbose_name = 'Кол-во ингридиентов'
        verbose_name_plural = 'Кол-во ингридиентов'
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'recipe'],
                                    name='unique ingredients recipe')
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique favorite recipe for user')
        ]


class Carts(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Корзина'
        verbose_name_plural = 'В корзине'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique cart user')
        ]
