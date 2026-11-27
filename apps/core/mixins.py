"""Reusable view mixins.

Each mixin has a single responsibility (authorisation by role, ownership
scoping, partial rendering) so views compose behaviour instead of
re-implementing it.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict a view to users whose ``role`` is in ``allowed_roles``."""

    allowed_roles: tuple = ()

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in self.allowed_roles

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()


class SeekerRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("seeker",)


class EmployerRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("employer",)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()


class PartialTemplateMixin:
    """Render ``partial_template_name`` for fetch() requests.

    Lets list pages refresh their results without a full reload while
    still working without JavaScript (progressive enhancement).
    """

    partial_template_name = None

    def is_partial(self):
        return self.request.headers.get("X-Partial") == "1"

    def get_template_names(self):
        if self.partial_template_name and self.is_partial():
            return [self.partial_template_name]
        return super().get_template_names()


class QueryStringMixin:
    """Expose the current query string without the ``page`` parameter."""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["querystring"] = params.urlencode()
        ctx["selected"] = {key: self.request.GET.getlist(key) for key in self.request.GET}
        return ctx
