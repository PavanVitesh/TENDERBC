from django.shortcuts import render, redirect
from .forms import UserForm
from django.contrib import messages


# Create your views here.
def Home(request):
    return render (request,'html/home.html')

def Register(request):
    if request.method == 'POST':
        userform=UserForm(data=request.POST)
        if userform.is_valid():
            userform.save()
        messages.success(request,"Registeration Sucessfull!")
        return redirect('/register/')
    userform = UserForm()
    return render(request,'html/register.html',{'userform':userform})

def Adminhome(request):
    return render (request,'html/home.html')
