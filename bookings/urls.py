from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('create/<slug:slug>/', views.booking_create_view, name='create'),
    path('<str:booking_id>/confirmation/', views.booking_confirmation_view, name='confirmation'),
    path('<str:booking_id>/', views.booking_detail_view, name='detail'),
    path('<str:booking_id>/cancel/', views.booking_cancel_view, name='cancel'),
    path('api/calculate/<slug:slug>/', views.calculate_price_api, name='api_calculate'),
]
