from django import forms
from django.contrib import messages
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import TAProfile
from datetime import timedelta
from courses.models import Classroom, Exam
from duties.models import ProctoringDuty
from duties.forms import AutoProctoringAssignmentForm
from decimal import Decimal

# Create your views here.
def is_time_conflict(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1


def auto_assign_proctors_view(request):
    if not (request.user.is_instructor() or request.user.is_secretary() or request.user.is_dept_chair()):
        return redirect('home')

    if request.method == 'POST':
        form = AutoProctoringAssignmentForm(request.POST)
        if form.is_valid():
            exam = form.cleaned_data['exam']
            num_needed = exam.num_proctors_required

            override_msphd = form.cleaned_data['override_msphd']
            override_proctor_type_0 = form.cleaned_data['override_proctor_type_0']
            override_proctor_type_1 = form.cleaned_data['override_proctor_type_1']
            override_same_day = form.cleaned_data['override_same_day']

            result, message, selected_ta_ids = perform_auto_assignment(
                exam, num_needed,
                override_msphd, override_proctor_type_0, override_proctor_type_1, override_same_day
            )

            if result:
                request.session['exam_id'] = exam.id
                request.session['selected_ta_ids'] = selected_ta_ids
                messages.success(request, message)
                return redirect('duties:assign_classrooms', exam_id=exam.id)
            else:
                messages.error(request, str(message))
    else:
        exam_id = request.GET.get("exam_id")
        if exam_id:
            form = AutoProctoringAssignmentForm(initial={"exam": exam_id})
        else:
            form = AutoProctoringAssignmentForm()


    return render(request, 'duties/auto_assign_proctors.html', {'form': form})

def assign_classrooms_view(request, exam_id):
    if not (request.user.is_instructor() or request.user.is_secretary() or request.user.is_dept_chair()):
        return redirect('home')

    exam = get_object_or_404(Exam, id=exam_id)
    selected_ta_ids = request.session.get('selected_ta_ids')
    if not selected_ta_ids:
        return HttpResponseBadRequest("No TA assignment data found.")

    selected_tas = TAProfile.objects.filter(id__in=selected_ta_ids)
    classrooms = exam.classroom.all()

    if request.method == 'POST':
        ProctoringDuty.objects.filter(exam=exam).delete()
        exam.assigned_tas.clear()
        for ta in selected_tas:
            classroom_id = request.POST.get(f'classroom_{ta.id}')
            if not classroom_id:
                continue
            classroom = get_object_or_404(Classroom, id=classroom_id)


            ProctoringDuty.objects.create(
                course=exam.course,
                date=exam.date,
                start_time=exam.start_time,
                end_time=exam.end_time,
                duration_hours=int(exam.duration.total_seconds() // 3600),
                created_by=request.user,
                assigned_ta=ta,
                exam=exam,
                classroom=classroom
            )

            exam.assigned_tas.add(ta)
            ta.total_workload += Decimal(exam.duration.total_seconds()) / Decimal('3600')

            ta.save()

        messages.success(request, "Classrooms and duties assigned successfully.")
        return redirect('home')

    return render(request, 'duties/assign_classrooms.html', {
        'exam': exam,
        'selected_tas': selected_tas,
        'classrooms': classrooms,
    }) 



def perform_auto_assignment(exam, num_proctors, override_msphd=False, override_proctor_type_0=False,
                            override_proctor_type_1=False, override_same_day=False):
    eligible_tas = []
    rejected_tas = []

    exam_date = exam.date
    start = exam.start_time
    end = exam.end_time
    duration_hours = exam.duration.total_seconds() / 3600.0
    offering = exam.course  # Tek bir course var

    all_tas = TAProfile.objects.filter(is_active=True, is_assignable=True).select_related('user')

    for ta in all_tas:
        user = ta.user

        # 1. Leave kontrolü
        if ta.leave_requests.filter(start_date__lte=exam_date, end_date__gte=exam_date, status='A').exists():
            rejected_tas.append((ta, 'On leave'))
            continue

        # 2. Enrolled course conflict
        if offering in ta.enrolled_course_offerings.values_list('course', flat=True):
            rejected_tas.append((ta, 'Enrolled in course'))
            continue

        # 3. Zaman çakışan başka exam var mı?
        # TA'nın kayıtlı olduğu derslerin course objelerini topla
        enrolled_courses = ta.enrolled_course_offerings.values_list('course', flat=True)

        # Aynı gün sınavı olan ve bu derslere ait exam'leri bul
        enrolled_exams = Exam.objects.filter(
            course__in=enrolled_courses,
            date=exam_date
        ).distinct()

        # Zaman çakışması kontrolü
        conflict1 = False
        for e in enrolled_exams:
            if is_time_conflict(start, end, e.start_time, e.end_time):
                rejected_tas.append((ta, 'Conflict with enrolled course exam'))
                conflict1 = True
                break

        if conflict1:
            continue

        proctorings = ProctoringDuty.objects.filter(
            assigned_ta=ta,
            date=exam_date
        ).select_related('exam')

        conflict2 = False
        for duty in proctorings:
            other_exam = duty.exam
            if is_time_conflict(start, end, other_exam.start_time, other_exam.end_time):
                rejected_tas.append((ta, 'Already assigned to another proctoring'))
                conflict2 = True
                break

        if conflict2:
            continue 
           
        # 4. Aynı gün başka iş var mı?
        if not override_same_day:
            # TA'nın kayıtlı olduğu course_offering'lerden aynı güne denk gelen exam var mı?
            same_day_enrolled_exam_exists = Exam.objects.filter(
            course__in=ta.enrolled_course_offerings.values_list('course', flat=True),
            date=exam_date
            ).exists()

            # Aynı gün içinde atanmış başka bir proctoring duty var mı?
            same_day_proctoring_exists = ProctoringDuty.objects.filter(
                assigned_ta=ta,
                date=exam_date
            ).exists()

            if same_day_enrolled_exam_exists or same_day_proctoring_exists:
                rejected_tas.append((ta, 'Already has exam/proctoring on this day'))
                continue

        # 5. MS/PhD kontrolü
        if not override_msphd and exam.course.course_code >= 500 and ta.ta_type != TAProfile.TAType.PHD:
            rejected_tas.append((ta, 'Not eligible for MS course'))
            continue

        # 6. Proctor type kontrolleri
        if ta.proctor_type == TAProfile.ProctorType.NO_PROCTORING and not override_proctor_type_0:
            rejected_tas.append((ta, 'Proctoring not allowed'))
            continue

        if ta.proctor_type == TAProfile.ProctorType.ASSIGNED_COURSES_ONLY and \
                not ta.assigned_course_offerings.filter(course=exam.course).exists() and \
                not override_proctor_type_1:
            rejected_tas.append((ta, 'Only assigned courses allowed'))
            continue


        eligible_tas.append(ta)

    def priority_key(ta):
        # PRIMARY: assigned_course_offering → course_id eşleşiyorsa 0
        if ta.assigned_course_offerings.filter(course=exam.course).exists():
            primary = 0
        # DEPARTMENT eşleşiyorsa 1
        elif ta.user.department == exam.course.department_code:
            primary = 1
        # Hiçbiri değilse 2
        else:
            primary = 2

        # SECONDARY: Adjacent günlerde başka proctoring varsa 1, yoksa 0
        adjacent_days = [exam_date - timedelta(days=1), exam_date + timedelta(days=1)]
        has_adjacent = ProctoringDuty.objects.filter(
            assigned_ta=ta,
            date__in=adjacent_days
        ).exists()
        secondary = 1 if has_adjacent else 0

        # TERTIARY: Workload
        tertiary = float(ta.total_workload)

        return (primary, secondary, tertiary)

    sorted_eligible = sorted(eligible_tas, key=priority_key)
    final_tas = sorted_eligible[:num_proctors]

    if len(final_tas) < num_proctors:
        return False, f"Only {len(final_tas)} eligible TAs found. Consider overriding restrictions.", []

   
    selected_ta_ids = [ta.id for ta in final_tas]
    return True, f"Successfully assigned {len(final_tas)} TAs to exam.", selected_ta_ids



def manual_assign_proctors_view(request, exam_id): 
    if not (request.user.is_instructor() or request.user.is_secretary() or request.user.is_dept_chair()):
        return redirect('home')

    exam = get_object_or_404(Exam, id=exam_id)
    exam_date = exam.date
    exam_course = exam.course

    all_tas = TAProfile.objects.filter(is_active=True).select_related('user').prefetch_related(
        'enrolled_course_offerings', 'assigned_course_offerings'
    )

    eligible_tas = []
    restricted_tas = []

    for ta in all_tas:
        restricted_reason = None

        if ta.leave_requests.filter(start_date__lte=exam_date, end_date__gte=exam_date, status='A').exists():
            restricted_reason = 'On leave'
        elif ta.enrolled_course_offerings.filter(course=exam_course).exists():
            restricted_reason = 'Enrolled in course'
        elif exam_course.course_code >= 500 and ta.ta_type != TAProfile.TAType.PHD:
            restricted_reason = 'Not eligible for MS/PHD course'
        elif ta.proctor_type == TAProfile.ProctorType.NO_PROCTORING:
            restricted_reason = 'Not allowed to proctor (type 0)'
        elif ta.proctor_type == TAProfile.ProctorType.ASSIGNED_COURSES_ONLY and \
                not ta.assigned_course_offerings.filter(course=exam_course).exists():
            restricted_reason = 'Only allowed to proctor assigned courses (type 1)'

        if restricted_reason:
            restricted_tas.append((ta, restricted_reason))
        else:
            eligible_tas.append(ta)

    def priority_key(ta):
        if ta.assigned_course_offerings.filter(course=exam_course).exists():
            primary = 0
        elif ta.user.department == exam_course.department_code:
            primary = 1
        else:
            primary = 2

        adjacent_days = [exam_date - timedelta(days=1), exam_date + timedelta(days=1)]
        has_adjacent = ProctoringDuty.objects.filter(
            assigned_ta=ta,
            date__in=adjacent_days
        ).exists()

        secondary = 1 if has_adjacent else 0
        tertiary = float(ta.total_workload)

        return (primary, secondary, tertiary)

    eligible_tas_sorted = sorted(eligible_tas, key=priority_key)

    class ManualProctorAssignmentForm(forms.Form):
        tas = forms.ModelMultipleChoiceField(
            queryset=TAProfile.objects.filter(
                id__in=[ta.id for ta in eligible_tas_sorted] + [ta.id for ta, _ in restricted_tas]
            ),
            widget=forms.CheckboxSelectMultiple,
            required=False  # Bu önemli!
        )

        def clean_tas(self):
            tas = self.cleaned_data.get('tas')
            if not tas or len(tas) != self.num_required:
                raise forms.ValidationError(
                    f"You must select exactly {self.num_required} TAs."
                )
            return tas

        def __init__(self, *args, **kwargs):
            self.num_required = kwargs.pop('num_required')
            super().__init__(*args, **kwargs)

    ta_display_list = []
    for ta in eligible_tas_sorted:
        ta_display_list.append((ta.id, f"{ta.user.username} ({ta.total_workload}h workload)"))
    for ta, reason in restricted_tas:
        ta_display_list.append((ta.id, f"\u26a0\ufe0f {ta.user.username} ({reason})"))

    if request.method == 'POST':
        form = ManualProctorAssignmentForm(request.POST, num_required=exam.num_proctors_required)
        if form.is_valid():
            selected_tas = form.cleaned_data['tas']
            request.session['exam_id'] = exam.id
            request.session['selected_ta_ids'] = [ta.id for ta in selected_tas]
            return redirect('duties:assign_classrooms', exam_id=exam.id)
        # Hatalıysa aynı sayfaya hata mesajıyla dön
        return render(request, 'duties/manual_assign_proctors.html', {
            'form': form,
            'exam': exam,
            'ta_display_list': ta_display_list,
        })
    else:
        form = ManualProctorAssignmentForm(num_required=exam.num_proctors_required)

    return render(request, 'duties/manual_assign_proctors.html', {
        'form': form,
        'exam': exam,
        'ta_display_list': ta_display_list,
    })



def select_exam_for_manual_assignment(request):
    if not (request.user.is_instructor() or request.user.is_secretary() or request.user.is_dept_chair()):
        return redirect('home')
    exams = Exam.objects.all()

    return render(request, 'duties/select_exam_for_manual_assignment.html', {
        'exams': exams
    })


def manage_exam_assignments_view(request):
    exams = Exam.objects.select_related('course').prefetch_related('assigned_tas', 'classroom')

    exam_data = []
    for exam in exams:
        assigned_count = ProctoringDuty.objects.filter(exam=exam).count()
        status = "Assigned" if assigned_count > 0 else "Unassigned"

        exam_data.append({
            'exam': exam,
            'assigned_count': assigned_count,
            'status': status,
        })

    return render(request, 'duties/manage_exam_assignments.html', {
        'exam_data': exam_data,
    })

def edit_exam_assignment_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    exam_date = exam.date
    exam_course = exam.course

    all_tas = TAProfile.objects.filter(is_active=True).select_related('user').prefetch_related(
        'enrolled_course_offerings', 'assigned_course_offerings'
    )

    eligible_tas = []
    restricted_tas = []
    previously_assigned = list(exam.assigned_tas.all())

    for ta in all_tas:
        restricted_reason = None

        if ta.leave_requests.filter(start_date__lte=exam_date, end_date__gte=exam_date, status='A').exists():
            restricted_reason = 'On leave'
        elif ta.enrolled_course_offerings.filter(course=exam_course).exists():
            restricted_reason = 'Enrolled in course'
        elif exam_course.course_code >= 500 and ta.ta_type != TAProfile.TAType.PHD:
            restricted_reason = 'Not eligible for MS/PHD course'
        elif ta.proctor_type == TAProfile.ProctorType.NO_PROCTORING:
            restricted_reason = 'Not allowed to proctor (type 0)'
        elif ta.proctor_type == TAProfile.ProctorType.ASSIGNED_COURSES_ONLY and \
                not ta.assigned_course_offerings.filter(course=exam_course).exists():
            restricted_reason = 'Only allowed to proctor assigned courses (type 1)'

        if restricted_reason:
            restricted_tas.append((ta, restricted_reason))
        else:
            eligible_tas.append(ta)

    def priority_key(ta):
        if ta.assigned_course_offerings.filter(course=exam_course).exists():
            primary = 0
        elif ta.user.department == exam_course.department_code:
            primary = 1
        else:
            primary = 2

        adjacent_days = [exam_date - timedelta(days=1), exam_date + timedelta(days=1)]
        has_adjacent = ProctoringDuty.objects.filter(
            assigned_ta=ta,
            date__in=adjacent_days
        ).exists()

        secondary = 1 if has_adjacent else 0
        tertiary = float(ta.total_workload)

        return (primary, secondary, tertiary)

    eligible_tas_sorted = sorted(eligible_tas, key=priority_key)

    ta_display_list = []
    for ta in eligible_tas_sorted:
        ta_display_list.append((ta.id, f"{ta.user.username} ({ta.total_workload}h workload)"))
    for ta, reason in restricted_tas:
        ta_display_list.append((ta.id, f"\u26a0\ufe0f {ta.user.username} ({reason})"))

    class ManualProctorEditForm(forms.Form):
        tas = forms.ModelMultipleChoiceField(
            queryset=TAProfile.objects.filter(
                id__in=[ta.id for ta in eligible_tas_sorted] + [ta.id for ta, _ in restricted_tas]
            ),
            widget=forms.CheckboxSelectMultiple,
            required=False,
            initial=[ta.id for ta in previously_assigned]
        )

        def __init__(self, *args, **kwargs):
            self.num_required = kwargs.pop('num_required')
            super().__init__(*args, **kwargs)

        def clean_tas(self):
            tas = self.cleaned_data.get('tas')
            if not tas or len(tas) != self.num_required:
                raise forms.ValidationError(
                    f"You must select exactly {self.num_required} TAs."
                )
            return tas

    if request.method == 'POST':
        form = ManualProctorEditForm(request.POST, num_required=exam.num_proctors_required)
        if form.is_valid():
            selected_tas = form.cleaned_data['tas']
            request.session['selected_ta_ids'] = [ta.id for ta in selected_tas]
            request.session['exam_id'] = exam.id

            previous_map = {
                str(duty.assigned_ta.id): duty.classroom.id
                for duty in exam.proctoring_duties.all()
            }
            request.session['previous_classroom_map'] = previous_map

            return redirect('duties:assign_classrooms', exam_id=exam.id)
    else:
        form = ManualProctorEditForm(num_required=exam.num_proctors_required)

    return render(request, 'duties/edit_exam_assignment.html', {
        'form': form,
        'exam': exam,
        'ta_display_list': ta_display_list,
    })

def manage_exam_assignments_view(request):
    exams = Exam.objects.select_related('course').prefetch_related('assigned_tas', 'classroom')

    exam_data = []
    for exam in exams:
        assigned_count = ProctoringDuty.objects.filter(exam=exam).count()
        status = "Assigned" if assigned_count > 0 else "Unassigned"

        exam_data.append({
            'exam': exam,
            'assigned_count': assigned_count,
            'status': status,
        })

    return render(request, 'duties/manage_exam_assignments.html', {
        'exam_data': exam_data,
    })



def delete_exam_assignments_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    # Sil tüm proctoring duties
    duties = ProctoringDuty.objects.filter(exam=exam)
    for duty in duties:
        ta = duty.assigned_ta
        if ta:
            ta.total_workload -= duty.duration_hours
            ta.save()
    duties.delete()

    # Temizle exam.assigned_tas
    exam.assigned_tas.clear()

    messages.success(request, "All assignments for this exam have been deleted.")
    return redirect('duties:manage_exam_assignments')

# duties/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views import View
from .models import LabDuty, GradingDuty, RecitationDuty, OfficeHourDuty, ProctoringDuty

from datetime import date

def is_instructor_or_staff(user):
    return user.is_authenticated and (user.is_instructor() or user.is_secretary() or user.is_dept_chair() or user.is_dean())

from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from .models import LabDuty, GradingDuty, RecitationDuty, OfficeHourDuty, ProctoringDuty
from .forms import get_duty_form_class

class DutyListView(View):
    def get(self, request):
        user = request.user
        form_class = get_duty_form_class("lab")
        form = form_class(user=user)
        
        # Get courses this instructor is related to
        instructor_courses = []
        if hasattr(user, 'get_instructor_profile') and user.get_instructor_profile():
            instructor_profile = user.get_instructor_profile()
            instructor_courses = instructor_profile.courses.all()
        
        # Get staff managed courses
        staff_courses = []
        if hasattr(user, 'get_staff_profile') and user.get_staff_profile():
            staff_profile = user.get_staff_profile()
            staff_courses = staff_profile.managed_courses.all()
        
        # Combine all relevant courses
        all_relevant_courses = list(instructor_courses) + list(staff_courses)
        
        # Get all course offerings this instructor/staff is related to
        from courses.models import CourseOffering
        relevant_offerings = CourseOffering.objects.filter(course__in=all_relevant_courses)
        
        # Filter duties by both creation and course relevance
        context = {
            "duty_groups": [
                ("Lab Duties", LabDuty.objects.filter(
                    offering__in=relevant_offerings) | LabDuty.objects.filter(created_by=user)),
                ("Grading Duties", GradingDuty.objects.filter(
                    offering__in=relevant_offerings) | GradingDuty.objects.filter(created_by=user)),
                ("Recitation Duties", RecitationDuty.objects.filter(
                    offering__in=relevant_offerings) | RecitationDuty.objects.filter(created_by=user)),
                ("Office Hour Duties", OfficeHourDuty.objects.filter(
                    offering__in=relevant_offerings) | OfficeHourDuty.objects.filter(created_by=user)),
                ("Proctoring Duties", ProctoringDuty.objects.filter(
                    offering__in=relevant_offerings) | ProctoringDuty.objects.filter(created_by=user)),
            ],
            "form": form,
        }
        return render(request, "duties/duty_list.html", context)
        



from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseNotFound
from .models import LabDuty, GradingDuty, RecitationDuty, OfficeHourDuty, ProctoringDuty
from .forms import get_duty_form_class

class DutyDetailView(View):
    DUTY_MODEL_MAP = {
        'lab': LabDuty,
        'grading': GradingDuty,
        'recitation': RecitationDuty,
        'office': OfficeHourDuty,
        'proctoring': ProctoringDuty,
    }

    def get_model(self, duty_type):
        return self.DUTY_MODEL_MAP.get(duty_type)

    def get(self, request, duty_type, duty_id):
        model = self.get_model(duty_type)
        if not model:
            return HttpResponseNotFound("Invalid duty type")
        duty = get_object_or_404(model, id=duty_id)
        form_class = get_duty_form_class(duty_type)
        form = form_class(instance=duty, user=request.user)
        return render(request, "duties/duty_detail.html", {"duty": duty, "form": form})

    def post(self, request, duty_type, duty_id):
        model = self.get_model(duty_type)
        if not model:
            return HttpResponseNotFound("Invalid duty type")
        duty = get_object_or_404(model, id=duty_id)
        form_class = get_duty_form_class(duty_type)
        form = form_class(request.POST, instance=duty, user=request.user)

        if form.is_valid():
            form.save()
            return redirect("duties:detail", duty_type=duty_type, duty_id=duty.id)

        return render(request, "duties/duty_detail.html", {"duty": duty, "form": form})
    
from django.views import View
from django.shortcuts import render, get_object_or_404
from .models import LabDuty, GradingDuty, RecitationDuty, OfficeHourDuty, ProctoringDuty
from .forms import AssignTAsForm  

class AssignTAsView(View):
    MODEL_MAP = {
        'lab': LabDuty,
        'grading': GradingDuty,
        'recitation': RecitationDuty,
        'office': OfficeHourDuty,
        'proctoring': ProctoringDuty,
    }

    def get(self, request, duty_type, duty_id):
        model = self.MODEL_MAP.get(duty_type)
        duty = get_object_or_404(model, id=duty_id)
        form = AssignTAsForm(duty=duty)
        return render(request, 'duties/assign_tas.html', {
            'duty': duty,
            'form': form,
        })

    def post(self, request, duty_type, duty_id):
        model = self.MODEL_MAP.get(duty_type)
        duty = get_object_or_404(model, id=duty_id)
        form = AssignTAsForm(request.POST, duty=duty)
        if form.is_valid():
            form.save()
            return redirect('duties:list')
        return render(request, 'duties/assign_tas.html', {
            'duty': duty,
            'form': form,
        })

# Add this new view class
class CreateDutyView(View):
    def get(self, request):
        user = request.user
        form_class = get_duty_form_class("lab")
        form = form_class(user=user)
        
        # Get querysets needed for dynamic fields
        from courses.models import Exam, Classroom
        
        context = {
            "form": form,
            "exams": Exam.objects.all(),
            "classrooms": Classroom.objects.all(),
        }
        return render(request, "duties/duty_create.html", context)
    
    def post(self, request):
        duty_type = request.POST.get("duty_type")
        form_class = get_duty_form_class(duty_type)
        if not form_class:
            return HttpResponseBadRequest("Invalid duty type")

        form = form_class(request.POST, user=request.user)
        if form.is_valid():
            duty = form.save(commit=False)
            duty.created_by = request.user
            duty.save()
            return redirect("duties:list")

        # Get querysets needed for dynamic fields
        from courses.models import Exam, Classroom
        
        # Re-render with form errors
        context = {
            "form": form,
            "exams": Exam.objects.all(),
            "classrooms": Classroom.objects.all(),
        }
        return render(request, "duties/duty_create.html", context)