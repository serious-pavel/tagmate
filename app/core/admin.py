from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from . import models

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount


class SocialAccountInline(admin.TabularInline):
    model = SocialAccount
    extra = 0

class EmailAddressInline(admin.TabularInline):
    model = EmailAddress
    extra = 0

class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users"""
    ordering = ['id']
    list_display = ['email', 'full_name', 'id']
    fieldsets = (
        (None, {'fields': ('email', 'full_name', 'profile_picture', 'password')}),
        (
            _('Permissions'),
            {'fields': ('is_active', 'is_staff', 'is_superuser')}
        ),
        (
            _('Important dates'),
            {'fields': ('last_login', )}
        ),
    )
    readonly_fields = ['last_login']
    inlines = [EmailAddressInline, SocialAccountInline]
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'full_name',
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),
    )


admin.site.register(models.User, UserAdmin)
