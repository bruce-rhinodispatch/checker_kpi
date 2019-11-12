from django import forms


class DateForm(forms.Form):
    start = forms.DateTimeField(input_formats=['%m/%d/%Y'], required=True)
    end = forms.DateTimeField(input_formats=['%m/%d/%Y'], required=True)
    start.widget.attrs.update({'id': 'start', 'placeholder': "Select start date", 'autocomplete': 'off'})
    end.widget.attrs.update({'id': 'end', 'placeholder': "Select end date", 'autocomplete': 'off'})

