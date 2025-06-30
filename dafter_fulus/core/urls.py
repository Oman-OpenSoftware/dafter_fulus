"""
URL patterns for the Money Tracker app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('parse/', views.parse_email, name='parse_email'),
    path('results/', views.results, name='results'),
    path('accounts/', views.accounts, name='accounts'),
    path('account/<str:account_number>/', views.account_details, name='account_details'),
    path('fetch_emails/', views.fetch_emails, name='fetch_emails'),
]