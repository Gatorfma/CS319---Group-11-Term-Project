from django.db import models
from django.conf import settings
from courses.models import Course
from accounts.models import CustomUser, TAProfile, InstructorProfile

class Semester(models.Model):
    """
    Represents an academic semester for which TA requests can be made
    """
    name = models.CharField(
        max_length=100,
        help_text="Semester name (e.g. 'Fall 2025')"
    )
    start_date = models.DateField(help_text="Start date of the semester")
    end_date = models.DateField(help_text="End date of the semester")
    
    # TA request period
    request_start_date = models.DateField(
        help_text="Date when instructors can start submitting TA requests"
    )
    request_end_date = models.DateField(
        help_text="Deadline for TA request submissions"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this is the current active semester"
    )
    
    ta_coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': CustomUser.Roles.INSTRUCTOR},
        related_name='coordinated_semesters',
        help_text="Instructor responsible for managing TA assignments this semester"
    )
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = "Semester"
        verbose_name_plural = "Semesters"
    
    def __str__(self):
        return self.name
    
    def is_request_period_active(self):
        """Check if the TA request period is currently active"""
        from datetime import date
        today = date.today()
        return self.request_start_date <= today <= self.request_end_date
    
    def save(self, *args, **kwargs):
        # Ensure only one active semester
        if self.is_active:
            Semester.objects.filter(is_active=True).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)


class TARequest(models.Model):
    """
    Model to store TA request data from instructors for a specific course.
    Based on the department's Excel form requirements.
    """
    # Basic information
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        limit_choices_to={'role': CustomUser.Roles.INSTRUCTOR},
        related_name='ta_request_cs_dept'
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name='ta_request_cs_dept',
        help_text="Semester for which this request applies"
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE,
        related_name='ta_request_cs_dept',
        help_text="Course that needs TAs"
    )
    
    # TA and grader quantities
    min_ta_loads = models.PositiveIntegerField(
        help_text="Minimum number of TA loads requested"
    )
    max_ta_loads = models.PositiveIntegerField(
        help_text="Maximum number of TA loads requested"
    )
    graders_requested = models.PositiveIntegerField(
        default=0,
        help_text="Number of graders requested"
    )
    
    # All preferences are now handled through preference models
    preferred_tas = models.ManyToManyField(
        TAProfile,
        through='TAPreference',
        related_name='preferred_by_requests',
        blank=True,
        help_text="Preferred TAs in order of preference"
    )
    
    preferred_graders = models.ManyToManyField(
        TAProfile,
        through='GraderPreference',
        related_name='preferred_as_grader',
        blank=True,
        help_text="Preferred graders in order of preference"
    )
    
    must_have_tas = models.ManyToManyField(
        TAProfile,
        through='MustHaveTAPreference',
        related_name='must_have_requests',
        blank=True,
        help_text="TAs that must be assigned to this course"
    )
    
    tas_to_avoid = models.ManyToManyField(
        TAProfile,
        through='AvoidTAPreference',
        related_name='avoid_as_ta',
        blank=True,
        help_text="TAs to avoid assigning to this course"
    )
    
    graders_to_avoid = models.ManyToManyField(
        TAProfile,
        through='AvoidGraderPreference',
        related_name='avoid_as_grader',
        blank=True,
        help_text="Graders to avoid assigning to this course"
    )
    
    # Justifications
    must_have_justification = models.TextField(
        blank=True,
        help_text="Justification for must-have TAs"
    )
    general_justification = models.TextField(
        blank=True,
        help_text="Justification for overage or other issues"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "TA Request"
        verbose_name_plural = "TA Requests"
        # One request per instructor per course per semester
        unique_together = ['instructor', 'course', 'semester']
        
    def __str__(self):
        return f"{self.course.department_code} {str(self.course.course_code)} - {self.semester.name} - {self.instructor.get_full_name()}"


# Base Preference Model to inherit from
class BasePreference(models.Model):
    ta_request = models.ForeignKey(TARequest, on_delete=models.CASCADE)
    ta = models.ForeignKey(TAProfile, on_delete=models.CASCADE)
    preference_order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers indicate higher preference"
    )
    
    class Meta:
        abstract = True
        ordering = ['preference_order']


class TAPreference(BasePreference):
    """Preferred TAs with preference order"""
    class Meta:
        unique_together = ['ta_request', 'ta']
        ordering = ['preference_order']
        verbose_name = "Preferred TA"
        verbose_name_plural = "Preferred TAs"


class GraderPreference(BasePreference):
    """Preferred graders with preference order"""
    class Meta:
        unique_together = ['ta_request', 'ta']
        ordering = ['preference_order']
        verbose_name = "Preferred Grader"
        verbose_name_plural = "Preferred Graders"


class MustHaveTAPreference(BasePreference):
    """Must-have TAs with preference order"""
    class Meta:
        unique_together = ['ta_request', 'ta']
        ordering = ['preference_order']
        verbose_name = "Must-have TA"
        verbose_name_plural = "Must-have TAs"


class AvoidTAPreference(BasePreference):
    """TAs to avoid with preference/priority order"""
    class Meta:
        unique_together = ['ta_request', 'ta']
        ordering = ['preference_order']
        verbose_name = "TA to Avoid"
        verbose_name_plural = "TAs to Avoid"


class AvoidGraderPreference(BasePreference):
    """Graders to avoid with preference/priority order"""
    class Meta:
        unique_together = ['ta_request', 'ta']
        ordering = ['preference_order']
        verbose_name = "Grader to Avoid"
        verbose_name_plural = "Graders to Avoid"