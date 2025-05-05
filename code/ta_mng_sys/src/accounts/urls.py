from django.urls import path
from django.contrib.auth import views as auth_views
from .views import UserListView, UserCreateView

app_name = "accounts"

urlpatterns = [
    path("login/",  auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="accounts:login"),      name="logout"),
    path("users/",        UserListView.as_view(),   name="user_list"),
    path("users/create/", UserCreateView.as_view(), name="user_create"),
]
