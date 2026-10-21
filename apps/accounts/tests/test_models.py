import pytest

from apps.accounts.models import Profile


@pytest.mark.django_db
def test_profile_auto_created_on_user_creation(django_user_model):
    user = django_user_model.objects.create_user("alice", password="StrongPass123!")
    assert Profile.objects.filter(user=user).exists()
    assert user.profile.role == Profile.Role.STANDARD


@pytest.mark.django_db
def test_is_admin_true_for_admin_role(django_user_model):
    user = django_user_model.objects.create_user("bob", password="StrongPass123!")
    user.profile.role = Profile.Role.ADMIN
    user.profile.save()
    assert user.profile.is_admin is True


@pytest.mark.django_db
def test_is_admin_false_for_standard_role(django_user_model):
    user = django_user_model.objects.create_user("carol", password="StrongPass123!")
    assert user.profile.is_admin is False
