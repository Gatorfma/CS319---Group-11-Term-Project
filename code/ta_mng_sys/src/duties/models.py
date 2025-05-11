from django.db import models
from courses.models import Classroom, Course, CourseOffering, Exam
from accounts.models import TAProfile, CustomUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

# Create your models here.
class Duty(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'P', 'Pending'
        APPROVED = 'A', 'Approved'
        REJECTED = 'R', 'Rejected'

    offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name='%(class)sduties',
        help_text='Course offering this duty belongs to',
        null=True,       
        blank=True,
        default=None
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_hours = models.PositiveIntegerField(
        help_text='Length of duty in hours'
    )
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.PENDING
    )
    description = models.TextField(
        blank=True,
        help_text='Optional description or notes'
    )
    created_by = models.ForeignKey(
        CustomUser,
        limit_choices_to={'role': CustomUser.Roles.INSTRUCTOR},
        on_delete=models.CASCADE,
        related_name='created_%(class)sduties',
        help_text='Instructor or staff who created this duty'
    )
    assigned_ta = models.ForeignKey(
        TAProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)sduties',
        help_text='TA assigned to this duty'
    )

    def get_type_slug(self):
        return {
            "LabDuty": "lab",
            "GradingDuty": "grading",
            "RecitationDuty": "recitation",
            "OfficeHourDuty": "office",  # ✅ fix this
            "ProctoringDuty": "proctoring",
        }.get(self.__class__.__name__.strip(), "unknown")

    assigned_ta_list = models.ManyToManyField(
    TAProfile,
    blank=True,
    related_name='%(class)sdutiees',
    help_text='TA assigned to this duty'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.__class__.__name__} for {self.offering} on {self.date}"


class LabDuty(Duty):
    lab_number = models.PositiveIntegerField(
        help_text='Lab number for this duty'
    )


class GradingDuty(Duty):
    class GradingType(models.TextChoices):
        MIDTERM   = 'MID', 'Midterm'
        FINAL     = 'FIN', 'Final'
        HOMEWORK  = 'HW',  'Homework'

    grading_type = models.CharField(
        max_length=6,
        choices=GradingType.choices,
        help_text='Type of grading task'
    )


class RecitationDuty(Duty):
    topic = models.CharField(
        max_length=200,
        help_text='Topic for this recitation session'
    )


class OfficeHourDuty(Duty):
    location = models.CharField(
        max_length=200,
        help_text='Location for this office hour'
    )


class ProctoringDuty(Duty):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='proctoring_duties',
        help_text='Exam this proctoring duty is for'
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proctoring_duties',
        help_text='Classroom where this TA will proctor the exam'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='proctoring_duties',
        help_text='Course for this duty'
    )



class TACourseAssignment(models.Model):
    ta       = models.ForeignKey(
        TAProfile,
        on_delete=models.CASCADE
    )
    offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.ta.user.username} assigned to {self.offering}"

class DutyLog(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'P', 'Pending'
        APPROVED = 'A', 'Approved'
        REJECTED = 'R', 'Rejected'

    duty_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text='Content type for the duty being logged'
    )
    duty_object_id    = models.PositiveIntegerField(
        help_text='PK of the duty being logged'
    )
    duty              = GenericForeignKey(
        'duty_content_type',
        'duty_object_id'
    )
    ta_profile        = models.ForeignKey(
        TAProfile,
        on_delete=models.CASCADE,
        related_name='duty_logs',
        help_text='TA who logged this duty'
    )
    date_logged       = models.DateTimeField(
        default=timezone.now,
        editable=False
    )
    hours_spent       = models.FloatField(
        help_text='Hours worked'
    )
    description       = models.TextField(blank=True)
    status            = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.PENDING
    )
    processed_by      = models.ForeignKey(
        CustomUser,
        limit_choices_to={
            'role__in': [
                CustomUser.Roles.INSTRUCTOR,
                CustomUser.Roles.SECRETARY,
                CustomUser.Roles.DEPT_CHAIR,
                CustomUser.Roles.DEAN,
                CustomUser.Roles.ADMIN
            ]
        },
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='processed_duty_logs',
        help_text='Staff user who approved/rejected this log'
    )
    processed_at      = models.DateTimeField(
        null=True, blank=True,
        help_text='When the log was approved/rejected'
    )

    class Meta:
        ordering = ['-date_logged']

    def __str__(self):
        return (f"DutyLog by {self.ta_profile.user.username}: "
                f"{self.hours_spent}h on {self.date_logged.date()} "
                f"[{self.get_status_display()}]")
