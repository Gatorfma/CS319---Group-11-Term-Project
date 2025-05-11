from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path('logs/', include('logs.urls', namespace='logs')),
     path(
        "accounts/logout/",
        LogoutView.as_view(next_page="home"),
        name="logout",
        ),  
     path("duties/", include("duties.urls")),
     path("courses/", include("courses.urls")),
]
