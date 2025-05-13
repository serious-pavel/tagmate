from django.shortcuts import render


def index(request):
    return render(request, template_name='index.html')


def profile(request):
    return render(request, template_name='core/profile.html')
