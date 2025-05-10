from django import forms
from .models import Exam, Classroom

class UploadExcelForm(forms.Form):
    excel_file = forms.FileField(
        label="Select Excel File",
        required=True,
        widget=forms.ClearableFileInput(attrs={'accept': '.xlsx'}))
    classroom_selection = forms.ModelMultipleChoiceField(
        queryset=Classroom.objects.all(),
        label="Select Classrooms",
        widget=forms.CheckboxSelectMultiple  # or use SelectMultiple for dropdown
    )