from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path("project/<int:pk>/", views.SubmitReviewView.as_view(), name="review_project"),
    path("testimonial/", views.SubmitTestimonialView.as_view(), name="testimonial"),
    path("report/<str:target_type>/<int:target_id>/", views.SubmitReportView.as_view(), name="report"),
]
