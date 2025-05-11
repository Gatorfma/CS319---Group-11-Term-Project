from django import forms
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import TAProfile
from datetime import timedelta
from courses.models import Classroom, Exam
from duties.models import ProctoringDuty
from duties.forms import AutoProctoringAssignmentForm
from decimal import Decimal

# Import logging functionality
from logs.utils import log_action
from logs.decorators import log_view_action

# Create your views here.
def is_time_conflict(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1


@log_view_action("initiated auto assignment of proctors")
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
                
                # Log successful assignment
                log_action(
                    user=request.user,
                    action=f"Auto-assigned {len(selected_ta_ids)} TAs to exam {exam}",
                    model_name="Exam",
                    object_id=exam.id
                )
                
                messages.success(request, message)
                return redirect('duties:assign_classrooms', exam_id=exam.id)
            else:
                # Log failed assignment
                log_action(
                    user=request.user,
                    action=f"Failed to auto-assign TAs to exam {exam}: {message}",
                    model_name="Exam",
                    object_id=exam.id
                )
                messages.error(request, str(message))
    else:
        exam_id = request.GET.get("exam_id")
        if exam_id:
            form = AutoProctoringAssignmentForm(initial={"exam": exam_id})
        else:
            form = AutoProctoringAssignmentForm()


    return render(request, 'duties/auto_assign_proctors.html', {'form': form})

@log_view_action("assigning classrooms for exam proctoring")
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

        used_classroom_ids = set()
        duplicate = False

        for ta in selected_tas:
            classroom_id = request.POST.get(f'classroom_{ta.id}')
            if not classroom_id:
                continue
            if classroom_id in used_classroom_ids:
                duplicate = True
                break
            used_classroom_ids.add(classroom_id)

        if duplicate:
            messages.error(request, "Each TA must be assigned to a different classroom.")
            return render(request, 'duties/assign_classrooms.html', {
                'exam': exam,
                'selected_tas': selected_tas,
                'classrooms': classrooms,
            })
            
        # Log classroom assignments
        log_action(
            user=request.user,
            action=f"Assigning classrooms for exam {exam}",
            model_name="Exam",
            object_id=exam.id
        )
            
        for ta in selected_tas:
            classroom_id = request.POST.get(f'classroom_{ta.id}')
            if not classroom_id:
                continue
            classroom = get_object_or_404(Classroom, id=classroom_id)

            duty = ProctoringDuty.objects.create(
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

            # Log individual assignment
            log_action(
                user=request.user,
                action=f"Assigned TA {ta.user.username} to proctor in classroom {classroom}",
                model_name="ProctoringDuty",
                object_id=duty.id
            )

            exam.assigned_tas.add(ta)
            ta.total_workload += Decimal(exam.duration.total_seconds()) / Decimal('3600')

            ta.save()

        return redirect('duties:manage_exam_assignments')
        

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
                rejected_tas.append((ta, 'Conflict with enrolled course exam in same hour'))
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
                rejected_tas.append((ta, 'Already assigned to another proctoring in same hour'))
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


@log_view_action("manually assigning proctors")
def manual_assign_proctors_view(request, exam_id): 
    if not (request.user.is_instructor() or request.user.is_secretary() or request.user.is_dept_chair()):
        return redirect('home')

    exam = get_object_or_404(Exam, id=exam_id)
    exam_date = exam.date
    exam_course = exam.course
    start = exam.start_time
    end = exam.end_time

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

        elif Exam.objects.filter(
            course__in=ta.enrolled_course_offerings.values_list('course', flat=True),
            date=exam_date
        ).exists():
            restricted_reason = 'Already has enrolled exam on this day'

        elif ProctoringDuty.objects.filter(
            assigned_ta=ta,
            date=exam_date
        ).exists():
            restricted_reason = 'Already assigned to proctoring on this day'

        else:
            enrolled_exams = Exam.objects.filter(
                course__in=ta.enrolled_course_offerings.values_list('course', flat=True),
                date=exam_date
            ).distinct()

            conflict1 = False
            for e in enrolled_exams:
                if is_time_conflict(start, end, e.start_time, e.end_time):
                    restricted_reason = 'Conflict with enrolled exam at the same hour'
                    conflict1 = True
                    break
            if conflict1:
                restricted_tas.append((ta, restricted_reason))
                continue

            proctorings = ProctoringDuty.objects.filter(
                assigned_ta=ta,
                date=exam_date
            ).select_related('exam')

            conflict2 = False
            for duty in proctorings:
                other_exam = duty.exam
                if is_time_conflict(start, end, other_exam.start_time, other_exam.end_time):
                    restricted_reason = 'Conflict with proctoring duty at the same hour'
                    conflict2 = True
                    break
            if conflict2:
                restricted_tas.append((ta, restricted_reason))
                continue

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

    class ManualProctorAssignmentForm(forms.Form):
        tas = forms.ModelMultipleChoiceField(
            queryset=TAProfile.objects.filter(
                id__in=[ta.id for ta in eligible_tas_sorted] + [ta.id for ta, _ in restricted_tas]
            ),
            widget=forms.CheckboxSelectMultiple,
            required=True
        )

    if request.method == 'POST':
        form = ManualProctorAssignmentForm(request.POST)

        if form.is_valid():
            selected_tas = form.cleaned_data.get('tas', [])

            if not selected_tas or len(selected_tas) != exam.num_proctors_required:
                messages.error(request, f"You must select exactly {exam.num_proctors_required} TAs.")
                return render(request, 'duties/manual_assign_proctors.html', {
                    'form': form,
                    'exam': exam,
                    'ta_display_list': ta_display_list
                })

            request.session['exam_id'] = exam.id
            request.session['selected_ta_ids'] = [ta.id for ta in selected_tas]
            
            # Log manual selection
            log_action(
                user=request.user,
                action=f"Manually selected {len(selected_tas)} TAs for exam {exam}",
                model_name="Exam",
                object_id=exam.id
            )

            return redirect('duties:assign_classrooms', exam_id=exam.id)

    else:
        form = ManualProctorAssignmentForm()

    return render(request, 'duties/manual_assign_proctors.html', {
        'form': form,
        'exam': exam,
        'ta_display_list': ta_display_list,
    })


@log_view_action("selecting exam for manual assignment")
def select_exam_for_manual_assignment(request):
    if not (request.user.is_instructor() or request.user.is_secretary() or request.user.is_dept_chair()):
        return redirect('home')
    exams = Exam.objects.all()

    return render(request, 'duties/select_exam_for_manual_assignment.html', {
        'exams': exams
    })


@log_view_action("editing exam assignment")
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
            required=True,
            initial=[ta.id for ta in previously_assigned]
        )

    if request.method == 'POST':
        form = ManualProctorEditForm(request.POST)
        if form.is_valid():
            selected_tas = form.cleaned_data['tas']
            
            if not selected_tas or len(selected_tas) != exam.num_proctors_required:
                messages.error(request, f"You must select exactly {exam.num_proctors_required} TAs.")
                return render(request, 'duties/edit_exam_assignment.html', {
                    'form': form,
                    'exam': exam,
                    'ta_display_list': ta_display_list
                })
            
            # Store selected TAs and previously assigned classrooms in session
            request.session['selected_ta_ids'] = [ta.id for ta in selected_tas]
            request.session['exam_id'] = exam.id
            
            # Log edit action
            log_action(
                user=request.user,
                action=f"Edited TA assignments for exam {exam}",
                model_name="Exam",
                object_id=exam.id
            )

            return redirect('duties:assign_classrooms', exam_id=exam.id)
    else:
        form = ManualProctorEditForm()


    return render(request, 'duties/edit_exam_assignment.html', {
        'form': form,
        'exam': exam,
        'ta_display_list': ta_display_list,
    })

@log_view_action("viewing exam assignments")
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


@log_view_action("deleting exam assignments")
def delete_exam_assignments_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    # Log deletion action first
    log_action(
        user=request.user,
        action=f"Deleted all TA assignments for exam {exam}",
        model_name="Exam",
        object_id=exam.id
    )

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

    return redirect('duties:manage_exam_assignments')