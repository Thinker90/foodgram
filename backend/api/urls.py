from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (RecipeViewSet, IngredientsViewSet,
                    TagsViewSet, CustomUserViewSet)

app_name = 'api'

router = DefaultRouter()
router.register('recipes', RecipeViewSet, 'recipes')
router.register('ingredients', IngredientsViewSet, 'ingredients')
router.register('tags', TagsViewSet, 'tags')
router.register('users', CustomUserViewSet, 'users')

urlpatterns = (
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
)
