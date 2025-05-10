from django import forms
from django.utils import timezone
from .models import LeaveRequest, SwapRequest
from django.contrib.contenttypes.models import ContentType
from duties.models import ProctoringDuty

class DutySwapForm(forms.Form):
    my_duty = forms.ModelChoiceField(
        queryset=ProctoringDuty.objects.none(),
        label="Step 1: Select Your Duty",
        widget=forms.RadioSelect(attrs={'class': 'form-input'})
    )
    other_duty = forms.ModelChoiceField(
        queryset=ProctoringDuty.objects.none(),
        label="Step 2: Select Duty to Swap With",
        widget=forms.RadioSelect(attrs={'class': 'form-input'})
    )
    reason = forms.CharField(
        label="Reason",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Why do you need this swap?',
            'class': 'form-textarea'
        }),
        required=True
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is None or not hasattr(user, 'ta_profile'):
            return

        today = timezone.now().date()
        ta = user.ta_profile

        # Your upcoming proctoring duties
        self.fields['my_duty'].queryset = ProctoringDuty.objects.filter(
            assigned_ta=ta,
            date__gte=today
        ).order_by('date', 'start_time')

        # All other TAs’ upcoming duties
        self.fields['other_duty'].queryset = ProctoringDuty.objects.filter(
            date__gte=today
        ).exclude(
            assigned_ta=ta
        ).order_by('date', 'start_time')

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'reason': forms.Textarea(attrs={'class': 'form-textarea'}),
        }

        
    def clean_start_date(self):
        sd = self.cleaned_data['start_date']
        if sd < timezone.now().date():
            raise forms.ValidationError("Geçmiş tarih seçilemez.")
        return sd
    def clean(self):
        cd = super().clean()
        sd, ed = cd.get('start_date'), cd.get('end_date')
        if sd and ed and ed < sd:
            raise forms.ValidationError("Bitiş tarihi, başlangıçtan önce olamaz.")
        return cd

class ProcessSwapRequestForm(forms.Form):
    swap_id = forms.IntegerField(widget=forms.HiddenInput())
    action  = forms.ChoiceField(
        choices=[('approve','Approve'), ('reject','Reject')],
        widget=forms.HiddenInput()
    )