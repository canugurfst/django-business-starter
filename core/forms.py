from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    # Honeypot: hidden from people with CSS, but naive spam bots fill in every
    # field. A filled-in value means the submission is silently dropped.
    # Cheaper than a CAPTCHA and invisible to real visitors.
    website = forms.CharField(required=False, label="Leave this field empty")

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 6})}

    def is_spam(self):
        return bool(self.cleaned_data.get("website"))
