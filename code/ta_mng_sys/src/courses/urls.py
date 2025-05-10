from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("upload_student_excell/",  views.upload_student_excell, name="upload_student_excell"),
]
