import os
import sys
import django
import urllib.request
from decimal import Decimal
from django.core.files.base import ContentFile
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apnastay_project.settings')
django.setup()

from listings.models import Listing, ListingImage, Amenity
from accounts.models import User


def download_image(url, filename, timeout=12):
    """Downloads an image from URL and returns a ContentFile with the given filename."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()
            if len(data) > 1000:
                print(f"  [OK] Downloaded {filename} ({len(data)} bytes)")
                cf = ContentFile(data)
                cf.name = filename
                return cf
    except Exception as e:
        print(f"  [WARN] Failed to download {url}: {e}")
    return None


def run():
    print("=" * 60)
    print("UPDATING APNASTAY COVER PHOTOS & EXPANDING STAY INVENTORY")
    print("=" * 60)

    # Fetch hosts
    host1 = User.objects.filter(username="host1").first() or User.objects.filter(is_host=True).first()
    host2 = User.objects.filter(username="host2").first() or host1
    admin_user = User.objects.filter(username="admin").first()

    amenities = {a.name: a for a in Amenity.objects.all()}

    # Curated real photos for the existing 9 properties
    existing_updates = {
        "Villa Oceana - Luxury Sea-Facing Villa with Private Pool": {
            "cover": "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=1000&q=85",
                "https://images.unsplash.com/photo-1590490360182-c33d57733427?w=1000&q=85",
                "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=1000&q=85"
            ]
        },
        "The Himalayan Cedar Chalet & Apple Orchard Retreat": {
            "cover": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1510798831971-661eb04b3739?w=1000&q=85",
                "https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?w=1000&q=85",
                "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=1000&q=85"
            ]
        },
        "Royal Haveli Courtyard Suite near Hawa Mahal": {
            "cover": "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=1000&q=85",
                "https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=1000&q=85",
                "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=1000&q=85"
            ]
        },
        "Lake Pichola Sunset Luxury Villa": {
            "cover": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=1000&q=85",
                "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=1000&q=85",
                "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=1000&q=85"
            ]
        },
        "Emerald Palms Backwater Homestay & Kayak Haven": {
            "cover": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1590073242678-70ee3fc28e8e?w=1000&q=85",
                "https://images.unsplash.com/photo-1616046229478-9901c5536a45?w=1000&q=85",
                "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1000&q=85"
            ]
        },
        "Ganga Riverfront Yoga Retreat & Penthouse": {
            "cover": "https://images.unsplash.com/photo-1544717305-2782549b5136?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=1000&q=85",
                "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1000&q=85",
                "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=1000&q=85"
            ]
        },
        "Infinity Mist Hilltop Farmhouse & Mango Orchard": {
            "cover": "https://images.unsplash.com/photo-1500076656116-558758c991c1?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1000&q=85",
                "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1000&q=85",
                "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1000&q=85"
            ]
        },
        "Pinecone Studio Cabin with Heated Jacuzzi": {
            "cover": "https://images.unsplash.com/photo-1518780664697-55e3ad937233?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1449158743715-0a90ebb6d2d8?w=1000&q=85",
                "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=1000&q=85",
                "https://images.unsplash.com/photo-1540518614846-7ede433c4ef4?w=1000&q=85"
            ]
        },
        "Anjuna Boho Studio Apartment near Flea Market": {
            "cover": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=1000&q=85",
                "https://images.unsplash.com/photo-1505691938895-1758d7feb511?w=1000&q=85",
                "https://images.unsplash.com/photo-1507652313519-d4e9174996dd?w=1000&q=85"
            ]
        }
    }

    print("\n>>> STEP 1: Replacing cover photos for existing properties...")
    for title, photos in existing_updates.items():
        listing = Listing.objects.filter(title=title).first()
        if not listing:
            continue
        print(f"\nUpdating: {title}")
        # Clear old generated image records
        listing.images.all().delete()

        # Download & set cover
        cover_cf = download_image(photos["cover"], f"{listing.slug}_cover.jpg")
        if cover_cf:
            c_img = ListingImage(listing=listing, is_cover=True, caption=f"Cover view of {listing.title}")
            c_img.image.save(f"{listing.slug}_cover.jpg", cover_cf, save=True)

        # Download gallery
        for idx, g_url in enumerate(photos["gallery"], start=1):
            g_cf = download_image(g_url, f"{listing.slug}_gallery_{idx}.jpg")
            if g_cf:
                g_img = ListingImage(listing=listing, is_cover=False, caption=f"Gallery photo {idx}")
                g_img.image.save(f"{listing.slug}_gallery_{idx}.jpg", g_cf, save=True)

    print("\n>>> STEP 2: Adding 10 brand-new diverse stays across India...")
    new_stays = [
        {
            "host": host1,
            "title": "Casa Portuguesa - Heritage Villa with Frangipani Courtyard",
            "property_type": "villa",
            "address": "Benaulim Village Road",
            "city": "South Goa",
            "state": "Goa",
            "price_per_night": Decimal("9800.00"),
            "cleaning_fee": Decimal("800.00"),
            "max_guests": 6,
            "bedrooms": 3,
            "beds": 3,
            "bathrooms": 3,
            "is_featured": True,
            "description": "Step into 19th-century Goan-Portuguese charm. Featuring terracotta tiled verandas, high vaulted ceilings, antique rosewood furniture, private splash pool, and tranquil palm gardens. 5 minutes from pristine Benaulim beach.",
            "amenities_list": ["High-speed Wi-Fi", "Private Swimming Pool", "Air Conditioning", "Fully Equipped Kitchen", "Free Parking on Premises", "Daily Housekeeping", "Smart LED TV"],
            "cover": "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1000&q=85",
                "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?w=1000&q=85",
                "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1000&q=85"
            ]
        },
        {
            "host": host2,
            "title": "Whispering Pines A-Frame Wooden Chalet",
            "property_type": "cabin",
            "address": "Mashobra Forest Ridge",
            "city": "Shimla",
            "state": "Himachal Pradesh",
            "price_per_night": Decimal("5800.00"),
            "cleaning_fee": Decimal("500.00"),
            "max_guests": 4,
            "bedrooms": 2,
            "beds": 2,
            "bathrooms": 2,
            "is_featured": True,
            "description": "An authentic Scandinavian-style A-frame chalet tucked deep inside Mashobra's deodar forest. Glass-wall living room, cast-iron fireplace, and sweeping views of cedar-covered slopes and starry night skies.",
            "amenities_list": ["High-speed Wi-Fi", "Scenic Mountain View", "Dedicated Workspace", "Free Parking on Premises", "Hot Water Geyser", "Pet Friendly"],
            "cover": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1510798831971-661eb04b3739?w=1000&q=85",
                "https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?w=1000&q=85"
            ]
        },
        {
            "host": host1,
            "title": "Munnar Cloud Valley Tea Plantation Bungalow",
            "property_type": "homestay",
            "address": "Chithirapuram Estate",
            "city": "Kerala",
            "state": "Kerala",
            "price_per_night": Decimal("4900.00"),
            "cleaning_fee": Decimal("400.00"),
            "max_guests": 5,
            "bedrooms": 2,
            "beds": 3,
            "bathrooms": 2,
            "is_featured": True,
            "description": "Wake up floating above the clouds. Colonial British-era tea bungalow perched amidst rolling emerald green tea estates. Enjoy morning bird-watching walks, fresh estate tea tastings, and cool mountain breezes.",
            "amenities_list": ["High-speed Wi-Fi", "Scenic Mountain View", "Free Parking on Premises", "Dedicated Workspace", "Daily Housekeeping"],
            "cover": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1000&q=85",
                "https://images.unsplash.com/photo-1616046229478-9901c5536a45?w=1000&q=85"
            ]
        },
        {
            "host": host2,
            "title": "The Blue City Heritage Haveli with Mehrangarh View",
            "property_type": "homestay",
            "address": "Navchokiya Heritage Street",
            "city": "Jodhpur",
            "state": "Rajasthan",
            "price_per_night": Decimal("3900.00"),
            "cleaning_fee": Decimal("300.00"),
            "max_guests": 4,
            "bedrooms": 2,
            "beds": 2,
            "bathrooms": 2,
            "is_featured": False,
            "description": "Authentic indigo-blue haveli nestled in Jodhpur's historic walled city. Breathtaking rooftop dining terrace gazing up at the majestic Mehrangarh Fort. Handcrafted Marwari furnishings and warm family hospitality.",
            "amenities_list": ["High-speed Wi-Fi", "Air Conditioning", "Smart LED TV", "Hot Water Geyser", "Daily Housekeeping"],
            "cover": "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=1000&q=85",
                "https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=1000&q=85"
            ]
        },
        {
            "host": host1,
            "title": "Coorg Misty Pines Coffee Plantation Cottage",
            "property_type": "cottage",
            "address": "Madikeri Estate Road",
            "city": "Coorg",
            "state": "Karnataka",
            "price_per_night": Decimal("6400.00"),
            "cleaning_fee": Decimal("500.00"),
            "max_guests": 6,
            "bedrooms": 3,
            "beds": 3,
            "bathrooms": 3,
            "is_featured": True,
            "description": "Immerse yourself in aromatic coffee and pepper groves. Stone-built cottage with outdoor bonfire pit, streaming brook nearby, Kodava home-cooked meals, and guided plantation walking tours.",
            "amenities_list": ["High-speed Wi-Fi", "Free Parking on Premises", "Pet Friendly", "Hot Water Geyser", "Dedicated Workspace"],
            "cover": "https://images.unsplash.com/photo-1518780664697-55e3ad937233?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1510798831971-661eb04b3739?w=1000&q=85",
                "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1000&q=85"
            ]
        },
        {
            "host": host2,
            "title": "White Town French Quarter Villa near Promenade",
            "property_type": "villa",
            "address": "Rue Suffren, White Town",
            "city": "Pondicherry",
            "state": "Puducherry",
            "price_per_night": Decimal("8500.00"),
            "cleaning_fee": Decimal("700.00"),
            "max_guests": 5,
            "bedrooms": 2,
            "beds": 3,
            "bathrooms": 2,
            "is_featured": True,
            "description": "Sunlit mustard-yellow colonial home with bougainvillea draped balconies, arched louvred doors, and high timber ceilings. Just two blocks from the famous Rock Beach Promenade and cozy French bistros.",
            "amenities_list": ["High-speed Wi-Fi", "Air Conditioning", "Fully Equipped Kitchen", "Smart LED TV", "Hot Water Geyser"],
            "cover": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?w=1000&q=85",
                "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=1000&q=85"
            ]
        },
        {
            "host": host1,
            "title": "Wayanad Canopy Luxury Treehouse & Nature Stay",
            "property_type": "unique",
            "address": "Vythiri Rainforest Zone",
            "city": "Kerala",
            "state": "Kerala",
            "price_per_night": Decimal("7500.00"),
            "cleaning_fee": Decimal("500.00"),
            "max_guests": 2,
            "bedrooms": 1,
            "beds": 1,
            "bathrooms": 1,
            "is_featured": True,
            "description": "Perched 40 feet high above the rainforest canopy. Built with native bamboo and teakwood, offering panoramic jungle vistas, morning mist, and complete romantic seclusion for nature lovers.",
            "amenities_list": ["High-speed Wi-Fi", "Scenic Mountain View", "Free Parking on Premises", "Hot Water Geyser", "Daily Housekeeping"],
            "cover": "https://images.unsplash.com/photo-1470246973918-29a93221c455?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1449158743715-0a90ebb6d2d8?w=1000&q=85",
                "https://images.unsplash.com/photo-1518780664697-55e3ad937233?w=1000&q=85"
            ]
        },
        {
            "host": host2,
            "title": "Alibaug Coastal Palms Beachfront Farmhouse",
            "property_type": "farmhouse",
            "address": "Awas Beach Road",
            "city": "Alibaug",
            "state": "Maharashtra",
            "price_per_night": Decimal("14000.00"),
            "cleaning_fee": Decimal("1000.00"),
            "max_guests": 10,
            "bedrooms": 4,
            "beds": 5,
            "bathrooms": 4,
            "is_featured": False,
            "description": "Sprawling 1.5-acre coconut grove estate featuring a 40-foot private swimming pool, gazebo, and lawn cricket setup. A fast 20-minute speedboat ride from Gateway of India, Mumbai.",
            "amenities_list": ["High-speed Wi-Fi", "Private Swimming Pool", "Air Conditioning", "Fully Equipped Kitchen", "Free Parking on Premises", "Smart LED TV", "Pet Friendly"],
            "cover": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1000&q=85",
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1000&q=85"
            ]
        },
        {
            "host": host1,
            "title": "Dharamshala Cedar Heights Mountain Chalet",
            "property_type": "resort",
            "address": "Dharamkot Hilltop",
            "city": "Dharamshala",
            "state": "Himachal Pradesh",
            "price_per_night": Decimal("5900.00"),
            "cleaning_fee": Decimal("500.00"),
            "max_guests": 4,
            "bedrooms": 2,
            "beds": 2,
            "bathrooms": 2,
            "is_featured": False,
            "description": "Overlooking the majestic Dhauladhar snow range. Wooden floors, large glass bay windows, cafe corner, and direct access to Triund trekking trail.",
            "amenities_list": ["High-speed Wi-Fi", "Scenic Mountain View", "Dedicated Workspace", "Free Parking on Premises", "Hot Water Geyser"],
            "cover": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=1000&q=85",
                "https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?w=1000&q=85"
            ]
        },
        {
            "host": host2,
            "title": "Varanasi Assi Ghat Heritage Ganga Suite",
            "property_type": "apartment",
            "address": "Near Assi Ghat Steps",
            "city": "Varanasi",
            "state": "Uttar Pradesh",
            "price_per_night": Decimal("4200.00"),
            "cleaning_fee": Decimal("300.00"),
            "max_guests": 3,
            "bedrooms": 1,
            "beds": 2,
            "bathrooms": 1,
            "is_featured": False,
            "description": "Hear the morning temple bells and flute melodies from your private Ganga-facing balcony. Located right beside historical Assi Ghat, famous for morning Subah-e-Banaras aarti.",
            "amenities_list": ["High-speed Wi-Fi", "Air Conditioning", "Smart LED TV", "Hot Water Geyser", "Daily Housekeeping"],
            "cover": "https://images.unsplash.com/photo-1561501900-3701fa6a0864?w=1000&q=85",
            "gallery": [
                "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=1000&q=85",
                "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1000&q=85"
            ]
        }
    ]

    for item in new_stays:
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
        for a_name in item["amenities_list"]:
            if a_name in amenities:
                listing.amenities.add(amenities[a_name])

        if not listing.images.exists():
            print(f"\nAdding photos for new stay: {listing.title}")
            cover_cf = download_image(item["cover"], f"{listing.slug}_cover.jpg")
            if cover_cf:
                c_img = ListingImage(listing=listing, is_cover=True, caption=f"Cover view of {listing.title}")
                c_img.image.save(f"{listing.slug}_cover.jpg", cover_cf, save=True)

            for idx, g_url in enumerate(item["gallery"], start=1):
                g_cf = download_image(g_url, f"{listing.slug}_gallery_{idx}.jpg")
                if g_cf:
                    g_img = ListingImage(listing=listing, is_cover=False, caption=f"Gallery photo {idx}")
                    g_img.image.save(f"{listing.slug}_gallery_{idx}.jpg", g_cf, save=True)

    total_listings = Listing.objects.count()
    total_images = ListingImage.objects.count()
    print("\n" + "=" * 60)
    print(f"SUCCESS: Now have {total_listings} accommodations with {total_images} real photos!")
    print("=" * 60)


if __name__ == "__main__":
    run()
