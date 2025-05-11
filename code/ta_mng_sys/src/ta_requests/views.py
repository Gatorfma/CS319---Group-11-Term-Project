from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from .models import LeaveRequest, SwapRequest
from .forms import LeaveRequestForm
from accounts.models import CustomUser
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .forms  import DutySwapForm
from duties.models import ProctoringDuty
from .forms import ProcessSwapRequestForm

@login_required
def review_swap_requests_view(request):
    # only TAs see swaps addressed to them
    if request.user.role != 'TA':
        return redirect('home')

    swaps = SwapRequest.objects.filter(
        to_ta=request.user.taprofile,
        status=SwapRequest.Status.PENDING
    )

    if request.method == 'POST':
        swap_id = request.POST['swap_id']
        action  = request.POST['action']
        swap    = get_object_or_404(SwapRequest, id=swap_id)

        if action == 'approve':
            swap.status = SwapRequest.Status.APPROVED
            swap.responded_at = timezone.now()
            swap.processed_by = request.user
            swap.save()

            # actually swap the duty assignment
            duty = swap.duty
            duty.assigned_ta = swap.to_ta.user
            duty.save()


        elif action == 'reject':
            swap.status = SwapRequest.Status.REJECTED
            swap.responded_at = timezone.now()
            swap.processed_by = request.user
            swap.save()

        return redirect('ta_requests:swap-review')

    return render(request, 'ta_requests/review_swap_requests.html', {
        'swap_requests': swaps
    })
    
class TAOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'ta_profile')


@login_required
def swap_request_view(request):
    # only TAs may open this page
    if not hasattr(request.user, 'ta_profile'):
        return redirect('home')

    if request.method == 'POST':
        form = DutySwapForm(request.POST, user=request.user)
        if form.is_valid():
            my_duty    = form.cleaned_data['my_duty']
            other_duty = form.cleaned_data['other_duty']
            reason     = form.cleaned_data['reason']

            SwapRequest.objects.create(
                duty_content_type=ContentType.objects.get_for_model(ProctoringDuty),
                duty_object_id  = my_duty.id,
                from_ta         = request.user.ta_profile,
                to_ta           = other_duty.assigned_ta,
                reason          = reason
            )
            return redirect('ta_requests:swap-list')
    else:
        form = DutySwapForm(user=request.user)

    return render(request, 'ta_requests/swap_request_form.html', {
        'form': form
    })

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

class SwapRequestListView(LoginRequiredMixin, ListView):
    model               = SwapRequest
    template_name       = 'ta_requests/swap_request_list.html'
    context_object_name = 'requests'
    paginate_by         = 10

    def get_queryset(self):
        return SwapRequest.objects.filter(
            from_ta=self.request.user.ta_profile
        ).order_by('-requested_at')

class LeaveRequestCreateView(LoginRequiredMixin, TAOnlyMixin, CreateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'ta_requests/leave_request_form.html'
    success_url = reverse_lazy('ta_requests:leave-list')

    def form_valid(self, form):
        form.instance.ta_profile = self.request.user.ta_profile
        return super().form_valid(form)

class LeaveRequestListView(LoginRequiredMixin, TAOnlyMixin, ListView):
    model = LeaveRequest
    template_name = 'ta_requests/leave_request_list.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        # Show only this TA’s own requests
        return LeaveRequest.objects.filter(
            ta_profile=self.request.user.ta_profile
        ).order_by('-submitted_at')

class ManageLeaveRequestListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = LeaveRequest
    template_name = 'ta_requests/leave_request_manage.html'
    context_object_name = 'requests'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_instructor()


    def get_queryset(self):
        return LeaveRequest.objects.all().order_by('-submitted_at')

@login_required
def approve_leave_view(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = LeaveRequest.Status.APPROVED
    leave.processed_by = request.user
    leave.processed_at = timezone.now()
    leave.save()
    return redirect('ta_requests:leave-manage')

@login_required
def reject_leave_view(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = LeaveRequest.Status.REJECTED
    leave.processed_by = request.user
    leave.processed_at = timezone.now()
    leave.save()
    return redirect('ta_requests:leave-manage')

@login_required
def review_swap_requests_view(request):
    # Sadece TA'lar erişsin
    if not hasattr(request.user, 'ta_profile'):
        return redirect('home')

    # Bekleyen swap isteklerini al (status 'P' → Pending)
    pending = SwapRequest.objects.filter(
        to_ta=request.user.ta_profile,
        status=SwapRequest.Status.PENDING
    )

    if request.method == 'POST':
        # istersen form üzerinden de çekebilirsin:
        # form = ProcessSwapRequestForm(request.POST)
        # if form.is_valid():
        #     swap_id = form.cleaned_data['swap_id']
        #     action  = form.cleaned_data['action']
        swap_id = request.POST.get('swap_id')
        action  = request.POST.get('action')

        swap = get_object_or_404(
            SwapRequest,
            id=swap_id,
            to_ta=request.user.ta_profile,
            status=SwapRequest.Status.PENDING
        )

        # Karar ve kaydetme
        swap.status       = SwapRequest.Status.APPROVED if action == 'approve' else SwapRequest.Status.REJECTED
        swap.processed_by = request.user
        swap.responded_at = timezone.now()
        swap.save()

        if action == 'approve':
            # Gerçek swap: duty atamasını değiştir
            duty = swap.duty  # GenericForeignKey ile gelen ProctoringDuty vb.
            duty.assigned_ta = swap.from_ta
            duty.save()
            # log_action(request.user, "Swap Approved", f"Swap#{swap.id} approved")
        else:
            # log_action(request.user, "Swap Rejected", f"Swap#{swap.id} rejected")

            return redirect('ta_requests:swap-review')

    return render(request, 'ta_requests/review_swap_requests.html', {
        'swap_requests': pending})