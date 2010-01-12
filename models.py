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
from django.utils.translation import ugettext as _

from django.db import models

from common.geos import COUNTRY_CHOICES, STATE_CHOICES
from common.tools import get_uuid

SEX_CHOICES = (
    ('male', _('Male')),
    ('female', _('Female')),
)

class Profile(models.Model):
    """
    A profile store data linked to a user. It allows you
    to extend the data model and functionality.
    """
    # User link (one to one relation)
    user = models.ForeignKey(User, related_name='profile', unique=True)

    sex = models.CharField(_('Gender'), max_length=6, choices=SEX_CHOICES, blank=True)
    birth_date = models.DateField(blank=True, null=True, help_text=_("format: yyyy-mm-dd"))

    # This link activate the friend relation
    friends = models.ManyToManyField('self', blank=True, symmetrical=True)

    # Contact Informations
    phone = models.CharField(max_length=20, blank=True)

    # Geographical Address
    address1 = models.CharField(max_length=255, blank=True)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=3, choices=STATE_CHOICES, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=4, choices=COUNTRY_CHOICES, blank=True)
    
    # The profile agreed with conditions
    agree_with_terms_and_conditions = models.BooleanField(default=False)
    
    @models.permalink
    def getFabsolute_url(self):
        return ('profile.views.profile_detail', [self.pk])


class Registration(models.Model):
    email = models.EmailField()
    key = models.CharField(max_length=55, unique=True, db_index=True, default=get_uuid)
    creation_date = models.DateTimeField(auto_now_add=True)

    @models.permalink
    def get_absolute_url(self):
        return ('profile.views.register_confirm', [str(self.key)])
