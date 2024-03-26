from django.shortcuts import render, redirect
from .forms import UserForm, TenderForm, ChgPwdForm, BidForm
from .models import Tender, Bid
# from .forms import save_to_chain, retreive_from_chain
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
        elif i.end_date_time < timezone.now() and i.Status != "Granted":
            i.Status = "Completed"
            # retreive_from_chain(i.id)
            i.save()
    active_tenders = Tender.objects.filter(Status='Active')
    inactive_tenders = Tender.objects.filter(Status='Inactive')
    completed_tenders = Tender.objects.filter(Status='Completed')
    return render (request,'html/home.html',{"active_tenders":active_tenders,"inactive_tenders":inactive_tenders,'completed_tenders':completed_tenders})

def Register(request):
    userform = UserForm()
    if request.method == 'POST':
        userform=UserForm(data=request.POST)
        if userform.is_valid():
            userform.save()
            return redirect('/login/')
    return render(request,'html/register.html',{'userform':userform})


def Change_Password(request):
	if request.method == "POST":
		n = ChgPwdForm(user=request.user,data=request.POST)
		if n.is_valid():
			n.save()
			return redirect('/login/')
	n = ChgPwdForm(user=request)
	return render(request,'html/changepassword.html',{'h':n})

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
    if request.method == 'POST':
        print(request.POST)
        bidsubmission = BidForm(request.POST, request.FILES)
        if bidsubmission.is_valid():
            bidsubmission = bidsubmission.save(commit=False)
            bidsubmission.bidder_id = request.user.id
            bidsubmission.tender_id = x
            bidsubmission.save()
            # outputpath = save_to_chain(input_path)
            # bisubmission.document = outputpath
            # bidsubmission.save()
        return redirect('/')
    bidsubmission = BidForm()
    alreadysubmitted = False
    bids_submitted_to_this_tender = Bid.objects.filter(tender_id=x)
    for  i in bids_submitted_to_this_tender:
        if i.bidder_id == request.user.id:
            alreadysubmitted = True
            break
    return render(request, 'html/view_tender.html', {'details':details,'bidsubmission':bidsubmission,'alreadysubmitted':alreadysubmitted,'bids_submitted_to_this_tender':bids_submitted_to_this_tender})


def Accept_Bid(request,x):
    bid_details = Bid.objects.get(id=x)
    tender_details = Tender.objects.get(id=bid_details.tender_id)
    all_bids = Bid.objects.filter(tender_id=bid_details.tender_id)
    for i in all_bids:
        i.Status = "Rejected"
        i.save()
    bid_details.Status = "Accepted"
    bid_details.save()
    tender_details.Status = "Granted"
    tender_details.save()
    return redirect('../ViewTender/'+str(bid_details.tender_id))