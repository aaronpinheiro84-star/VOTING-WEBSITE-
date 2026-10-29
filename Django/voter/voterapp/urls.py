from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.registration, name='register'),
    path('login/', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path("vote/", views.vote, name="vote"),
    path('results/', views.results, name='results'),
    path('logout/', views.logout, name='logout'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path("vote-receipt/", views.vote_receipt, name="vote_receipt"),

    # Your premium dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('test-email/', views.test_email),
]