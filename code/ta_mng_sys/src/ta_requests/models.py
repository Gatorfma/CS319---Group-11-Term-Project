from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from accounts.models import TAProfile, CustomUser
from django.utils import timezone

# Create your models here.

class SwapRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'P', 'Pending'
        APPROVED = 'A', 'Approved'
        REJECTED = 'R', 'Rejected'

    duty_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text='Content type for the duty being swapped'
    )
    duty_object_id = models.PositiveIntegerField(
        help_text='Primary key for the duty being swapped'
    )
    duty = GenericForeignKey(
        'duty_content_type',
        'duty_object_id'
    )
    from_ta = models.ForeignKey(
        TAProfile,
        related_name='swap_requests_sent',
        on_delete=models.CASCADE,
        help_text='TA initiating the swap request'
    )
    to_ta = models.ForeignKey(
        TAProfile,
        related_name='swap_requests_received',
        on_delete=models.CASCADE,
        help_text='TA requested to take over the duty'
    )
    reason = models.TextField(
        help_text='Reason for swap'
    )
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.PENDING
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when the request was processed'
    )
    processed_by = models.ForeignKey(
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
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='processed_swap_requests',
        help_text='Staff user who processed the request'
    )

    class Meta:
        ordering = ['-requested_at']
        verbose_name = 'Swap Request'
        verbose_name_plural = 'Swap Requests'

    def __str__(self):
        return f"SwapRequest({self.duty} from {self.from_ta} to {self.to_ta})"


class LeaveRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'P', 'Pending'
        APPROVED = 'A', 'Approved'
        REJECTED = 'R', 'Rejected'

    ta_profile = models.ForeignKey(
        TAProfile,
        on_delete=models.CASCADE,
        related_name='leave_requests',
        help_text='TA requesting leave'
    )
    start_date = models.DateField(
        help_text='First day of leave'
    )
    end_date = models.DateField(
        help_text='Last day of leave'
    )
    reason = models.TextField(
        help_text='Reason for leave request'
    )
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.PENDING,
        help_text='Approval status of the request'
    )
    submitted_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text='Timestamp when request was submitted'
    )
    processed_by = models.ForeignKey(
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
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='processed_leave_requests',
        help_text='Staff user who processed the request'
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when the request was processed'
    )

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'

    def __str__(self):
        return f"LeaveRequest({self.ta_profile.user.get_full_name()} from {self.start_date} to {self.end_date})"