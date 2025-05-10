from django.db import models
from django.conf import settings
from accounts.models import TAProfile, Student, CustomUser

# Create your models here.

class Course(models.Model):
    department_code = models.CharField(
        max_length=5,
        help_text='e.g. "CS", "IE", "EE"'
    )
    course_code = models.PositiveIntegerField(
        help_text='Numeric code, e.g. 101, 402'
    )
    title = models.CharField(
        max_length=200,
        help_text='Course title, e.g. "Object-Oriented Software Engineering"'
    )

    class Meta:
        unique_together = ('department_code', 'course_code')
        ordering = ['department_code', 'course_code']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    def __str__(self):
        return f"{self.department_code}{self.course_code} – {self.title}"

# classrooms
class Classroom(models.Model):
    building = models.CharField(
        max_length=100,
        blank=True,
        help_text='Building name or code, e.g. "ENGR", "Main"'
    )
    room_number = models.CharField(
        max_length=20,
        help_text='Room number or identifier, e.g. "101", "B-12"'
    )
    capacity = models.PositiveIntegerField(
        help_text='Standard seating capacity for classes'
    )
    exam_capacity = models.PositiveIntegerField(
        help_text='Number of seats available when arranged for exam'
    )

    class Meta:
        unique_together = ('building', 'room_number')
        ordering = ['building', 'room_number']
        verbose_name = 'Classroom'
        verbose_name_plural = 'Classrooms'

    def __str__(self):
        if self.building:
            return f"{self.building} {self.room_number}"
        return self.room_number

# exams
class Exam(models.Model):
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='exams'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.DurationField(
        help_text='Duration of the exam as a timedelta'
    )
    num_proctors_required = models.PositiveSmallIntegerField(
        help_text='Number of TAs needed to proctor'
    )
    assigned_tas = models.ManyToManyField(
        'accounts.TAProfile',
        related_name='proctored_exams',
        blank=True,
        help_text='TAs assigned to proctor this exam'
    )
    classroom = models.ManyToManyField(
        'courses.Classroom',
        blank=True,
        related_name='exams',
        help_text='Room where the exam will be held'
    )
    number_of_students = models.PositiveIntegerField(
        help_text='Total students taking the exam'
    )
    students = models.ManyToManyField(
        'accounts.Student',
        related_name='exams',
        blank=True,
        help_text='List of students taking this exam'
    )

    class Meta:
        ordering = ['date', 'start_time']
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'

    def __str__(self):
        return f"{self.course} Exam on {self.date}"


# courses/models.py
class CourseOffering(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='offerings',
        help_text='The course this offering belongs to'
    )
    semester = models.CharField(
        max_length=20,
        help_text='e.g. "Fall 2025", "Spring 2026"'
    )
    section = models.PositiveSmallIntegerField(
        help_text='Section number, e.g. 1, 2, 3'
    )

    # Instructors: multiple per offering
    instructors = models.ManyToManyField(
        CustomUser,
        limit_choices_to={'role': CustomUser.Roles.INSTRUCTOR},
        related_name='course_offerings',
        blank=True,
        help_text='Instructors teaching this offering'
    )

    # TAs assigned to this offering
    tas = models.ManyToManyField(
        TAProfile,
        related_name='course_offerings',
        blank=True,
        help_text='TAs assigned to assist this offering'
    )

    # Student enrollment
    max_capacity = models.PositiveIntegerField(
        help_text='Maximum number of students allowed'
    )
    enrolled_count = models.PositiveIntegerField(
        default=0,
        help_text='Current count of enrolled students'
    )
    students = models.ManyToManyField(
        Student,
        related_name='course_offerings',
        blank=True,
        help_text='Students enrolled in this offering'
    )

    class Meta:
        unique_together = ('course', 'semester', 'section')
        ordering = [
            'course__department_code',
            'course__course_code',
            'semester',
            'section'
        ]
        verbose_name = 'Course Offering'
        verbose_name_plural = 'Course Offerings'

    def __str__(self):
        return f"{self.course} — {self.semester} (Sec {self.section})"
    
