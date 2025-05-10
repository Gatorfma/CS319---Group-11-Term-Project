from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("export_student_classroom_dist/",  views.export_student_classroom_dist, name="export_student_classroom_dist"),
    path("upload_student_excell/",  views.upload_student_excell, name="upload_student_excell"),
]
