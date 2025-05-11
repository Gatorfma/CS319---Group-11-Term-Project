from django.urls import path
from django.contrib.auth import views as auth_views
from .views import UserListView, UserCreateView
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/",  auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="accounts:login"),      name="logout"),
    path("users/",        UserListView.as_view(),   name="user_list"),
    path("users/create/", UserCreateView.as_view(), name="user_create"),
    path("assign_ta_to_courses/", views.assign_ta_to_courses, name="assign_ta_to_courses"),
    path("assign_ta_to_courses_excell/", views.assign_ta_to_courses_excell, name="assign_ta_to_courses_excell"),
    path('instructor/ta_workloads/', views.instructor_ta_workload_view, name='instructor_ta_workloads'),
]
