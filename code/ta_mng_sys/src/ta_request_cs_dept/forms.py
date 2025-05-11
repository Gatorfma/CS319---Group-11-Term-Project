from django import forms
from django.utils import timezone
from .models import TARequest, Semester
from accounts.models import TAProfile, CustomUser
from courses.models import Course

class TARequestForm(forms.ModelForm):
    """Form for instructors to request TAs for their courses"""
    
    # Hidden field for the instructor (set in the view)
    instructor = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role=CustomUser.Roles.INSTRUCTOR),
        widget=forms.HiddenInput(),
        required=False
    )
    
    # Course selection (limited to available courses)
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        empty_label="Select a course",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # TA and grader quantities
    min_ta_loads = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-input'})
    )
    max_ta_loads = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-input'})
    )
    graders_requested = forms.IntegerField(
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-input'})
    )
    
    # Justifications
    must_have_justification = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'placeholder': 'Explain why specific TAs are required'
        })
    )
    
    general_justification = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'placeholder': 'Provide any additional justification for TA/grader requirements'
        })
    )
    
    class Meta:
        model = TARequest
        fields = [
            'instructor', 'course', 'min_ta_loads', 'max_ta_loads',
            'graders_requested', 'must_have_justification', 'general_justification'
        ]
        exclude = ['semester']  # Semester is automatically set based on current active semester

    def __init__(self, *args, **kwargs):
        self.instructor = kwargs.pop('instructor', None)
        self.semester = kwargs.pop('semester', None)
        super().__init__(*args, **kwargs)
        
        if self.instructor:
            # Set the instructor field value
            self.fields['instructor'].initial = self.instructor

    def clean(self):
        cleaned_data = super().clean()
        min_ta_loads = cleaned_data.get('min_ta_loads')
        max_ta_loads = cleaned_data.get('max_ta_loads')
        
        if min_ta_loads is not None and max_ta_loads is not None:
            if min_ta_loads > max_ta_loads:
                raise forms.ValidationError("Minimum TA loads cannot be greater than maximum TA loads.")
        
        # Check if a request already exists for this course this semester
        if not self.instance.pk and self.instructor and self.semester:
            course = cleaned_data.get('course')
            if course and TARequest.objects.filter(
                instructor=self.instructor,
                course=course,
                semester=self.semester
            ).exists():
                raise forms.ValidationError(
                    f"You have already submitted a request for {course.department_code} {str(course.course_code)} this semester. Please edit your existing request."
                )
        
        return cleaned_data


class SemesterForm(forms.ModelForm):
    """Form for managing semesters and request periods"""
    
    class Meta:
        model = Semester
        fields = [
            'name', 'start_date', 'end_date', 
            'request_start_date', 'request_end_date',
            'is_active', 'ta_coordinator'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'start_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'request_start_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'request_end_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'ta_coordinator': forms.Select(attrs={'class': 'form-select'})
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        request_start_date = cleaned_data.get('request_start_date')
        request_end_date = cleaned_data.get('request_end_date')
        
        errors = {}
        
        if start_date and end_date and start_date >= end_date:
            errors['end_date'] = 'End date must be after start date.'
            
        if request_start_date and request_end_date and request_start_date >= request_end_date:
            errors['request_end_date'] = 'Request end date must be after request start date.'
            
        if request_start_date and end_date and request_start_date > end_date:
            errors['request_start_date'] = 'Request start date must be before semester end date.'
            
        if errors:
            raise forms.ValidationError(errors)
            
        return cleaned_data