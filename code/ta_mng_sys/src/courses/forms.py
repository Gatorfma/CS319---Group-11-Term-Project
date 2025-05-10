from django import forms

class UploadExcelForm(forms.Form):
    excel_file = forms.FileField(
        label="Select Excel File",
        required=True,
        widget=forms.ClearableFileInput(attrs={'accept': '.xlsx'}))
