from django.contrib import admin
from .models import Course, Classroom, Exam, CourseOffering

# Register your models here.
# courses/admin.py

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('department_code', 'course_code', 'title')
    list_filter = ('department_code',)
    search_fields = ('department_code', 'course_code', 'title')
    ordering = ('department_code', 'course_code')


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('building', 'room_number', 'capacity', 'exam_capacity')
    list_filter = ('building',)
    search_fields = ('building', 'room_number')
    ordering = ('building', 'room_number')

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = (
        'course',
        'date',
        'start_time',
        'end_time',
        'num_proctors_required',
        'number_of_students',
        'classroom',
    )
    list_filter = (
        'date',
        'course__department_code',
        'classroom__building',
    )
    search_fields = (
        'course__department_code',
        'course__course_code',
        'course__title',
    )
    filter_horizontal = ('assigned_tas', 'students')

# courses/admin.py
@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = (
        'course',
        'semester',
        'section',
        'max_capacity',
        'enrolled_count'
    )
    list_filter = (
        'semester',
        'course__department_code',
        'instructors',
    )
    search_fields = (
        'course__department_code',
        'course__course_code',
        'course__title',
        'semester',
    )
    filter_horizontal = ('instructors', 'tas', 'students')
