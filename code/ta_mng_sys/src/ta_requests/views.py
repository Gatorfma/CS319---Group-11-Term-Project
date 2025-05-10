from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView
from .forms import LeaveRequestForm, SwapRequestForm
from .models import LeaveRequest, SwapRequest

class TAOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'ta_profile')

class LeaveRequestCreateView(LoginRequiredMixin, TAOnlyMixin, CreateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'ta_requests/leave_request_form.html'
    success_url = reverse_lazy('ta_requests:leave-success')
    def form_valid(self, form):
        form.instance.ta_profile = self.request.user.ta_profile
        return super().form_valid(form)

class SwapRequestCreateView(LoginRequiredMixin, TAOnlyMixin, CreateView):
    model = SwapRequest
    form_class = SwapRequestForm
    template_name = 'ta_requests/swap_request_form.html'
    success_url = reverse_lazy('ta_requests:swap-success')
    def form_valid(self, form):
        form.instance.from_ta = self.request.user.ta_profile
        return super().form_valid(form)
