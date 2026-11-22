import os
from pathlib import Path
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
import io

from listings.models import Listing, ListingImage, Amenity
from bookings.models import Booking
from reviews.models import Review
from wishlists.models import Wishlist

User = get_user_model()


def create_styled_image(title, subtitle, color1, color2, width=800, height=533):
    """Generates an aesthetic travel property image with a gradient and badge."""
    image = Image.new("RGB", (width, height), color1)
    draw = ImageDraw.Draw(image)

    # Simple vertical gradient effect
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    for y in range(height):
        factor = y / height
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Darker bottom overlay for readability
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([0, height - 160, width, height], fill=(0, 0, 0, 150))
    image.paste(overlay, (0, 0), overlay)

    # Draw border card
    draw.rectangle([20, 20, width - 20, height - 20], outline=(255, 255, 255, 100), width=2)

    # Draw labels
    draw.text((40, height - 130), title, fill=(255, 255, 255))
    draw.text((40, height - 80), subtitle, fill=(255, 200, 100))
    draw.text((40, 40), "APNASTAY VERIFIED", fill=(255, 255, 255))

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=90)
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = "Populate ApnaStay database with realistic Indian destinations, properties, amenities, demo users, bookings, and reviews."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing ApnaStay Demo Dataset..."))

        # 1. Create Demo Users
        self.stdout.write("Creating demo users...")

        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@apnastay.in",
                "first_name": "System",
                "last_name": "Administrator",
                "is_staff": True,
                "is_superuser": True,
                "is_host": True,
            }
        )
        admin_user.set_password("admin123")
        admin_user.save()

        host1, _ = User.objects.get_or_create(
            username="host1",
            defaults={
                "email": "rajesh.sharma@apnastay.in",
                "first_name": "Rajesh",
                "last_name": "Sharma",
                "phone_number": "+91 9876543210",
                "bio": "Superhost passionate about coastal villas and warm Indian hospitality.",
                "is_host": True,
            }
        )
        host1.set_password("host123")
        host1.save()

        host2, _ = User.objects.get_or_create(
            username="host2",
            defaults={
                "email": "ananya.patel@apnastay.in",
                "first_name": "Ananya",
                "last_name": "Patel",
                "phone_number": "+91 9811223344",
                "bio": "Heritage architect hosting restored mountain chalets and havelis.",
                "is_host": True,
            }
        )
        host2.set_password("host234")
        host2.save()

        guest1, _ = User.objects.get_or_create(
            username="guest1",
            defaults={
                "email": "priya.verma@example.com",
                "first_name": "Priya",
                "last_name": "Verma",
                "phone_number": "+91 9988776655",
                "bio": "Solo wanderer and photographer exploring culture and quiet stays.",
                "is_host": False,
            }
        )
        guest1.set_password("guest123")
        guest1.save()

        self.stdout.write(self.style.SUCCESS(" Users created: admin (admin123), host1 (host123), host2 (host234), guest1 (guest123)"))

        # 2. Create Standard Amenities
        amenities_data = [
            ("High-speed Wi-Fi", "bi-wifi", "Fast optical fiber Internet for remote work"),
            ("Private Swimming Pool", "bi-water", "Clean, private fresh-water swimming pool"),
            ("Air Conditioning", "bi-snow", "Climate-controlled split air conditioning"),
            ("Fully Equipped Kitchen", "bi-fire", "Refrigerator, microwave, gas stove, and cookware"),
            ("Free Parking on Premises", "bi-car-front", "Secure on-site private vehicle parking"),
            ("Scenic Mountain View", "bi-triangle", "Panoramic vistas of mountain peaks and valley"),
            ("Beachfront / Sea View", "bi-tsunami", "Steps away from the beach with sea breeze"),
            ("Smart LED TV", "bi-tv", "55-inch Ultra HD TV with Netflix and Prime Video"),
            ("Pet Friendly", "bi-heart", "Pets are welcomed with open arms"),
            ("Dedicated Workspace", "bi-laptop", "Ergonomic desk and chair with charging ports"),
            ("Hot Water Geyser", "bi-thermometer-sun", "24/7 continuous hot water in bathrooms"),
            ("Daily Housekeeping", "bi-stars", "Complimentary daily cleaning and fresh linen"),
        ]

        amenities_dict = {}
        for name, icon, desc in amenities_data:
            amenity, _ = Amenity.objects.get_or_create(
                name=name,
                defaults={"icon": icon, "description": desc}
            )
            amenities_dict[name] = amenity

        self.stdout.write(self.style.SUCCESS(f" {len(amenities_dict)} amenities ready."))

        # 3. Create Sample Properties
        listings_data = [
            {
                "host": host1,
                "title": "Villa Oceana - Luxury Sea-Facing Villa with Private Pool",
                "property_type": "villa",
                "address": "House 45, Near Calangute Beach Road",
                "city": "North Goa",
                "state": "Goa",
                "price_per_night": Decimal("14500.00"),
                "cleaning_fee": Decimal("1200.00"),
                "max_guests": 8,
                "bedrooms": 4,
                "beds": 4,
                "bathrooms": 4,
                "is_featured": True,
                "description": "Escape to Villa Oceana, a luxury Mediterranean-inspired sanctuary situated a 5-minute stroll from Calangute beach. Features an azure private pool, sun deck, lush tropical lawn, high-ceiling living spaces, and an in-house chef available upon request.",
                "amenities": ["High-speed Wi-Fi", "Private Swimming Pool", "Air Conditioning", "Fully Equipped Kitchen", "Free Parking on Premises", "Beachfront / Sea View", "Smart LED TV", "Hot Water Geyser"],
                "color1": (24, 76, 120),
                "color2": (224, 86, 91),
            },
            {
                "host": host2,
                "title": "The Himalayan Cedar Chalet & Apple Orchard Retreat",
                "property_type": "cottage",
                "address": "Naggar Old Road, Shuru",
                "city": "Manali",
                "state": "Himachal Pradesh",
                "price_per_night": Decimal("6800.00"),
                "cleaning_fee": Decimal("600.00"),
                "max_guests": 5,
                "bedrooms": 2,
                "beds": 3,
                "bathrooms": 2,
                "is_featured": True,
                "description": "Nestled inside an organic apple orchard with unobstructed views of the snow-capped Rohtang peaks, this cedar-wood cottage features a wood-burning fireplace, large balcony, and star-gazing attic room. Ideal for mountain lovers and digital nomads.",
                "amenities": ["High-speed Wi-Fi", "Scenic Mountain View", "Dedicated Workspace", "Free Parking on Premises", "Hot Water Geyser", "Smart LED TV", "Pet Friendly"],
                "color1": (35, 60, 50),
                "color2": (180, 140, 90),
            },
            {
                "host": host1,
                "title": "Royal Haveli Courtyard Suite near Hawa Mahal",
                "property_type": "homestay",
                "address": "Badi Chaupar, Old Heritage Quarter",
                "city": "Jaipur",
                "state": "Rajasthan",
                "price_per_night": Decimal("4200.00"),
                "cleaning_fee": Decimal("400.00"),
                "max_guests": 3,
                "bedrooms": 1,
                "beds": 2,
                "bathrooms": 1,
                "is_featured": True,
                "description": "Experience genuine Rajputana heritage in this 120-year-old restored haveli. Hand-painted fresco ceilings, traditional jharokha bay windows, and tranquil central marble courtyard. Steps away from the bustling bazaars and Hawa Mahal.",
                "amenities": ["High-speed Wi-Fi", "Air Conditioning", "Smart LED TV", "Daily Housekeeping", "Hot Water Geyser"],
                "color1": (160, 60, 45),
                "color2": (230, 180, 80),
            },
            {
                "host": host2,
                "title": "Lake Pichola Sunset Luxury Villa",
                "property_type": "villa",
                "address": "Haridas Ji Ki Magri, Lake Edge",
                "city": "Udaipur",
                "state": "Rajasthan",
                "price_per_night": Decimal("18500.00"),
                "cleaning_fee": Decimal("1500.00"),
                "max_guests": 6,
                "bedrooms": 3,
                "beds": 3,
                "bathrooms": 3,
                "is_featured": True,
                "description": "Perched on the rim of Lake Pichola, this private villa offers an infinity plunge pool gazing onto the City Palace. Expansive rooftop terrace for candlelight dinners and bespoke boat rides arranged by host.",
                "amenities": ["High-speed Wi-Fi", "Private Swimming Pool", "Air Conditioning", "Fully Equipped Kitchen", "Free Parking on Premises", "Daily Housekeeping", "Smart LED TV"],
                "color1": (30, 70, 110),
                "color2": (210, 130, 40),
            },
            {
                "host": host1,
                "title": "Emerald Palms Backwater Homestay & Kayak Haven",
                "property_type": "homestay",
                "address": "Punnamada Lake Bank, Kainakary",
                "city": "Kerala",
                "state": "Kerala",
                "price_per_night": Decimal("3800.00"),
                "cleaning_fee": Decimal("300.00"),
                "max_guests": 4,
                "bedrooms": 2,
                "beds": 2,
                "bathrooms": 2,
                "is_featured": False,
                "description": "Awake to kingfishers chirping and country boats gliding by. Traditional Kerala timber house amidst coconut groves. Includes complimentary village canoe rides, fresh banana-leaf breakfast, and peaceful canal views.",
                "amenities": ["High-speed Wi-Fi", "Free Parking on Premises", "Pet Friendly", "Daily Housekeeping", "Dedicated Workspace"],
                "color1": (20, 90, 60),
                "color2": (100, 160, 90),
            },
            {
                "host": host2,
                "title": "Ganga Riverfront Yoga Retreat & Penthouse",
                "property_type": "apartment",
                "address": "Tapovan Upper Road, Near Laxman Jhula",
                "city": "Rishikesh",
                "state": "Uttarakhand",
                "price_per_night": Decimal("5200.00"),
                "cleaning_fee": Decimal("500.00"),
                "max_guests": 4,
                "bedrooms": 2,
                "beds": 2,
                "bathrooms": 2,
                "is_featured": True,
                "description": "A tranquil sanctuary overlooking the holy Ganges and green foothills. Rooftop yoga deck with mats provided, soundproof meditation corner, and organic herbal tea bar. Close to famous river ghats and hiking trails.",
                "amenities": ["High-speed Wi-Fi", "Air Conditioning", "Scenic Mountain View", "Dedicated Workspace", "Hot Water Geyser"],
                "color1": (40, 100, 120),
                "color2": (220, 160, 60),
            },
            {
                "host": host1,
                "title": "Infinity Mist Hilltop Farmhouse & Mango Orchard",
                "property_type": "farmhouse",
                "address": "Tungarli Hills, Old Highway Sector",
                "city": "Lonavala",
                "state": "Maharashtra",
                "price_per_night": Decimal("11000.00"),
                "cleaning_fee": Decimal("800.00"),
                "max_guests": 10,
                "bedrooms": 4,
                "beds": 5,
                "bathrooms": 4,
                "is_featured": False,
                "description": "Spectacular 2-acre estate with private lawn, barbecue area, and stunning sunset views over the valley. Perfect weekend gathering spot for families and friend reunions escaping Mumbai and Pune.",
                "amenities": ["High-speed Wi-Fi", "Private Swimming Pool", "Fully Equipped Kitchen", "Free Parking on Premises", "Pet Friendly", "Smart LED TV"],
                "color1": (70, 90, 40),
                "color2": (190, 110, 50),
            },
            {
                "host": host2,
                "title": "Pinecone Studio Cabin with Heated Jacuzzi",
                "property_type": "cabin",
                "address": "Upper Kanyal Road",
                "city": "Manali",
                "state": "Himachal Pradesh",
                "price_per_night": Decimal("7500.00"),
                "cleaning_fee": Decimal("500.00"),
                "max_guests": 2,
                "bedrooms": 1,
                "beds": 1,
                "bathrooms": 1,
                "is_featured": False,
                "description": "A romantic A-frame cabin designed for couples. Glass ceiling for watching constellations, outdoor heated jacuzzi bathtub overlooking pine forests, and cozy pellet fireplace.",
                "amenities": ["High-speed Wi-Fi", "Scenic Mountain View", "Hot Water Geyser", "Free Parking on Premises", "Smart LED TV"],
                "color1": (50, 45, 40),
                "color2": (140, 80, 60),
            },
            {
                "host": host1,
                "title": "Anjuna Boho Studio Apartment near Flea Market",
                "property_type": "apartment",
                "address": "Soranto Vaddo, Anjuna",
                "city": "North Goa",
                "state": "Goa",
                "price_per_night": Decimal("3200.00"),
                "cleaning_fee": Decimal("300.00"),
                "max_guests": 3,
                "bedrooms": 1,
                "beds": 1,
                "bathrooms": 1,
                "is_featured": False,
                "description": "Bright bohemian studio with private balcony shaded by bougainvillea. Shared complex pool, 24/7 security, high-speed WiFi for workation, and walking distance to cafes and beach shacks.",
                "amenities": ["High-speed Wi-Fi", "Air Conditioning", "Private Swimming Pool", "Dedicated Workspace", "Hot Water Geyser"],
                "color1": (20, 110, 110),
                "color2": (240, 130, 90),
            },
        ]

        created_listings = []
        for item in listings_data:
            listing, created = Listing.objects.get_or_create(
                title=item["title"],
                defaults={
                    "host": item["host"],
                    "property_type": item["property_type"],
                    "address": item["address"],
                    "city": item["city"],
                    "state": item["state"],
                    "country": "India",
                    "price_per_night": item["price_per_night"],
                    "cleaning_fee": item["cleaning_fee"],
                    "max_guests": item["max_guests"],
                    "bedrooms": item["bedrooms"],
                    "beds": item["beds"],
                    "bathrooms": item["bathrooms"],
                    "is_active": True,
                    "is_featured": item["is_featured"],
                    "description": item["description"],
                }
            )

            # Assign amenities
            for a_name in item["amenities"]:
                if a_name in amenities_dict:
                    listing.amenities.add(amenities_dict[a_name])

            # Generate aesthetic local cover photo if no images
            if not listing.images.exists():
                img_file = create_styled_image(
                    title=listing.title[:38],
                    subtitle=f"{listing.city}, {listing.state} · ₹{int(listing.price_per_night)}/night",
                    color1=item["color1"],
                    color2=item["color2"],
                )
                filename = f"{listing.slug}_cover.jpg"
                ListingImage.objects.create(
                    listing=listing,
                    image=img_file.name if hasattr(img_file, 'name') else filename,
                    is_cover=True,
                    caption=f"Exterior photo of {listing.title}"
                )
                # Save file via Django storage
                cover_img = listing.images.first()
                cover_img.image.save(filename, img_file, save=True)

            created_listings.append(listing)

        self.stdout.write(self.style.SUCCESS(f" {len(created_listings)} listings created and configured with photos."))

        # 4. Create Realistic Completed Bookings & Reviews
        today = timezone.now().date()

        # Completed booking 1 (in Goa) by guest1
        goa_listing = created_listings[0]
        check_in_past = today - timedelta(days=20)
        check_out_past = today - timedelta(days=16)

        past_booking1, _ = Booking.objects.get_or_create(
            listing=goa_listing,
            guest=guest1,
            check_in=check_in_past,
            check_out=check_out_past,
            defaults={
                "guests_count": 4,
                "price_per_night": goa_listing.price_per_night,
                "total_nights": 4,
                "subtotal": goa_listing.price_per_night * 4,
                "service_fee": Decimal("2900.00"),
                "cleaning_fee": goa_listing.cleaning_fee,
                "total_amount": (goa_listing.price_per_night * 4) + Decimal("2900.00") + goa_listing.cleaning_fee,
                "status": "completed",
                "payment_status": "paid",
            }
        )

        Review.objects.get_or_create(
            listing=goa_listing,
            booking=past_booking1,
            user=guest1,
            defaults={
                "rating": 5,
                "comment": "Absolutely extraordinary stay! The private pool was pristine and the sunset over the Arabian Sea from the balcony is something we will never forget. Host Rajesh was attentive and made our holiday seamless.",
            }
        )

        # Completed booking 2 (in Manali) by guest1
        manali_listing = created_listings[1]
        check_in_past2 = today - timedelta(days=40)
        check_out_past2 = today - timedelta(days=36)

        past_booking2, _ = Booking.objects.get_or_create(
            listing=manali_listing,
            guest=guest1,
            check_in=check_in_past2,
            check_out=check_out_past2,
            defaults={
                "guests_count": 2,
                "price_per_night": manali_listing.price_per_night,
                "total_nights": 4,
                "subtotal": manali_listing.price_per_night * 4,
                "service_fee": Decimal("1360.00"),
                "cleaning_fee": manali_listing.cleaning_fee,
                "total_amount": (manali_listing.price_per_night * 4) + Decimal("1360.00") + manali_listing.cleaning_fee,
                "status": "completed",
                "payment_status": "paid",
            }
        )

        Review.objects.get_or_create(
            listing=manali_listing,
            booking=past_booking2,
            user=guest1,
            defaults={
                "rating": 5,
                "comment": "Waking up to the apple trees and fresh pine scent was magical. High-speed Wi-Fi worked flawlessly for my Zoom calls. Ananya was a superb host with great local cafe recommendations.",
            }
        )

        # 5. Create an Upcoming Booking
        upcoming_checkin = today + timedelta(days=10)
        upcoming_checkout = today + timedelta(days=14)
        jaipur_listing = created_listings[2]

        Booking.objects.get_or_create(
            listing=jaipur_listing,
            guest=guest1,
            check_in=upcoming_checkin,
            check_out=upcoming_checkout,
            defaults={
                "guests_count": 2,
                "price_per_night": jaipur_listing.price_per_night,
                "total_nights": 4,
                "subtotal": jaipur_listing.price_per_night * 4,
                "service_fee": Decimal("840.00"),
                "cleaning_fee": jaipur_listing.cleaning_fee,
                "total_amount": (jaipur_listing.price_per_night * 4) + Decimal("840.00") + jaipur_listing.cleaning_fee,
                "status": "confirmed",
                "payment_status": "pay_at_property",
            }
        )

        # 6. Create Wishlist items for guest1
        Wishlist.objects.get_or_create(user=guest1, listing=created_listings[3]) # Udaipur
        Wishlist.objects.get_or_create(user=guest1, listing=created_listings[5]) # Rishikesh

        self.stdout.write(self.style.SUCCESS(" Sample bookings, reviews, and wishlists populated successfully!"))
        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(self.style.SUCCESS("APNASTAY READY FOR DEMO & TESTING"))
        self.stdout.write("Credentials:")
        self.stdout.write("  Admin: admin / admin123")
        self.stdout.write("  Host 1: host1 / host123")
        self.stdout.write("  Host 2: host2 / host234")
        self.stdout.write("  Guest 1: guest1 / guest123")
        self.stdout.write(self.style.NOTICE("=" * 60))
