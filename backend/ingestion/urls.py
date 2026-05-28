from django.urls import path
from . import views

urlpatterns = [
    path('sap/', views.SAPUploadView.as_view()),
    path('utility/', views.UtilityUploadView.as_view()),
    path('travel/', views.TravelUploadView.as_view()),
    path('batches/', views.BatchListView.as_view()),
]
