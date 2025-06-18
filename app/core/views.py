from django.shortcuts import render
from allauth.socialaccount.models import SocialAccount


def profile(request):
    user = request.user
    context = {}
    if user.is_authenticated:
        social_acc = SocialAccount.objects.filter(
            provider='google',
            user_id=user.id,
        ).first()
        if social_acc:
            context.update({'social_acc': social_acc})

    return render(request, template_name='core/profile.html', context=context)
