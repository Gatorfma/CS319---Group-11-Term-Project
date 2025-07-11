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

class AssignTAFormExcell(forms.Form):
    excell_file = forms.FileField(
        label="Upload Excell File"
    )
# New form for editing users
class CustomUserEditForm(forms.ModelForm):
    # Add TA-specific fields
    max_workload = forms.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-input", "step": "0.5"})
    )
    max_absent_days = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-input"})
    )
    
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
            "is_active",
            "is_staff",
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
            "is_active":    forms.CheckboxInput(attrs={"class": "form-checkbox"}),
            "is_staff":     forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If this is an existing TA user, populate the TA-specific fields
        if self.instance and self.instance.pk and self.instance.role == CustomUser.Roles.TA:
            try:
                ta_profile = self.instance.ta_profile
                self.fields['max_workload'].initial = ta_profile.max_workload
                self.fields['max_absent_days'].initial = ta_profile.max_absent_days
            except Exception:
                # Handle the case where the TA profile might not exist yet
                pass