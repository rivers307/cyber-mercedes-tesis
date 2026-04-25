from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

@login_required
def custom_logout(request):
    logout(request)
    return redirect('login')