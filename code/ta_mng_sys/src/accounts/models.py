from django.contrib.auth.models import AbstractUser
from django.db import models

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
    employee_id  = models.CharField(max_length=20, blank=True, null=True)
    department   = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

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
 

    # …add helpers for other roles if you like…
