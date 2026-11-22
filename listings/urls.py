from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    path('', views.listing_list_view, name='list'),
    path('create/', views.listing_create_view, name='create'),
    path('<slug:slug>/', views.listing_detail_view, name='detail'),
    path('<slug:slug>/edit/', views.listing_update_view, name='edit'),
    path('<slug:slug>/delete/', views.listing_delete_view, name='delete'),
    path('<slug:slug>/toggle-status/', views.listing_toggle_status_view, name='toggle_status'),
    path('<int:listing_id>/images/<int:image_id>/cover/', views.set_cover_image_view, name='set_cover_image'),
    path('<int:listing_id>/images/<int:image_id>/delete/', views.delete_image_view, name='delete_image'),
]
