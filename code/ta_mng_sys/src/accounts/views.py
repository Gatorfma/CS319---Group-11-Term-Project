from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView
from .forms import AssignTAForm, AssignTAFormExcell
from django.shortcuts import render
from courses.models import CourseOffering
from accounts.models import TAProfile
from django.contrib import messages
import openpyxl

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

def assign_ta_to_courses_excell(request):
    success_count = 0
    errors = []

    if request.method == "POST":
        form = AssignTAFormExcell(request.POST, request.FILES)
        if form.is_valid():
            excell_file = form.cleaned_data['excell_file']
            if not excell_file.name.endswith('.xlsx'):
                errors.append("Please upload a valid .xlsx file.")
            else:
                try:
                    wb = openpyxl.load_workbook(excell_file)
                    sheet = wb.active
                    department_codes = []
                    course_codes = []
                    sections = []
                    semesters = []

                    for cell in sheet[1][1:]:  # Skip column A (index 0)
                        if cell.value:
                            try:
                                code_part, section, semester = cell.value.split('-')
                                dept, course = code_part.strip().split(' ')
                                department_codes.append(dept)
                                course_codes.append(course)
                                sections.append(section.strip())
                                semesters.append(semester.strip())
                            except Exception:
                                department_codes.append(None)
                                course_codes.append(None)
                                sections.append(None)
                                semesters.append(None)
                        else:
                            department_codes.append(None)
                            course_codes.append(None)
                            sections.append(None)
                            semesters.append(None)

                    # Iterate over TA rows
                    for row in sheet.iter_rows(min_row=2, values_only=True):
                        ta_name = row[0]
                        if not ta_name:
                            continue

                        for i, cell_value in enumerate(row[1:]):
                            if cell_value in (1, 2):
                                try:
                                    course_offering = CourseOffering.objects.get(
                                        course__department_code=department_codes[i],
                                        course__course_code=course_codes[i],
                                        section=sections[i],
                                        semester=semesters[i]
                                    )
                                except CourseOffering.DoesNotExist:
                                    errors.append(f"Course offering not found for: {department_codes[i]} {course_codes[i]} {sections[i]} {semesters[i]}")
                                    continue

                                try:
                                    ta = CustomUser.objects.get(username=ta_name)
                                    if ta.role != CustomUser.Roles.TA:
                                        errors.append(f"{ta_name} is not a TA.")
                                        continue
                                except CustomUser.DoesNotExist:
                                    errors.append(f"TA {ta_name} does not exist.")
                                    continue

                                # Add relationship both ways
                                ta = TAProfile.objects.get(user=ta)
                                ta.assigned_course_offerings.add(course_offering)
                                course_offering.tas.add(ta)
                                success_count += 1

                except Exception as e:
                    errors.append(f"Unexpected error: {e}")

            if success_count > 0:
                messages.success(request, f"{success_count} TA-course assignments completed successfully.")
            elif not errors:
                messages.warning(request, "No TA assignments were made.")
            form = AssignTAFormExcell()  # Reset form

    else:
        form = AssignTAFormExcell()

    return render(request, 'accounts/assign_ta_to_courses_excell.html', {
        'form': form,
        'errors': errors
    })


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
