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

from django.test import TestCase

from gitstorage import factories
from gitstorage import forms


class UsersChoiceFieldTestCase(TestCase):

    def test_superuser(self):
        factories.SuperUserFactory()
        field = forms.UsersChoiceField()
        self.assertQuerysetEqual(field.queryset, [])

    def test_user(self):
        factories.UserFactory(username="john_doe")
        field = forms.UsersChoiceField()
        self.assertQuerysetEqual(field.queryset, ["john_doe"], transform=lambda obj: obj.username)

    def test_label_from_instance(self):
        user = factories.UserFactory(first_name="John", last_name="Doe", email="john.doe@example.com")
        field = forms.UsersChoiceField()
        choice = field.choices.choice(user)
        self.assertEqual(choice, (user.pk, "John Doe <john.doe@example.com>"))


class RemoveUsersFormTestCase(TestCase):

    def test_current_users(self):
        user1 = factories.UserFactory()
        user2 = factories.UserFactory()
        current_user_ids = [user1.pk]
        form = forms.RemoveUsersForm(current_user_ids)
        self.assertIn(user1, form.fields['users'].queryset)
        self.assertNotIn(user2, form.fields['users'].queryset)


class AddUsersFormTestCase(TestCase):

    def test_current_users(self):
        user1 = factories.UserFactory()
        user2 = factories.UserFactory()
        current_user_ids = [user1.pk]
        form = forms.AddUsersForm(current_user_ids)
        self.assertNotIn(user1, form.fields['users'].queryset)
        self.assertIn(user2, form.fields['users'].queryset)
