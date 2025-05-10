from django import forms
from django.utils import timezone
from .models import LeaveRequest, SwapRequest

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['start_date','end_date','reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type':'date'}),
            'end_date':   forms.DateInput(attrs={'type':'date'}),
            'reason':     forms.Textarea(attrs={'rows':4}),
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

class SwapRequestForm(forms.ModelForm):
    class Meta:
        model = SwapRequest
        fields = ['duty_content_type','duty_object_id','to_ta','reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows':3}),
        }
