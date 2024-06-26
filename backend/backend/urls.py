from django.contrib import admin
from django.urls import path, include

from api.views import redirect_short_link

urlpatterns = [
    path('s/<str:short_link>/', redirect_short_link),
    path('admin/', admin.site.urls),
    path("api/", include("api.urls", namespace="api")),
]
