from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import models
import json
from .forms import UserRegistrationForm, UserLoginForm
from .models import Message
from django.contrib.auth.models import User

def register(request):
    if request.user.is_authenticated:
        return redirect('chat')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('chat')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('chat')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


@login_required(login_url='login')
def chat_page(request):
    # Check if current user is admin
    is_admin = request.user.is_staff
    
    if is_admin:
        # Admins see list of all non-admin users
        other_users = User.objects.filter(is_staff=False)
    else:
        # Regular users see list of admins
        other_users = User.objects.filter(is_staff=True)
    
    context = {
        'other_users': other_users,
        'current_user': request.user,
        'is_admin': is_admin,
    }
    
    return render(request, "chat.html", context)


@login_required(login_url='login')
@require_http_methods(["GET"])
def get_messages(request, user_id):
    """API endpoint to get message history between current user and another user"""
    try:
        other_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    # Get all messages between these two users
    messages_list = Message.objects.filter(
        (models.Q(sender=request.user) & models.Q(recipient=other_user)) |
        (models.Q(sender=other_user) & models.Q(recipient=request.user))
    ).order_by('timestamp').values('sender__username', 'sender_id', 'text', 'timestamp')
    
    return JsonResponse({
        'messages': list(messages_list)
    })
