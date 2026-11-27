"""Presentation helpers used across templates (registered as builtins)."""
import hashlib

from django import template
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

from apps.core.icons import render_icon

register = template.Library()

AVATAR_GRADIENTS = [
    ("#2563EB", "#7C3AED"),
    ("#06B6D4", "#2563EB"),
    ("#7C3AED", "#EC4899"),
    ("#10B981", "#06B6D4"),
    ("#F59E0B", "#EF4444"),
    ("#0EA5E9", "#6366F1"),
]


@register.simple_tag
def icon(name, size=20, css_class=""):
    return mark_safe(render_icon(name, int(size), css_class))


def _gradient_for(seed: str):
    digest = int(hashlib.md5(seed.encode("utf-8")).hexdigest(), 16)
    return AVATAR_GRADIENTS[digest % len(AVATAR_GRADIENTS)]


def _initials(name: str) -> str:
    words = ("".join(ch for ch in w if ch.isalnum()) for w in (name or "?").split())
    parts = [w for w in words if w]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


@register.simple_tag
def avatar(name, image=None, size=48, css_class=""):
    """Image avatar, falling back to gradient initials."""
    size = int(size)
    if image:
        try:
            url = image.url
        except ValueError:
            url = None
        if url:
            return format_html(
                '<img class="avatar {}" src="{}" alt="{}" width="{}" height="{}" loading="lazy" decoding="async">',
                css_class, url, name, size, size,
            )
    a, b = _gradient_for(name or "?")
    return format_html(
        '<span class="avatar avatar--initials {}" style="--s:{}px;background:linear-gradient(135deg,{},{})" '
        'role="img" aria-label="{}">{}</span>',
        css_class, size, a, b, name, _initials(name),
    )


@register.simple_tag
def logo(company, size=48, css_class=""):
    if company is None:
        return avatar("?", None, size, css_class)
    return avatar(company.name, company.logo, size, "avatar--square " + css_class)


@register.simple_tag
def stars(rating, max_stars=5):
    try:
        rating = float(rating or 0)
    except (TypeError, ValueError):
        rating = 0
    out = []
    for i in range(1, int(max_stars) + 1):
        cls = "star is-on" if rating >= i - 0.25 else "star"
        out.append(f'<span class="{cls}">{render_icon("star", 16)}</span>')
    return mark_safe(f'<span class="stars" aria-label="{rating:.1f} / {max_stars}">{"".join(out)}</span>')


@register.simple_tag(takes_context=True)
def nav_active(context, *prefixes):
    path = context["request"].path
    return "is-active" if any(path.startswith(p) for p in prefixes) else ""


@register.simple_tag(takes_context=True)
def query_replace(context, **kwargs):
    params = context["request"].GET.copy()
    for key, value in kwargs.items():
        if value in (None, ""):
            params.pop(key, None)
        else:
            params[key] = value
    return params.urlencode()


@register.filter
def money(value, currency="$"):
    if value in (None, ""):
        return ""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    return f"{currency}{value:,}"


@register.filter
def localized(obj, field="name"):
    """Return ``<field>_en`` when the active language is English."""
    if obj is None:
        return ""
    if (get_language() or "ar").startswith("en"):
        en = getattr(obj, f"{field}_en", "")
        if en:
            return en
    return getattr(obj, field, "")


@register.filter
def split_lines(value):
    return [line.strip(" -•\t") for line in (value or "").splitlines() if line.strip()]


@register.filter
def get_item(mapping, key):
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.filter
def percent_of(value, total):
    try:
        return round(int(value) * 100 / int(total)) if int(total) else 0
    except (TypeError, ValueError, ZeroDivisionError):
        return 0


@register.simple_tag
def status_badge(status, label):
    return format_html('<span class="badge badge--{}">{}</span>', escape(status), label)
