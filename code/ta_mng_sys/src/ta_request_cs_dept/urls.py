from django.urls import path
from . import views

app_name = 'ta_request_cs_dept'

urlpatterns = [
    # Instructor views
    path('', views.TARequestListView.as_view(), name='list'),
    path('create/', views.TARequestCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.TARequestUpdateView.as_view(), name='update'),
    path('<int:pk>/', views.TARequestDetailView.as_view(), name='detail'),
    
    # TA Coordinator views
    path('coordinator/', views.CoordinatorDashboardView.as_view(), name='coordinator_dashboard'),
    path('semesters/', views.SemesterListView.as_view(), name='semester_list'),
    path('semesters/create/', views.SemesterCreateView.as_view(), name='semester_create'),
    path('semesters/<int:pk>/edit/', views.SemesterUpdateView.as_view(), name='semester_update'),
    path('export/csv/', views.export_requests_csv, name='export_csv'),
    path('export/excel/', views.export_requests_excel, name='export_excel'),
    
    # API endpoints
    path('api/tas/', views.get_tas_json, name='tas_json'),
]