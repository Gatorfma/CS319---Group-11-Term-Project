from django.urls import path
from .views import (
    LeaveRequestCreateView,
    LeaveRequestListView,
    ManageLeaveRequestListView,
    swap_request_view,
    SwapRequestListView,
    approve_leave_view,
    reject_leave_view,
    review_swap_requests_view
)
from django.views.generic import TemplateView

app_name = 'ta_requests'

urlpatterns = [
    path('leave/request/', LeaveRequestCreateView.as_view(), name='leave-request'),
    path('leave/approve/<int:pk>/', approve_leave_view, name='leave-approve'),
    path('leave/reject/<int:pk>/', reject_leave_view, name='leave-reject'),
    path('leave/list/', LeaveRequestListView.as_view(), name='leave-list'),
    path('leave/manage/', ManageLeaveRequestListView.as_view(), name='leave-manage'),
    path('swap/request/', swap_request_view,   name='swap-request'),
    path('swap/review/', review_swap_requests_view, name='swap-review'),
    path('swap/list/',    SwapRequestListView.as_view(), name='swap-list'),
]