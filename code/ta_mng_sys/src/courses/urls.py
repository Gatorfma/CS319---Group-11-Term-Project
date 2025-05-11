from django.urls import path
from .views import import_data_view

app_name = "courses"

urlpatterns = [
    path('import-data/', import_data_view, name='import_data'),
]
