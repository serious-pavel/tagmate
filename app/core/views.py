from django.shortcuts import render


def profile(request):
    return render(request, template_name='core/profile.html')
