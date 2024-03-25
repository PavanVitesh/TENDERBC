from django.urls import path
from TENDERBC_App import views
from django.contrib.auth import views as ad


urlpatterns = [
    path('',views.Home,name='hm'),
    path('register/',views.Register,name='rg'),
    path('login/',ad.LoginView.as_view(template_name="html/login.html"),name='ln'),
    path('logout/',ad.LogoutView.as_view(template_name="html/logout.html"),name="lo"),
    path('ChangePassword',views.Change_Password,name='cp'),
    path('CreateTender/',views.Create_Tender,name='ct'),
    path('ViewTender/<int:x>',views.View_Tender,name='vt'),
    path('AcceptBid/<int:x>',views.Accept_Bid,name='ab'),
]