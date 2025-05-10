from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView
from .forms import AssignTAForm
from django.shortcuts import render, redirect
from courses.models import CourseOffering
from django.contrib import messages

from .models import CustomUser
from .forms import CustomUserCreationForm

def is_admin_user(user):
    return user.is_authenticated and user.role in {
        CustomUser.Roles.SECRETARY,
        CustomUser.Roles.DEPT_CHAIR,
        CustomUser.Roles.DEAN,
        CustomUser.Roles.ADMIN,
    }

def assign_ta_to_courses(request):
    if request.method == "POST":
        form = AssignTAForm(request.POST)
        if form.is_valid():
            ta = form.cleaned_data['ta']
            selected_courses = form.cleaned_data['course_offerings']

            # Update both sides of the relationship
            ta.assigned_course_offerings.add(selected_courses)
            selected_courses.tas.add(ta)  # update the CourseOffering model side too

            messages.success(request, f"{ta} has been successfully assigned to the selected courses.")
            form = AssignTAForm()  # Reset form after success
    else:
        form = AssignTAForm()

    return render(request, 'accounts/assign_ta_to_courses.html', {'form': form})

@login_required
def instructor_ta_workload_view(request):
    instructor = request.user

    # Ensure the user is an instructor
    if instructor.role != instructor.Roles.INSTRUCTOR:
        return render(request, 'accounts/login.html')

    # Get course offerings where the user is one of the instructors
    course_offerings = CourseOffering.objects.filter(
        instructors=instructor
    ).prefetch_related('tas__user')

    context = {
        'course_offerings': course_offerings,
    }
    return render(request, 'accounts/ta_workloads.html', context)

@method_decorator([login_required, user_passes_test(is_admin_user)], name="dispatch")
class UserListView(ListView):
    model = CustomUser
    template_name = "accounts/user_list.html"
    context_object_name = "users"

@method_decorator([login_required, user_passes_test(is_admin_user)], name="dispatch")
class UserCreateView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")
