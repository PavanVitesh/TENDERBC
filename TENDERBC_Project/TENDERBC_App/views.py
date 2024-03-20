from django.shortcuts import render, redirect
from .forms import UserForm, TenderForm
from .models import Tender
from django.utils import timezone
from django.contrib import messages
from django.utils import timezone


# Create your views here.
def Home(request):
    tends = Tender.objects.all()
    for i in tends:
        print(i.start_date_time , timezone.now() , i.end_date_time)
        if i.start_date_time <= timezone.now() <= i.end_date_time:
            i.Status = "Active"
            i.save()
        elif i.end_date_time < timezone.now():
            i.Status = "Completed"
            i.save()
    active_tenders = Tender.objects.filter(Status='Active')
    inactive_tenders = Tender.objects.filter(Status='Inactive')
    return render (request,'html/home.html',{"active_tenders":active_tenders,"inactive_tenders":inactive_tenders})

def Register(request):
    if request.method == 'POST':
        userform=UserForm(data=request.POST)
        if userform.is_valid():
            userform.save()
        return redirect('/register/')
    userform = UserForm()
    return render(request,'html/register.html',{'userform':userform})

def Create_Tender(request):
    if request.method == 'POST':
        ctform=TenderForm(request.POST, request.FILES)
        print(request.POST)
        if ctform.is_valid():
            ctform.save()
        return redirect('/Create Tender/')
    ctform = TenderForm()
    return render (request,'html/create_tender.html',{'ctform':ctform})

def View_Tender(request,x):
    details = Tender.objects.get(id=x)
    return render(request, 'html/view_tender.html', {'details':details})
