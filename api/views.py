from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.models import User
from listings.models import Listing, ListingImage, Amenity
from bookings.models import Booking
from reviews.models import Review
from wishlists.models import Wishlist

from .serializers import (
    UserSerializer, UserRegisterSerializer,
    ListingListSerializer, ListingDetailSerializer, ListingCreateUpdateSerializer,
    BookingSerializer, BookingCreateSerializer,
    ReviewSerializer, WishlistSerializer
)
from .permissions import IsOwnerOrReadOnly, IsBookingParticipant, IsReviewAuthorOrReadOnly


# ==========================================
# AUTHENTICATION APIs
# ==========================================

class RegisterAPIView(APIView):
    """Register a new user account (Guest or Host)."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user, context={'request': request}).data,
                'message': 'Account created successfully.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """Authenticate with username/email and password, returning an auth token."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username_or_email = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')

        if not username_or_email or not password:
            return Response({'error': 'Please provide both username/email and password.'}, status=status.HTTP_400_BAD_REQUEST)

        user = None
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(username=username_or_email, password=password)

        if not user:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)
        login(request, user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user, context={'request': request}).data,
            'message': 'Login successful.'
        })


class LogoutAPIView(APIView):
    """Logs out the user and deletes their token."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        logout(request)
        return Response({'message': 'Logged out successfully.'})


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    """Retrieve or update current user profile."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ==========================================
# LISTING APIs
# ==========================================

class ListingListCreateAPIView(generics.ListCreateAPIView):
    """
    List active properties with searching, filtering, and ordering.
    Create a new listing (Hosts only / authenticated users).
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'city', 'state']
    ordering_fields = ['price_per_night', 'created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ListingCreateUpdateSerializer
        return ListingListSerializer

    def get_queryset(self):
        queryset = Listing.objects.filter(is_active=True).select_related('host').prefetch_related('images', 'amenities')

        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(property_type__iexact=category)

        min_price = self.request.query_params.get('min_price')
        if min_price and min_price.isdigit():
            queryset = queryset.filter(price_per_night__gte=min_price)

        max_price = self.request.query_params.get('max_price')
        if max_price and max_price.isdigit():
            queryset = queryset.filter(price_per_night__lte=max_price)

        guests = self.request.query_params.get('guests')
        if guests and guests.isdigit():
            queryset = queryset.filter(max_guests__gte=guests)

        return queryset.distinct()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_host:
            user.is_host = True
            user.save(update_fields=['is_host'])
        serializer.save(host=user)


class ListingDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a listing (Update/Delete restricted to listing host)."""
    queryset = Listing.objects.all().select_related('host').prefetch_related('images', 'amenities', 'reviews')
    permission_classes = [IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ListingCreateUpdateSerializer
        return ListingDetailSerializer


# ==========================================
# BOOKING APIs
# ==========================================

class BookingListCreateAPIView(generics.ListCreateAPIView):
    """
    List user bookings (Guest sees their reservations; Host sees reservations for their listings).
    Create a new booking with date validation and concurrency protection.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BookingCreateSerializer
        return BookingSerializer

    def get_queryset(self):
        user = self.request.user
        # Include both guest bookings and bookings on host's properties
        return Booking.objects.filter(
            models_Q(guest=user) | models_Q(listing__host=user)
        ).select_related('listing', 'guest').distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        listing = serializer.validated_data['listing']
        check_in = serializer.validated_data['check_in']
        check_out = serializer.validated_data['check_out']
        guests_count = serializer.validated_data['guests_count']
        special_requests = serializer.validated_data.get('special_requests', '')

        delta = check_out - check_in
        nights = max(1, delta.days)
        pricing = listing.calculate_price_breakdown(nights)

        with transaction.atomic():
            locked_listing = Listing.objects.select_for_update().get(id=listing.id)
            conflicts = Booking.objects.select_for_update().filter(
                listing=locked_listing,
                status__in=['confirmed', 'pending'],
                check_in__lt=check_out,
                check_out__gt=check_in,
            )
            if conflicts.exists():
                return Response(
                    {'error': 'Selected dates have just been booked by another guest.'},
                    status=status.HTTP_409_CONFLICT
                )

            booking = Booking.objects.create(
                listing=locked_listing,
                guest=request.user,
                check_in=check_in,
                check_out=check_out,
                guests_count=guests_count,
                price_per_night=listing.price_per_night,
                total_nights=nights,
                subtotal=pricing['subtotal'],
                service_fee=pricing['service_fee'],
                cleaning_fee=pricing['cleaning_fee'],
                total_amount=pricing['total_amount'],
                status='confirmed',
                payment_status='pay_at_property',
                special_requests=special_requests,
            )

        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class BookingDetailAPIView(generics.RetrieveAPIView):
    """Retrieve booking details (Participant only)."""
    queryset = Booking.objects.all().select_related('listing', 'guest')
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsBookingParticipant]


class BookingCancelAPIView(APIView):
    """Cancel an active booking and release reserved dates."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        if booking.guest != request.user and booking.listing.host != request.user and not request.user.is_staff:
            return Response({'error': 'Unauthorized to cancel this reservation.'}, status=status.HTTP_403_FORBIDDEN)

        if not booking.can_cancel:
            return Response({'error': 'This booking cannot be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        booking.status = 'cancelled'
        booking.cancellation_reason = request.data.get('reason', 'Cancelled via API')
        booking.cancelled_at = timezone.now()
        booking.save(update_fields=['status', 'cancellation_reason', 'cancelled_at'])

        return Response({'message': f'Booking {booking.booking_id} has been cancelled successfully.'})


# ==========================================
# REVIEW APIs
# ==========================================

class ListingReviewListCreateAPIView(APIView):
    """
    GET: List all reviews for a listing.
    POST: Submit a review for a completed stay.
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get(self, request, listing_id):
        listing = get_object_or_404(Listing, id=listing_id)
        reviews = listing.reviews.select_related('user').order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    def post(self, request, listing_id):
        listing = get_object_or_404(Listing, id=listing_id)

        if listing.host == request.user:
            return Response({'error': 'Hosts cannot review their own property.'}, status=status.HTTP_403_FORBIDDEN)

        booking_id = request.data.get('booking_id')
        if not booking_id:
            # Try to find user's eligible completed booking
            eligible_booking = Booking.objects.filter(
                listing=listing,
                guest=request.user,
                review__isnull=True
            ).filter(
                status__in=['completed', 'confirmed']
            ).first()
            if not eligible_booking or not eligible_booking.can_review:
                return Response(
                    {'error': 'A completed booking is required to submit a review.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            booking = eligible_booking
        else:
            booking = get_object_or_404(Booking, id=booking_id, listing=listing, guest=request.user)
            if not booking.can_review:
                return Response({'error': 'This booking is not eligible for a review.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            review = serializer.save(listing=listing, booking=booking, user=request.user)
            return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewDetailAPIView(generics.UpdateAPIView, generics.DestroyAPIView):
    """Edit or delete a review (Author only)."""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsReviewAuthorOrReadOnly]


# ==========================================
# WISHLIST APIs
# ==========================================

class WishlistListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List wishlisted items for current user.
    POST: Add a listing to current user's wishlist.
    """
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('listing')

    def create(self, request, *args, **kwargs):
        listing_id = request.data.get('listing_id') or request.data.get('listing')
        if not listing_id:
            return Response({'error': 'listing_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        listing = get_object_or_404(Listing, id=listing_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, listing=listing)

        return Response(
            WishlistSerializer(wishlist_item, context={'request': request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class WishlistDeleteAPIView(APIView):
    """Remove a listing from current user's wishlist."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        wishlist_item = get_object_or_404(Wishlist, id=pk, user=request.user)
        wishlist_item.delete()
        return Response({'message': 'Removed from wishlist.'}, status=status.HTTP_204_NO_CONTENT)


# Helper for Q query in views
from django.db.models import Q as models_Q
