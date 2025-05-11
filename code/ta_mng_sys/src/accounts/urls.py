from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    UserListView, UserCreateView, UserUpdateView, UserDeleteView,
    CustomLoginView
)
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="accounts:login"), name="logout"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/create/", UserCreateView.as_view(), name="user_create"),
    path("assign_ta_to_courses/", views.assign_ta_to_courses, name="assign_ta_to_courses"),
    path("assign_ta_to_courses_excell/", views.assign_ta_to_courses_excell, name="assign_ta_to_courses_excell"),
    path('instructor/ta_workloads/', views.instructor_ta_workload_view, name='instructor_ta_workloads'),
    path("users/<int:pk>/edit/", UserUpdateView.as_view(), name="user_edit"),
    path("users/<int:pk>/delete/", UserDeleteView.as_view(), name="user_delete"),
]