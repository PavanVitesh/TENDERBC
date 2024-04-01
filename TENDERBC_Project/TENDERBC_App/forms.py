from django import forms
from .models import User, Tender, Bid
from django.contrib.auth.forms import UserCreationForm,PasswordChangeForm
from datetime import datetime

class UserForm(UserCreationForm):
	password1 = forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control my-2","placeholder":"Password"}))
	password2 = forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control my-2","placeholder":"Re-Enter Password"}))
	class Meta:
		model = User
		fields = ["username", "email", "mobile", "company_type", "regno", "address", "establishment_year"]
		widgets = {
		"username":forms.TextInput(attrs={
			"class":"form-control my-2",
			"placeholder":"Username",
			}),
		"email":forms.TextInput(attrs={
			"class":"form-control my-2",
			"placeholder":"Email",
			}),
		"mobile":forms.NumberInput(attrs={
			"class":"form-control my-2",
			"placeholder":"Mobile Number"}),
		"company_type":forms.Select(attrs={
			"class":"form-control my-2",
			}),
		"regno":forms.TextInput(attrs={
			"class":"form-control my-2",
			"placeholder":"Registration Number"
        }),
		"address":forms.TextInput(attrs={
			"class":"form-control my-2",
			"placeholder":"Address"
        }),
		"establishment_year":forms.Select(attrs={
			"class":"form-control my-2"
        })
		}

class TenderForm(forms.ModelForm):
    class Meta:
        model = Tender
        fields = ["title", "description", "document", "start_date_time", "end_date_time"]
        widgets ={
            "title":forms.TextInput(attrs={"class":"form-control my-2","placeholder":"Title"}),
            "description":forms.TextInput(attrs={"class":"form-control my-2","placeholder":"description"}),
            "start_date_time":forms.DateInput(attrs={"type":"datetime-local","class":"form-control my-2","placeholder":"End","min":datetime.today()}),
            "end_date_time":forms.DateInput(attrs={"type":"datetime-local","class":"form-control my-2","placeholder":"End","min":datetime.today()}),
		}

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ["document"]

class ChgPwdForm(PasswordChangeForm):
	old_password = forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control my-2","placeholder":"Old Password"}))
	new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control my-2","placeholder":"New Password"}))
	new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control my-2","placeholder":"Password Again"}))
	class Meta:
		model = User
		fields = "__all__"