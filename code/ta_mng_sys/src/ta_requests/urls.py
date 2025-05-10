from django.urls import path
from .views import LeaveRequestCreateView, SwapRequestCreateView
from django.views.generic import TemplateView

app_name = 'ta_requests'

urlpatterns = [
    path('leave/request/', LeaveRequestCreateView.as_view(), name='leave-request'),
    path('leave/success/', TemplateView.as_view(
            template_name='ta_requests/leave_success.html'),
         name='leave-success'),

    path('swap/request/', SwapRequestCreateView.as_view(), name='swap-request'),
    path('swap/success/', TemplateView.as_view(
            template_name='ta_requests/swap_success.html'),
         name='swap-success'),
]
