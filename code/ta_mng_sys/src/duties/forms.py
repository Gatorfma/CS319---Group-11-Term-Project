from django import forms

from courses.models import Exam


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