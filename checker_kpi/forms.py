from django import forms


class DateForm(forms.Form):
    start = forms.DateTimeField(input_formats=['%m/%d/%Y'])
    end = forms.DateTimeField(input_formats=['%m/%d/%Y'])
    start.widget.attrs.update({'id': 'start', 'placeholder': "Select start date"})
    end.widget.attrs.update({'id': 'end', 'placeholder': "Select end date"})

