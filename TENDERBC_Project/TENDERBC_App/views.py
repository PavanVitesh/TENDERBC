import time
from django.shortcuts import render, redirect
from .forms import UserForm, TenderForm, ChgPwdForm, BidForm
from .models import Tender, Bid, User
from .security_utils import save_dkey_to_chain, save_to_chain, add_tender_data_to_chain, retreive_tender_dkeys_from_chain
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from TENDERBC_Project import settings
from django.core.mail import send_mail
# pattern: send_mail(subject,mail body, from mail -> app mail id given in settings.py at last check (settings.EMAIL_HOST_USER),list of mail ids to which mail has to be sent)
# example: # send_mail("Welcome to TENDERBC","Registartion Successful",settings.EMAIL_HOST_USER,[request.user.email])


# Create your views here.
def Home(request):
    tends = Tender.objects.all()
    for i in tends:
        if i.start_date_time > timezone.now():
            i.Status = "Inactive"
            i.save()
        elif i.start_date_time <= timezone.now() <= i.end_date_time:
            i.Status = "Active"
            i.save()
        elif timezone.now() <= i.end_date_time + timezone.timedelta(seconds=120):
            i.Status = "Key Submission"
            i.save()
        elif i.Status != "Granted":
            i.Status = "Completed"
            bid_ids = Bid.objects.filter(tender_id=i.id).values_list('id', flat=True)
            i.save()
    if request.method == "POST"  and request.POST['keyword'] != "":
        active_tenders = Tender.objects.filter(title__icontains=request.POST['keyword'], description__icontains=request.POST['keyword'], Status='Active')
        inactive_tenders = Tender.objects.filter(title__icontains=request.POST['keyword'], description__icontains=request.POST['keyword'], Status='Inactive')
        keysubmission_tenders = Tender.objects.filter(title__icontains=request.POST['keyword'], description__icontains=request.POST['keyword'], Status='Key Submission')
        completed_tenders = Tender.objects.filter(title__icontains=request.POST['keyword'], description__icontains=request.POST['keyword'], Status='Completed')
    else:
        active_tenders = Tender.objects.filter(Status='Active')
        inactive_tenders = Tender.objects.filter(Status='Inactive')
        keysubmission_tenders = Tender.objects.filter(Status='Key Submission')
        completed_tenders = Tender.objects.filter(Status='Completed')
    return render (request,'html/home.html',{"active_tenders":active_tenders,"inactive_tenders":inactive_tenders,'completed_tenders':completed_tenders, 'keysubmission_tenders':keysubmission_tenders})

def Register(request):
    userform = UserForm()
    if request.method == 'POST':
        userform=UserForm(data=request.POST)
        if userform.is_valid():
            userform.save()
            messages.success(request, 'Registration Successful. Please login to continue.')
            mail_service("Welcome to TENDERBC!", "Thank you for registering to TENDERBC you can now use it to submit your bids for tenders", User.objects.get(username=request.POST['username']).id)
            return redirect('/login/')
        else:
            messages.error(request, userform.errors.popitem()[1][0])
    return render(request,'html/register.html',{'userform':userform})

def Login(request):
    if request.method == 'POST':
        uname = request.POST['username']
        pwd = request.POST['password']
        from django.contrib.auth import authenticate, login
        user = authenticate(username=uname, password=pwd)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login Successful')
            return redirect('/')
        else:
            if not request.user.is_superuser:
                mail_service("Login Alert! Invalid Credentials", "You have made an invalid attempt to login \nNot You? \n Protect your account by changing password!", request.user.id)
            messages.error(request, 'Invalid Credentials')
    return render(request,'html/login.html')

def Profile(request,x):
    user_details = User.objects.get(id=x)
    return render (request,'html/profile.html',{'user_details':user_details})

def Change_Password(request):
    if request.method == "POST":
        n = ChgPwdForm(user=request.user,data=request.POST)
        if n.is_valid():
            n.save()
            messages.success(request, 'Password Changed Successfully')
            mail_service("Changed Password Sucessfully!", "Account Password Changed successfully", request.user.id)
            return redirect('/login/')
        else:
            messages.error(request, n.errors.popitem()[1][0])
    n = ChgPwdForm(user=request)
    return render(request,'html/changepassword.html',{'h':n})

def Create_Tender(request):
    if request.method == 'POST':
        ctform=TenderForm(request.POST, request.FILES)
        print(request.POST)
        if ctform.is_valid():
            ctform = ctform.save()
            try: 
                add_tender_data_to_chain(ctform.id, ctform.start_date_time, ctform.end_date_time)
                messages.success(request, 'Tender created successfully')
                return redirect('../')
            except BaseException as e: 
                ctform.delete()
                messages.error(request, e)
                print(e)
        else:
            messages.error(request, ctform.errors.popitem()[1][0])

    ctform = TenderForm()
    return render (request,'html/create_tender.html',{'ctform':ctform})

def View_Tender(request,x):
    details = Tender.objects.get(id=x)
    dkey = ""
    if request.method == 'POST':
        if details.Status == 'Active':
            bidsubmission = BidForm(request.POST, request.FILES)
            if bidsubmission.is_valid():
                bidsubmission = bidsubmission.save(commit=False)
                filename = str(bidsubmission.document)
                bidsubmission.bidder_id = request.user.id
                bidsubmission.tender_id = x
                bidsubmission.save()
                try:
                    outputpath, dkey = save_to_chain(filename, bidsubmission.tender_id, bidsubmission.bidder_id)
                    bidsubmission.document = outputpath
                    bidsubmission.save()
                    messages.success(request, 'Your bid has been submitted successfully, and the Secret Key has been downloaded. Please keep it safe for later use.')
                    mail_service("Bid submission successfull!", "You have submitted you bid for following Tender: " + "\nTitle: "+ details.title + "\nDescription: " + detais.description + "\nExpiry: " + details.end_date_time, request.user.id)
                    messages.success(request, "")
                except:
                    bidsubmission.delete()
                    messages.error(request, 'Error while saving to blockchain')
                    mail_service("Bid submission failed!", "Your bid submission for following Tender: " + "\nTitle: "+ details.title + "\nDescription: " + detais.description + "\nExpiry: " + details.end_date_time + "\nis Failed! please resubmit your bid", request.user.id)
        if details.Status == 'Key Submission':
            secret_key = request.POST.get('secret_key')
            if not secret_key:
                messages.error(request, 'Secret Key')
            else:
                try:
                    save_dkey_to_chain(x, request.user.id, secret_key)
                    messages.success(request, 'Secret Key uploaded successfully')
                    mail_service("Key submission successfull!", "You have submitted secret key for you bid successfully", request.user.id)
                except BaseException as e:
                    messages.error(request, e)
                    mail_service("Key submission Failed!", "Secret Key submission failed due to following error\n" + e, request.user.id)
                    
                
    bidsubmission = BidForm()
    alreadysubmitted = False
    bids_submitted_to_this_tender = Bid.objects.filter(tender_id=x)
    if details.Status == 'Completed':
        tampered_bidder_ids = retreive_tender_dkeys_from_chain(x, list(Bid.objects.filter(tender_id=x).values_list('bidder_id', flat=True)))
        print("tampered ", tampered_bidder_ids)
        if not tampered_bidder_ids:
            tampered_bidder_ids = []
        for i in bids_submitted_to_this_tender:
            if i.bidder_id in tampered_bidder_ids:
                i.Status = "Ignored"
                i.save()
    my_bid = None
    for  i in bids_submitted_to_this_tender:
        if i.bidder_id == request.user.id:
            alreadysubmitted = True
            my_bid = i
            break
    if request.method == 'POST' and details.Status == 'Key Submission':
        return redirect('/ViewTender/'+str(x))
    return render(request, 'html/view_tender.html', {'details':details,'bidsubmission':bidsubmission,'alreadysubmitted':alreadysubmitted,'bids_submitted_to_this_tender':bids_submitted_to_this_tender,'my_bid':my_bid, 'dkey':dkey})


def Past_Tenders(request):
    completed_tendrs = Tender.objects.filter(Status="Completed")
    granted_tenders = Tender.objects.filter(Status="Granted")
    return render(request, 'html/past_tenders.html',{'completed_tendrs':completed_tendrs,'granted_tenders':granted_tenders})

def Past_Bids(request):
    list_tenders = list(Bid.objects.filter(bidder_id=request.user.id).values_list('tender_id', flat=True))
    submitted_tenders = Tender.objects.filter(id__in=list_tenders)
    return render(request, 'html/past_bids.html',{'submitted_tenders':submitted_tenders})

def Accept_Bid(request,x):
    bid_details = Bid.objects.get(id=x)
    tender_details = Tender.objects.get(id=bid_details.tender_id)
    all_bids = Bid.objects.filter(tender_id=bid_details.tender_id)
    for i in all_bids:
        if i.Status == "Ignored":
            mail_service("Bid Ignored!", "Bid submitted to following tender is IGNORED!!!" + "\nTitle: "+ tender_details.title + "\nDescription: " + tender_detais.description + "\nExpiry: " + tender_details.end_date_time, i.bidder_id)
        else:
            i.Status = "Rejected"
            i.save()
            if i.bidder_id != bid_details.bidder_id:
                mail_service("Bid Rejected!", "Bid submitted to following tender is REJECTED!!!" + "\nTitle: "+ tender_details.title + "\nDescription: " + tender_detais.description + "\nExpiry: " + tender_details.end_date_time, i.bidder_id)
    bid_details.Status = "Accepted"
    bid_details.save()
    mail_service("Bid Accepted!", "Bid submitted to following tender is ACCEPTED!!!" + "\nTitle: "+ tender_details.title + "\nDescription: " + tender_detais.description + "\nExpiry: " + tender_details.end_date_time, bid_details.bidder_id)
    tender_details.Status = "Granted"
    bidder_name = User.objects.get(id=bid_details.bidder_id).username
    messages.success(request, bidder_name + ' has been granted the tender')
    tender_details.save()
    return redirect('../ViewTender/'+str(bid_details.tender_id))



def mail_service(subject, description, userid):
    user_obj = User.objects.get(id=userid)
    body = f"Dear {user_obj.username},\n\n{description}\n\nRegards,\nTENDERBC"
    send_mail(subject, body, settings.EMAIL_HOST_USER, [user_obj.email])
