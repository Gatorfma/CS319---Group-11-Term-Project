from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse

from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserEditForm

def is_admin_user(user):
    return user.is_authenticated and user.role in {
        CustomUser.Roles.SECRETARY,
        CustomUser.Roles.DEPT_CHAIR,
        CustomUser.Roles.DEAN,
        CustomUser.Roles.ADMIN,
    }

# Add the custom login view to redirect all users to the home page
class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    
    def get_success_url(self):
        # Redirect everyone to the home page
        return reverse('home')

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
    
    def form_valid(self, form):
        messages.success(self.request, f"User {form.instance.username} was created successfully.")
        return super().form_valid(form)

# Keep your existing edit view
@method_decorator([login_required, user_passes_test(is_admin_user)], name="dispatch")
class UserUpdateView(UpdateView):
    model = CustomUser
    form_class = CustomUserEditForm
    template_name = "accounts/user_edit.html"
    success_url = reverse_lazy("accounts:user_list")
    
    def form_valid(self, form):
        messages.success(self.request, f"User {form.instance.username} was updated successfully.")
        return super().form_valid(form)

# Keep your existing delete view
@method_decorator([login_required, user_passes_test(is_admin_user)], name="dispatch")
class UserDeleteView(DeleteView):
    model = CustomUser
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy("accounts:user_list")
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        messages.success(request, f"User {user.username} was deleted successfully.")
        return super().delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Check if the user is trying to delete themselves
        if self.get_object() == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect("accounts:user_list")
        return super().post(request, *args, **kwargs)