"""
Forms for the Money Tracker app.
"""

from django import forms

class EmailContentForm(forms.Form):
    """Form for pasting email content."""
    source = forms.ChoiceField(
        choices=[('paste', 'Paste Email Content'), ('upload', 'Upload Email File')],
        widget=forms.RadioSelect,
        initial='paste'
    )
    subject = forms.CharField(
        max_length=200, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    from_email = forms.CharField(
        max_length=200, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email_content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        required=False
    )
    email_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    save_to_db = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get('source')
        email_content = cleaned_data.get('email_content')
        email_file = cleaned_data.get('email_file')

        if source == 'paste' and not email_content:
            self.add_error('email_content', 'Please paste email content')
        elif source == 'upload' and not email_file:
            self.add_error('email_file', 'Please upload an email file')

        return cleaned_data

class EmailFetchForm(forms.Form):
    """Form for fetching emails from an email account."""
    email_host = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        initial='imap.gmail.com'
    )
    email_port = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        initial=993
    )
    email_username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    email_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    email_use_ssl = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    bank_email_addresses = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        initial='bankmuscat@bankmuscat.com',
        help_text='Comma-separated list of bank email addresses'
    )
    bank_email_subjects = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        initial='transaction,alert,notification',
        help_text='Comma-separated list of bank email subject keywords'
    )
    folder = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        initial='INBOX'
    )
    unread_only = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    save_to_db = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )