from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView
from .forms import AssignTAForm
from django.shortcuts import render, redirect

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
            ta.assigned_course_offerings.set(selected_courses)
            for course in selected_courses:
                course.tas.add(ta)  # update the CourseOffering model side too

            return redirect('ta-assignment-success')  # You can define this route later
    else:
        form = AssignTAForm()

    return render(request, 'accounts/assign_ta_to_courses.html', {'form': form})

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
