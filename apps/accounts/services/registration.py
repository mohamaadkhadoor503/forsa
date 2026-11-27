"""User registration use-case.

Creating a user also creates the role-specific profile. Each role has its
own ``ProfileProvisioner`` so adding a new role never requires changing the
service itself (Open/Closed principle).
"""
from typing import Protocol

from django.db import transaction
from django.utils.text import slugify

from apps.accounts.models import User


class ProfileProvisioner(Protocol):
    def provision(self, user: User, data: dict) -> None: ...


class SeekerProvisioner:
    def provision(self, user, data):
        from apps.talents.models import SeekerProfile

        SeekerProfile.objects.get_or_create(user=user, defaults={"headline": data.get("headline", "")})


class EmployerProvisioner:
    def provision(self, user, data):
        from apps.companies.models import Company

        name = data.get("company_name") or user.display_name
        Company.objects.get_or_create(owner=user, defaults={"name": name, "slug": Company.unique_slug(name)})


PROVISIONERS: dict[str, ProfileProvisioner] = {
    User.Role.SEEKER: SeekerProvisioner(),
    User.Role.EMPLOYER: EmployerProvisioner(),
}


class RegistrationService:
    def __init__(self, provisioners: dict | None = None):
        self.provisioners = provisioners or PROVISIONERS

    @transaction.atomic
    def register(self, *, email, password, first_name, last_name, role, **extra) -> User:
        base = slugify(email.split("@")[0], allow_unicode=True) or "user"
        username = base
        i = 1
        while User.objects.filter(username=username).exists():
            i += 1
            username = f"{base}{i}"
        user = User.objects.create_user(
            email=email, password=password, first_name=first_name,
            last_name=last_name, role=role, username=username,
        )
        provisioner = self.provisioners.get(role)
        if provisioner:
            provisioner.provision(user, extra)
        from apps.core.services.stats import invalidate_stats
        invalidate_stats()
        return user
