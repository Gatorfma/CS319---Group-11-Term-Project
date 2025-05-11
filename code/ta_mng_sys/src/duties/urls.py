from django.urls import path
from .views import get_offerings_for_duty_type, manage_duty_logs, auto_assign_proctors_view, assign_classrooms_view, delete_exam_assignments_view, edit_exam_assignment_view, manage_exam_assignments_view, manual_assign_proctors_view, select_exam_for_manual_assignment, log_completed_duty
app_name = "duties"

urlpatterns = [
    path('auto-assign-proctors/', auto_assign_proctors_view, name='auto_assign_proctors'),
    path('assign-classrooms/<int:exam_id>/', assign_classrooms_view, name='assign_classrooms'),
    path('assign/manual/select-exam/', select_exam_for_manual_assignment, name='select_exam_for_manual_assignment'),
    path('assign/manual/<int:exam_id>/', manual_assign_proctors_view, name='manual_assign_proctors'),
    path('manage-exam-assignments/', manage_exam_assignments_view, name='manage_exam_assignments'),
    path('edit-exam-assignment/<int:exam_id>/', edit_exam_assignment_view, name='edit_exam_assignment'),
    path('delete-exam-assignments/<int:exam_id>/', delete_exam_assignments_view, name='delete_exam_assignments'),
    path('log-duty/', log_completed_duty, name='log-completed-duty'),
    path('log-duty/manage/', manage_duty_logs, name='manage-duty-logs'),
    path('ajax/get_offerings/', get_offerings_for_duty_type, name='get_offerings_for_duty_type'),
]