from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a listing to edit or delete it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.host == request.user or request.user.is_staff


class IsBookingParticipant(permissions.BasePermission):
    """
    Custom permission allowing only the guest or the property host to view/cancel the booking.
    """
    def has_object_permission(self, request, view, obj):
        return obj.guest == request.user or obj.listing.host == request.user or request.user.is_staff


class IsReviewAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission allowing only the author of a review to update or delete it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user or request.user.is_staff
