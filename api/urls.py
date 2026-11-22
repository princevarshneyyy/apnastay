from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Auth APIs
    path('auth/register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('auth/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('auth/logout/', views.LogoutAPIView.as_view(), name='api_logout'),
    path('auth/profile/', views.ProfileAPIView.as_view(), name='api_profile'),

    # Listing APIs
    path('listings/', views.ListingListCreateAPIView.as_view(), name='api_listing_list_create'),
    path('listings/<int:pk>/', views.ListingDetailAPIView.as_view(), name='api_listing_detail'),

    # Booking APIs
    path('bookings/', views.BookingListCreateAPIView.as_view(), name='api_booking_list_create'),
    path('bookings/<int:pk>/', views.BookingDetailAPIView.as_view(), name='api_booking_detail'),
    path('bookings/<int:pk>/cancel/', views.BookingCancelAPIView.as_view(), name='api_booking_cancel'),

    # Review APIs
    path('listings/<int:listing_id>/reviews/', views.ListingReviewListCreateAPIView.as_view(), name='api_listing_reviews'),
    path('reviews/<int:pk>/', views.ReviewDetailAPIView.as_view(), name='api_review_detail'),

    # Wishlist APIs
    path('wishlist/', views.WishlistListCreateAPIView.as_view(), name='api_wishlist_list_create'),
    path('wishlist/<int:pk>/', views.WishlistDeleteAPIView.as_view(), name='api_wishlist_delete'),
]
