from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from accounts.models import TAProfile
from courses.models import CourseOffering

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "employee_id",
            "department",
            "phone_number",
        ]
        widgets = {
            "username":     forms.TextInput(attrs={"class": "form-input"}),
            "email":        forms.EmailInput(attrs={"class": "form-input"}),
            "first_name":   forms.TextInput(attrs={"class": "form-input"}),
            "last_name":    forms.TextInput(attrs={"class": "form-input"}),
            "role":         forms.Select(attrs={"class": "form-select"}),
            "employee_id":  forms.TextInput(attrs={"class": "form-input"}),
            "department":   forms.TextInput(attrs={"class": "form-input"}),
            "phone_number": forms.TextInput(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Style the password fields as well
        self.fields["password1"].widget.attrs.update({"class": "form-input"})
        self.fields["password2"].widget.attrs.update({"class": "form-input"})

class AssignTAForm(forms.Form):
    ta = forms.ModelChoiceField(queryset=TAProfile.objects.filter(is_active=True))
    course_offerings = forms.ModelChoiceField(
        queryset=CourseOffering.objects.all(),
        label="Course Offering"
    )