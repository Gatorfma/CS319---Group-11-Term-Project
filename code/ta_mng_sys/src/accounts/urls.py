from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    UserListView, UserCreateView, UserUpdateView, UserDeleteView,
    CustomLoginView
)

app_name = "accounts"

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="accounts:login"), name="logout"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/create/", UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/edit/", UserUpdateView.as_view(), name="user_edit"),
    path("users/<int:pk>/delete/", UserDeleteView.as_view(), name="user_delete"),
]