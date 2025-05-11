from django.urls import path
from . import views

app_name = 'logs'

urlpatterns = [
    path('', views.logs_dashboard, name='dashboard'),
    path('object/<str:model_name>/<str:object_id>/', views.object_logs, name='object_logs'),
]