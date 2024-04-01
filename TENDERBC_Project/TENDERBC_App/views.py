from django.shortcuts import render, redirect
from .forms import UserForm, TenderForm, ChgPwdForm, BidForm
from .models import Tender, Bid, User
from .security_utils import save_to_chain, retreive_from_chain
from django.utils import timezone
from django.contrib import messages
from django.utils import timezone


# Create your views here.
def Home(request):
    tends = Tender.objects.all()
    for i in tends:
        if i.start_date_time <= timezone.now() <= i.end_date_time:
            i.Status = "Active"
            i.save()
        elif i.end_date_time < timezone.now() and i.Status != "Granted":
            i.Status = "Completed"
            bid_ids = Bid.objects.filter(tender_id=i.id).values_list('id', flat=True)
            tamper_bid_ids = retreive_from_chain(i.id, list(bid_ids))
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

def Profile(request,x):
    user_details = User.objects.get(id=x)
    return render (request,'html/profile.html',{'user_details':user_details})


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
        return redirect('/CreateTender/')
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
            outputpath = save_to_chain(bidsubmission.document, bidsubmission.tender_id, bidsubmission.id, details.end_date_time)
            bisubmission.document = outputpath
            bidsubmission.save()
        return redirect('/')
    bidsubmission = BidForm()
    alreadysubmitted = False
    bids_submitted_to_this_tender = Bid.objects.filter(tender_id=x)
    for  i in bids_submitted_to_this_tender:
        if i.bidder_id == request.user.id:
            alreadysubmitted = True
            my_bid = i
            break
    return render(request, 'html/view_tender.html', {'details':details,'bidsubmission':bidsubmission,'alreadysubmitted':alreadysubmitted,'bids_submitted_to_this_tender':bids_submitted_to_this_tender,'my_bid':my_bid})


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
        i.Status = "Rejected"
        i.save()
    bid_details.Status = "Accepted"
    bid_details.save()
    tender_details.Status = "Granted"
    tender_details.save()
    return redirect('../ViewTender/'+str(bid_details.tender_id))