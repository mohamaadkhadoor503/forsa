from django.shortcuts import render


def permission_denied(request, exception=None):
    return render(request, "errors/403.html", status=403)


def page_not_found(request, exception=None):
    return render(request, "errors/404.html", status=404)


def server_error(request):
    # Keep the 500 page free of DB-dependent context.
    return render(request, "errors/500.html", status=500)
