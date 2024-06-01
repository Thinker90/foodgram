from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, IngredientsViewSet, TagsViewSet

app_name = 'api'

router = DefaultRouter()
router.register('recipes', RecipeViewSet, 'recipes')
router.register('ingredients', IngredientsViewSet, 'ingredients')
router.register('tags', TagsViewSet, 'tags')

urlpatterns = (
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
)
