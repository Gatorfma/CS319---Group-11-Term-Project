from django import forms

from courses.models import Exam

from django import forms
from django.utils.timezone import now
from courses.models import CourseOffering
from duties.models import LabDuty, GradingDuty, RecitationDuty, OfficeHourDuty, ProctoringDuty
from django.db.models import Q

DUTY_MODEL_MAP = {
    'lab':        LabDuty,
    'grading':    GradingDuty,
    'recitation': RecitationDuty,
    'officehour': OfficeHourDuty,
    'proctoring': ProctoringDuty,
}

class DutyLogForm(forms.Form):
    duty_type = forms.ChoiceField(
        label="Duty Type",
        choices=[(k, k.capitalize()) for k in DUTY_MODEL_MAP.keys()],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    offering = forms.ModelChoiceField(
        label="Course & Section",
        queryset=CourseOffering.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    minutes_worked = forms.IntegerField(
        label="Minutes Worked",
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-input'})
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not user or not hasattr(user, 'ta_profile'):
            return
        ta = user.ta_profile

        selected = self.data.get('duty_type')
        if selected in DUTY_MODEL_MAP:
            model_cls     = DUTY_MODEL_MAP[selected]
            duty_qs       = model_cls.objects.filter(assigned_ta=ta)
            offering_ids = duty_qs.values_list('offering_id', flat=True)
            qs = CourseOffering.objects.filter(pk__in=offering_ids)
        else:
            qs = CourseOffering.objects.filter(
                Q(labdutyduties__assigned_ta=ta) |
                Q(gradingdutyduties__assigned_ta=ta) |
                Q(recitationdutyduties__assigned_ta=ta) |
                Q(officehourdutyduties__assigned_ta=ta) |
                Q(proctoringdutyduties__assigned_ta=ta)
            ).distinct()

        self.fields['offering'].queryset = qs.order_by('course__course_code')

        self.fields['offering'].label_from_instance = lambda o: (
            f"{o.course.course_code} – {o.course.title} (Section {o.section})"
        )


class AutoProctoringAssignmentForm(forms.Form):
    exam = forms.ModelChoiceField(
        queryset=Exam.objects.all(),
        label="Exam",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    override_msphd = forms.BooleanField(
        required=False,
        label="Allow MS students to be assigned to MS/PHD courses",
        widget=forms.CheckboxInput(attrs={"class": "form-input"})
    )

    override_proctor_type_0 = forms.BooleanField(
        required=False,
        label="Allow assignment on proctor type 0 TA",
        widget=forms.CheckboxInput(attrs={"class": "form-input"})
    )

    override_proctor_type_1 = forms.BooleanField(
        required=False,
        label="Allow assignment on proctor type 1 TA",
        widget=forms.CheckboxInput(attrs={"class": "form-input"})
    )

    override_same_day = forms.BooleanField(
        required=False,
        label="Allow assignment on proctors with same day exam or proctoring",
        widget=forms.CheckboxInput(attrs={"class": "form-input"})
    )
