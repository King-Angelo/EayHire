from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .forms import SecureUserCreationForm, StudentProfileForm

@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == 'POST':
        form = SecureUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.terms_accepted = True
            user.save()
            return redirect('login')
    else:
        form = SecureUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def student_profile(request):
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect('profile')
    else:
        form = StudentProfileForm()
    return render(request, 'users/profile.html', {'form': form}) 