from django.urls import path
from . import views

app_name = 'wishlists'

urlpatterns = [
    path('', views.wishlist_list_view, name='list'),
    path('toggle/<int:listing_id>/', views.wishlist_toggle_view, name='toggle'),
]
