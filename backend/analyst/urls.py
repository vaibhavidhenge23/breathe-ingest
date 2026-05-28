from django.urls import path
from . import views

urlpatterns = [
    path('records/', views.RecordListView.as_view()),
    path('records/<int:record_id>/', views.RecordDetailView.as_view()),
    path('records/<int:record_id>/approve/', views.ApproveRecordView.as_view()),
    path('bulk-approve/', views.BulkApproveView.as_view()),
    path('summary/', views.DashboardSummaryView.as_view()),
]
