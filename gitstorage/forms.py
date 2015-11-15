# Copyright Bors LTD
# This file is part of django-gitstorage.
#
#    Django-gitstorage is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Django-gitstorage is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with django-gitstorage.  If not, see <http://www.gnu.org/licenses/>.

from django import forms
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _


class UsersChoiceField(forms.ModelMultipleChoiceField):

    def __init__(self, **kwargs):
        # Since superusers always are allowed, filter them out by default
        queryset = auth_models.User.objects.filter(is_superuser=False)
        super().__init__(queryset, **kwargs)

    def label_from_instance(self, user):
        return "{0.first_name} {0.last_name} <{0.email}>".format(user)


class RemoveUsersForm(forms.Form):
    users = UsersChoiceField(label=_("Users"), widget=forms.CheckboxSelectMultiple)

    def __init__(self, current_user_ids, **kwargs):
        super().__init__(**kwargs)
        self.fields['users'].queryset = self.fields['users'].queryset.filter(pk__in=current_user_ids)


class AddUsersForm(forms.Form):
    users = UsersChoiceField(label=_("Users"), widget=forms.CheckboxSelectMultiple)

    def __init__(self, current_user_ids, **kwargs):
        super().__init__(**kwargs)
        self.fields['users'].queryset = self.fields['users'].queryset.exclude(pk__in=current_user_ids)


class UploadForm(forms.Form):
    file = forms.FileField(label=_("File"))
