from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from accounts.models import User
from listings.models import Listing, ListingImage, Amenity
from bookings.models import Booking
from reviews.models import Review
from wishlists.models import Wishlist


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'phone_number', 'bio', 'is_host', 'profile_picture', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'confirm_password', 'is_host']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'icon', 'description']


class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ['id', 'image', 'is_cover', 'caption']


class HostSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email', 'profile_picture']


class ListingListSerializer(serializers.ModelSerializer):
    host = HostSummarySerializer(read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()

    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'slug', 'property_type', 'city', 'state', 'country',
            'price_per_night', 'max_guests', 'bedrooms', 'bathrooms',
            'cover_image_url', 'average_rating', 'review_count', 'host', 'is_active', 'is_featured'
        ]

    def get_cover_image_url(self, obj):
        cover = obj.cover_image
        if cover and cover.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(cover.image.url)
            return cover.image.url
        return None


class ListingDetailSerializer(serializers.ModelSerializer):
    host = HostSummarySerializer(read_only=True)
    images = ListingImageSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()

    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'slug', 'description', 'property_type', 'address', 'city', 'state', 'country',
            'price_per_night', 'cleaning_fee', 'service_fee_percent', 'max_guests', 'bedrooms', 'beds', 'bathrooms',
            'is_active', 'is_featured', 'average_rating', 'review_count', 'host', 'amenities', 'images', 'created_at', 'updated_at'
        ]


class ListingCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'property_type', 'address', 'city', 'state', 'country',
            'price_per_night', 'cleaning_fee', 'max_guests', 'bedrooms', 'beds', 'bathrooms',
            'amenities', 'is_active', 'is_featured'
        ]
        read_only_fields = ['id']


class BookingSerializer(serializers.ModelSerializer):
    listing_title = serializers.ReadOnlyField(source='listing.title')
    listing_city = serializers.ReadOnlyField(source='listing.city')
    guest_name = serializers.ReadOnlyField(source='guest.full_name')

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_id', 'listing', 'listing_title', 'listing_city',
            'guest', 'guest_name', 'check_in', 'check_out', 'guests_count',
            'price_per_night', 'total_nights', 'subtotal', 'service_fee', 'cleaning_fee',
            'total_amount', 'status', 'payment_status', 'special_requests', 'can_cancel',
            'can_review', 'created_at'
        ]
        read_only_fields = [
            'id', 'booking_id', 'price_per_night', 'total_nights', 'subtotal',
            'service_fee', 'cleaning_fee', 'total_amount', 'status', 'created_at'
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['listing', 'check_in', 'check_out', 'guests_count', 'special_requests']

    def validate(self, attrs):
        listing = attrs['listing']
        check_in = attrs['check_in']
        check_out = attrs['check_out']
        guests_count = attrs['guests_count']
        today = timezone.now().date()
        request = self.context.get('request')

        if check_out <= check_in:
            raise serializers.ValidationError({"check_out": "Check-out must be after check-in."})

        if check_in < today:
            raise serializers.ValidationError({"check_in": "Check-in date cannot be in the past."})

        if request and request.user == listing.host:
            raise serializers.ValidationError("Host cannot book their own property.")

        if guests_count > listing.max_guests:
            raise serializers.ValidationError({
                "guests_count": f"Maximum capacity for this property is {listing.max_guests} guests."
            })

        overlapping = Booking.objects.filter(
            listing=listing,
            status__in=['confirmed', 'pending'],
            check_in__lt=check_out,
            check_out__gt=check_in,
        )
        if overlapping.exists():
            raise serializers.ValidationError("These dates are already reserved for this property.")

        return attrs


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')

    class Meta:
        model = Review
        fields = ['id', 'listing', 'booking', 'user', 'user_name', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'listing', 'created_at', 'updated_at']


class WishlistSerializer(serializers.ModelSerializer):
    listing_details = ListingListSerializer(source='listing', read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'listing', 'listing_details', 'created_at']
        read_only_fields = ['id', 'created_at']
