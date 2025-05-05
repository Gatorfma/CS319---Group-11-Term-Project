from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView

from .models import CustomUser
from .forms import CustomUserCreationForm

def is_admin_user(user):
    return user.is_authenticated and user.role in {
        CustomUser.Roles.SECRETARY,
        CustomUser.Roles.DEPT_CHAIR,
        CustomUser.Roles.DEAN,
        CustomUser.Roles.ADMIN,
    }

@method_decorator([login_required, user_passes_test(is_admin_user)], name="dispatch")
class UserListView(ListView):
    model = CustomUser
    template_name = "accounts/user_list.html"
    context_object_name = "users"

@method_decorator([login_required, user_passes_test(is_admin_user)], name="dispatch")
class UserCreateView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")
