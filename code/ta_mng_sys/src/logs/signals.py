from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

# Import your models
from duties.models import ProctoringDuty 
from ta_requests.models import SwapRequest, LeaveRequest
from courses.models import Exam, Classroom, CourseOffering
from accounts.models import TAProfile, CustomUser

from .utils import log_action
from .middleware import get_current_user

User = get_user_model()

# User creation and modification
@receiver(post_save, sender=CustomUser)
def log_user_actions(sender, instance, created, **kwargs):
    """Log when users are created or updated"""
    current_user = get_current_user()
    user = current_user if current_user else instance
    
    if created:
        log_action(
            user=user,
            action=f"User '{instance.username}' was created",
            model_name="User",
            object_id=instance.id
        )
    else:
        log_action(
            user=user,
            action=f"User '{instance.username}' was updated",
            model_name="User",
            object_id=instance.id
        )

# User deletion
@receiver(post_delete, sender=CustomUser)
def log_user_deletion(sender, instance, **kwargs):
    """Log when users are deleted"""
    current_user = get_current_user()
    
    log_action(
        user=current_user,
        action=f"User '{instance.username}' was deleted",
        model_name="User",
        object_id=instance.id
    )

# TA Profile changes
@receiver(post_save, sender=TAProfile)
def log_ta_profile_changes(sender, instance, created, **kwargs):
    """Log when TA profiles are created or updated"""
    current_user = get_current_user()
    
    if created:
        log_action(
            user=current_user,
            action=f"TA profile for {instance.user.username} was created",
            model_name="TAProfile",
            object_id=instance.id
        )
    else:
        log_action(
            user=current_user,
            action=f"TA profile for {instance.user.username} was updated",
            model_name="TAProfile",
            object_id=instance.id
        )

# Course offering changes
@receiver(post_save, sender=CourseOffering)
def log_course_offering_changes(sender, instance, created, **kwargs):
    """Log when course offerings are created or updated"""
    current_user = get_current_user()
    
    if created:
        log_action(
            user=current_user,
            action=f"Course offering {instance} was created",
            model_name="CourseOffering",
            object_id=instance.id
        )
    else:
        log_action(
            user=current_user,
            action=f"Course offering {instance} was updated",
            model_name="CourseOffering",
            object_id=instance.id
        )

# Exam changes
@receiver(post_save, sender=Exam)
def log_exam_changes(sender, instance, created, **kwargs):
    """Log when exams are created or updated"""
    current_user = get_current_user()
    
    if created:
        log_action(
            user=current_user,
            action=f"Exam for {instance.course} was created",
            model_name="Exam",
            object_id=instance.id
        )
    else:
        log_action(
            user=current_user,
            action=f"Exam for {instance.course} was updated",
            model_name="Exam",
            object_id=instance.id
        )

# Duty creation and updates
@receiver(post_save, sender=ProctoringDuty)
def log_proctoring_duty_save(sender, instance, created, **kwargs):
    """Log when proctoring duties are created or updated"""
    action_type = "created" if created else "updated"
    
    if created:
        log_action(
            user=instance.created_by,
            action=f"Proctoring duty {action_type} for {instance.exam} on {instance.date}",
            model_name="ProctoringDuty",
            object_id=instance.id
        )
    else:
        # Use the current user from middleware for updates
        current_user = get_current_user()
        if current_user:
            log_action(
                user=current_user,
                action=f"Proctoring duty {action_type}",
                model_name="ProctoringDuty",
                object_id=instance.id
            )

# Log when TAs are assigned to course offerings
@receiver(m2m_changed, sender=TAProfile.assigned_course_offerings.through)
def log_ta_course_assignment(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Log when TAs are assigned to or removed from course offerings"""
    current_user = get_current_user()
    
    if action == 'post_add':
        for pk in pk_set:
            course = CourseOffering.objects.get(pk=pk)
            log_action(
                user=current_user,
                action=f"TA {instance.user.username} assigned to course {course}",
                model_name="TAProfile",
                object_id=instance.id
            )
    
    elif action == 'post_remove':
        for pk in pk_set:
            try:
                course = CourseOffering.objects.get(pk=pk)
                course_name = str(course)
            except CourseOffering.DoesNotExist:
                course_name = f"ID: {pk} (deleted)"
                
            log_action(
                user=current_user,
                action=f"TA {instance.user.username} removed from course {course_name}",
                model_name="TAProfile",
                object_id=instance.id
            )

# Swap requests
@receiver(post_save, sender=SwapRequest)
def log_swap_request(sender, instance, created, **kwargs):
    """Log when swap requests are created or updated"""
    if created:
        log_action(
            user=instance.from_ta.user,
            action=f"Created swap request from {instance.from_ta} to {instance.to_ta}",
            model_name="SwapRequest",
            object_id=instance.id
        )
    elif instance.status != 'P':  # If status changed from pending
        if instance.processed_by:
            status_map = {'A': 'approved', 'R': 'rejected', 'C': 'canceled'}
            status_text = status_map.get(instance.status, instance.status)
            
            log_action(
                user=instance.processed_by,
                action=f"Swap request {status_text} by {instance.processed_by}",
                model_name="SwapRequest",
                object_id=instance.id
            )
        elif instance.to_ta and instance.to_ta.user:
            log_action(
                user=instance.to_ta.user,
                action=f"Swap request responded by {instance.to_ta}",
                model_name="SwapRequest",
                object_id=instance.id
            )

# Leave requests
@receiver(post_save, sender=LeaveRequest)
def log_leave_request(sender, instance, created, **kwargs):
    """Log when leave requests are created or updated"""
    if created:
        current_user = get_current_user()
        log_action(
            user=current_user,
            action=f"Created leave request for {instance.start_date} to {instance.end_date}",
            model_name="LeaveRequest",
            object_id=instance.id
        )
    elif instance.processed_by:
        status_map = {'A': 'approved', 'R': 'rejected', 'C': 'canceled', 'P': 'pending'}
        status_text = status_map.get(instance.status, instance.status)
        
        log_action(
            user=instance.processed_by,
            action=f"Leave request {status_text} by {instance.processed_by}",
            model_name="LeaveRequest",
            object_id=instance.id
        )