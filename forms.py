"""
This file is part of Profile module for Django. This module is
intended to provide a template for profile management.

Copyright (C) 2010  Brice Leroy

Profile is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Profile is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Profile.  If not, see <http://www.gnu.org/licenses/>.
"""

from django import forms
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import forms as authforms
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.utils.http import int_to_base36
from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

from common.shortcuts import render_string
from profile.models import Profile, Registration

# favour django-mailer but fall back to django.core.mail
if "mailer" in settings.INSTALLED_APPS:
    from mailer import send_mail
else:
    from django.core.mail import send_mail

from profile.settings import DEFAULT_EMAIL_FROM

class RegisterForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ('email',)

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')
                  
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('user',)

class LoginForm(forms.Form):
    """
    Review of the base class for authenticating users but using email instead of username.
    """
    email = forms.EmailField(max_length=128, label='Email')
    password = forms.CharField(max_length=50, widget=forms.PasswordInput, label='Password' )

    def __init__(self, request=None, *args, **kwargs):
        """
        If request is passed in, the form will validate that cookies are
        enabled. Note that the request (a HttpRequest object) must have set a
        cookie with the key TEST_COOKIE_NAME and value TEST_COOKIE_VALUE before
        running this validation.
        """
        self.request = request
        self.user_cache = None
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        try:
            username = User.objects.get(email__iexact=email).username
        except:
            username = None
            raise forms.ValidationError(_("Please enter a correct email and password. Note that password is case-sensitive."))
        if username and password:
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(_("Please enter a correct email and password. Note that password is case-sensitive."))
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_("This account is inactive."))

        if self.request:
            if not self.request.session.test_cookie_worked():
                raise forms.ValidationError(_("Your Web browser doesn't appear to have cookies enabled. Cookies are required for logging in."))

        return self.cleaned_data

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache

class SetPasswordForm(forms.Form):
    """
    A form that lets a user change set his/her password for user creation
    """
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(_("The two password fields didn't match."))
        return password2
        
class PasswordResetForm(authforms.PasswordResetForm):
    def save(self, domain_override=None, email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator):
        """
        Generates a one-use only link for resetting password and sends 
        it in an email. 
        """
        for user in self.users_cache:
            if not domain_override:
                current_site = Site.objects.get_current()
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            c = {
                'DEFAULT_EMAIL_FROM': DEFAULT_EMAIL_FROM,
                'SITE_URL': domain,
                'email': user.email,
                'email_to': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
            }
            t = loader.get_template(email_template_name)
            text_content = t.render(Context(c))
            
            send_mail(_("Password reset on %s") % site_name, text_content, settings.DEFAULT_EMAIL_FROM, [user.email])
