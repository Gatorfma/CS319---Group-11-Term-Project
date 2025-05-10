from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        TA           = "TA",         "Teaching Assistant"
        INSTRUCTOR   = "INSTRUCTOR", "Instructor"
        SECRETARY    = "SECRETARY",  "Secretary"
        DEPT_CHAIR   = "DEPT_CHAIR",  "Department Chair"
        DEAN         = "DEAN",       "Dean"
        ADMIN        = "ADMIN",      "Administrator"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.TA,
        help_text="Determines menu items & permissions."
    )
    @property
    def admin_roles(self):
        return {
            self.Roles.SECRETARY,
            self.Roles.DEPT_CHAIR,
            self.Roles.DEAN, 
            self.Roles.ADMIN
        }
    employee_id  = models.CharField(max_length=20, blank=True, null=True)
    department   = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def get_ta_profile(self):
        """
        Helper method to easily access TA profile if it exists
        """
        if self.is_ta():
            return self.ta_profile
        return None

    def is_ta(self):
        return self.role == self.Roles.TA
    def is_instructor(self):
        return self.role == self.Roles.INSTRUCTOR
    def is_secretary(self):
        return self.role == self.Roles.SECRETARY
    def is_dept_chair(self):
        return self.role == self.Roles.DEPT_CHAIR
    def is_dean(self):
        return self.role == self.Roles.DEAN
    def is_admin(self):
        return self.role == self.Roles.ADMIN
 

class TAProfile(models.Model):
    """
    Profile model for Teaching Assistants (TAs) containing TA-specific attributes and relationships.
    """
    class TAType(models.TextChoices):
        PHD = "PHD", "PhD Student"
        GRAD = "GRAD", "Graduate Student"

    class ProctorType(models.IntegerChoices):
        NO_PROCTORING = 0, "Cannot proctor any exam"
        ASSIGNED_COURSES_ONLY = 1, "Can only proctor assigned courses"
        ALL_COURSES = 2, "Can proctor any exam"

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='ta_profile'
    )

    # TA Type and Status Fields
    ta_type = models.CharField(
        max_length=4,
        choices=TAType.choices,
        default=TAType.GRAD
    )
    is_active = models.BooleanField(default=True)
    is_assignable = models.BooleanField(default=True)
    proctor_type = models.IntegerField(
        choices=ProctorType.choices,
        default=ProctorType.NO_PROCTORING
    )

    # Workload Related Fields
    total_workload = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0
    )
    max_workload = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=-1
    )
    max_absent_days = models.IntegerField(default=-1)

    # Relationship Fields
    assigned_course_offerings = models.ManyToManyField(
        'courses.CourseOffering',
        related_name='assigned_tas',
        blank=True
    )
    enrolled_course_offerings = models.ManyToManyField(
        'courses.CourseOffering',
        related_name='enrolled_tas',
        blank=True
    )

    # These will be implemented once the respective models are created
    """
    assigned_duties = models.ManyToManyField(
        'duties.Duty',
        related_name='assigned_tas',
        blank=True,
        help_text="List of duties assigned to this TA"
    )

    leave_requests = models.ManyToManyField(
        'leaves.LeaveRequest',
        related_name='requesting_ta',
        blank=True,
        help_text="Leave requests made by this TA"
    )

    swap_requests = models.ManyToManyField(
        'duties.SwapRequest',
        related_name='involved_tas',
        blank=True,
        help_text="Duty swap requests involving this TA"
    )
    """

    class Meta:
        verbose_name = "TA Profile"
        verbose_name_plural = "TA Profiles"

    def __str__(self):
        return f"TA Profile: {self.user.get_full_name() or self.user.username}"

    def can_proctor_course(self, course_offering):
        if not self.is_active or not self.is_assignable:
            return False
        if self.proctor_type == self.ProctorType.ALL_COURSES:
            return True
        elif self.proctor_type == self.ProctorType.ASSIGNED_COURSES_ONLY:
            return course_offering in self.assigned_course_offerings.all()
        return False

    def has_workload_capacity(self, additional_hours):
        if self.max_workload == -1:
            return True
        return (self.total_workload + additional_hours) <= self.max_workload



class InstructorProfile(models.Model):
    """
    Profile model for Instructors containing instructor-specific attributes and relationships.
    This model extends the base CustomUser model through a one-to-one relationship.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='instructor_profile'
    )

    is_faculty = models.BooleanField(
        default=True,
        help_text="Indicates if the instructor is a faculty member"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Indicates if instructor is active in the current semester"
    )

    # Relationship Fields
    assigned_course_offerings = models.ManyToManyField(
        'courses.CourseOffering',
        related_name='assigned_instructors',
        blank=True,
        help_text="Course offerings this instructor is teaching"
    )

    # These will be implemented once the respective models are created
    """
    leave_requests = models.ManyToManyField(
        'leaves.LeaveRequest',
        related_name='approving_instructor',
        blank=True,
        help_text="Leave requests assigned to this instructor for approval"
    )

    duties_assigned = models.ManyToManyField(
        'duties.Duty',
        related_name='assigning_instructor',
        blank=True,
        help_text="Duties created/assigned by this instructor"
    )
    """

    class Meta:
        verbose_name = "Instructor Profile"
        verbose_name_plural = "Instructor Profiles"

    def __str__(self):
        return f"Instructor Profile: {self.user.get_full_name() or self.user.username}"

    def can_approve_leave_requests(self):
        """
        Checks if instructor can approve leave requests
        """
        return self.is_active and self.is_faculty

# Add to CustomUser class
def get_instructor_profile(self):
    """
    Helper method to easily access instructor profile if it exists
    """
    if self.is_instructor():
        return self.instructor_profile
    return None



# Add after InstructorProfile class
class StaffProfile(models.Model):
    """
    Common profile model for administrative staff roles (Secretary, Dean, Department Chair).
    Contains shared attributes and functionality for staff members.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='staff_profile'
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Indicates if staff member is currently active"
    )

    # These will be implemented once the respective models are created
    """
    leave_requests_to_process = models.ManyToManyField(
        'leaves.LeaveRequest',
        related_name='processing_staff',
        blank=True,
        help_text="Leave requests pending this staff member's review"
    )
    """

    class Meta:
        verbose_name = "Staff Profile"
        verbose_name_plural = "Staff Profiles"

    def __str__(self):
        return f"{self.user.get_role_display()} Profile: {self.user.get_full_name() or self.user.username}"

    def can_process_requests(self):
        """
        Checks if staff member can process requests
        """
        return self.is_active

# Add to CustomUser class
def get_staff_profile(self):
    """
    Helper method to easily access staff profile if it exists
    """
    if self.is_secretary() or self.is_dean() or self.is_dept_chair():
        return self.staff_profile
    return None

class Student(models.Model):
    """
    Represents a student who may be enrolled in one or more course offerings.
    Students are not system users and do not log into the system.
    """
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    enrolled_courses = models.ManyToManyField(
        'courses.CourseOffering',
        related_name='enrolled_students',
        blank=True,
        help_text="Courses this student is enrolled in."
    )

    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
        ordering = ['student_id']


@receiver(post_save, sender=CustomUser)
def create_or_update_user_profiles(sender, instance, created, **kwargs):
    if instance.role == CustomUser.Roles.TA:
        TAProfile.objects.get_or_create(user=instance)
    elif instance.role == CustomUser.Roles.INSTRUCTOR:
        InstructorProfile.objects.get_or_create(user=instance)
    elif instance.role in [
        CustomUser.Roles.SECRETARY,
        CustomUser.Roles.DEAN,
        CustomUser.Roles.DEPT_CHAIR
    ]:
        StaffProfile.objects.get_or_create(user=instance)

