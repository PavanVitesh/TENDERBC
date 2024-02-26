from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm,PasswordChangeForm
from datetime import date

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