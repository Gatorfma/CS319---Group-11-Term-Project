from django.urls import path
from .views import import_data_view
from . import views

app_name = "courses"

urlpatterns = [
    path('import-data/', import_data_view, name='import_data'),
    path("upload_student_excell/",  views.upload_student_excell, name="upload_student_excell"),
]
