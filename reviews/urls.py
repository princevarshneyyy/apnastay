from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('create/<str:booking_id>/', views.review_create_view, name='create'),
    path('<int:review_id>/edit/', views.review_update_view, name='edit'),
    path('<int:review_id>/delete/', views.review_delete_view, name='delete'),
]
