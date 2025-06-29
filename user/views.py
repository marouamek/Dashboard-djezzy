from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User

def login_user(request):
    next_url = request.GET.get('next') or request.POST.get('next')
    # Afficher le message SEULEMENT si on vient d'une redirection (GET avec next)
    if request.method == 'GET' and request.GET.get('next'):
        messages.error(request, "Vous devez être connecté pour accéder à cette page.")
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect')
            return redirect('login_user')
    return render(request, 'login_user.html', {'next': next_url})

def logout_user(request):
    if request.user.is_authenticated:
        referer = request.META.get('HTTP_REFERER', '/')
        if request.method == 'POST':
            logout(request)
            return redirect('home')
    return render(request, 'logout_user.html', {'referer': referer})
