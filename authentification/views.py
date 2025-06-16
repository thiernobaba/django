from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import CustomUser
from django.contrib.auth import get_user_model


User = get_user_model()

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Bienvenue, {user.first_name}!')
                return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'authentification/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Compte créé avec succès!')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'authentification/register.html', {'form': form})

@login_required
def dashboard_view(request):
    try:
        if request.user.user_type == 'responsable_filiere':
            return redirect('/res_filiere') 
        elif request.user.user_type == 'responsable_classe':
            return redirect('/responsable_classe/') # URL absolue en dur pour tester
        elif request.user.user_type == 'eleve':
            return redirect('/eleve/') # URL absolue en dur pour tester
        ...
    except Exception as e:
        print(f"Erreur: {str(e)}")  # Debug
        logout(request)
        return redirect('login')

def logout_view(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('login')

@login_required
def profile_view(request):
    return render(request, 'authentification/profile.html', {'user': request.user})