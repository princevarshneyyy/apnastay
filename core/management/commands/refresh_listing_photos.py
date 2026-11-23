"""
Replace every sample listing's photos with location-accurate images and
reset nightly prices to an affordable range starting at Rs 1,000.

Location photos come from Wikimedia Commons; each file's title names the
place it shows (e.g. "Courtyard of Samode Haveli, Jaipur"). A few generic
interior shots (bedrooms / living rooms) come from Unsplash.

Usage:
    python manage.py refresh_listing_photos            # photos + prices
    python manage.py refresh_listing_photos --prices-only
"""
import time
import urllib.request
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from listings.models import Listing, ListingImage

USER_AGENT = "ApnaStayDemo/1.0 (sample data seeding)"


def wm(path):
    """Wikimedia Commons file given as '<hash dir>/<file name>' (e.g. '1/1f/Foo.jpg')."""
    return ("wm", path)


def us(photo_id):
    """Unsplash photo id."""
    return ("us", photo_id)


# Generic interiors, not tied to any city.
BEDROOM_CLASSIC = us("1618773928121-c32242e63f39")
BEDROOM_WOOD = us("1582719478250-c89cae4dc85b")
BEDROOM_LUXE = us("1590490360182-c33d57733427")
BEDROOM_COSY = us("1522771739844-6a9f6d5f14af")
BED_DETAIL = us("1590073242678-70ee3fc28e8e")
LIVING_PLANTS = us("1502672260266-1c1ef2d93688")
LIVING_GREEN = us("1616046229478-9901c5536a45")
LIVING_MINIMAL = us("1513694203232-719a280e022f")
LIVING_MODERN = us("1600607687939-ce8a6c25118c")

# title -> (price_per_night, cleaning_fee, [(source, caption), ...]); first photo is the cover.
LISTINGS = {
    "Villa Oceana - Luxury Sea-Facing Villa with Private Pool": (4500, 500, [
        (us("1580587771525-78b9dba3b914"), "Villa exterior with private pool"),
        (us("1613977257363-707ba9348227"), "Pool deck and garden"),
        (wm("1/1f/Calangute_beach_bear_Panaji%2C_Goa_%28December_2018%29.jpg"), "Calangute Beach, a short walk away"),
        (BEDROOM_LUXE, "Master bedroom"),
    ]),
    "The Himalayan Cedar Chalet & Apple Orchard Retreat": (2200, 200, [
        (wm("7/7a/Cottages_Simsa_Manali_Himachal_May24_A7CR_00116.jpg"), "Cottages in Simsa, Manali"),
        (wm("d/de/Snow_Rohtang_Range_Manali_May24_A7CR_00128.jpg"), "Snow-capped Rohtang range from Manali"),
        (wm("8/82/Old_manali_lazy_dog_lounge.jpg"), "Riverside cafes in Old Manali"),
        (LIVING_MINIMAL, "Living room"),
    ]),
    "Royal Haveli Courtyard Suite near Hawa Mahal": (1800, 150, [
        (wm("d/df/Courtyard_of_Samode_Haveli%2C_Jaipur.jpg"), "Haveli courtyard, Jaipur"),
        (wm("4/41/East_facade_Hawa_Mahal_Jaipur_from_ground_level_%28July_2022%29_-_img_01.jpg"), "Hawa Mahal, steps away"),
        (us("1599661046289-e31897846e41"), "Amber Fort, Jaipur"),
        (BEDROOM_CLASSIC, "Suite bedroom"),
    ]),
    "Lake Pichola Sunset Luxury Villa": (5500, 500, [
        (wm("7/74/20191207_Lake_Pichola%2C_City_Palace%2C_Udaipur%2C_1516_7254.jpg"), "Lake Pichola and City Palace, Udaipur"),
        (wm("0/07/Taj_Lake_Palace_Udaipur_from_City_Palace.jpg"), "Lake Palace view"),
        (wm("5/59/20191207_Bagore_Ki_Haveli%2C_Udaipur%2C_0647_7056.jpg"), "Heritage haveli courtyard, Udaipur"),
        (BEDROOM_WOOD, "Bedroom with lake-facing windows"),
    ]),
    "Emerald Palms Backwater Homestay & Kayak Haven": (1500, 150, [
        (wm("3/35/Traditional_Kerala_House_located_in_lake_side_of_Punnamada_Backwaters.jpg"), "Traditional Kerala house on Punnamada backwaters"),
        (wm("f/f4/Alleppey_Backwaters_%2816051710115%29.jpg"), "Village life on the backwaters"),
        (wm("b/b3/Alleppey_backwaters.2.jpg"), "Palm-lined canals"),
        (BED_DETAIL, "Guest bedroom"),
    ]),
    "Ganga Riverfront Yoga Retreat & Penthouse": (1600, 150, [
        (wm("1/13/Ganga_ghats%2C_Laxman_jhula%2C_Rishikesh.jpg"), "Ganga ghats near Laxman Jhula, Rishikesh"),
        (wm("5/5d/Ganga_ghats%2C_Laxman_jhula%2C_Rishikesh_2.jpg"), "View from Laxman Jhula"),
        (LIVING_PLANTS, "Living room"),
        (BEDROOM_COSY, "Bedroom"),
    ]),
    "Infinity Mist Hilltop Farmhouse & Mango Orchard": (3800, 400, [
        (us("1600585154340-be6161a56a0c"), "Farmhouse exterior"),
        (wm("b/b4/Lonavala_Valley_%2851430499813%29.jpg"), "Lonavala valley"),
        (wm("6/6b/Lonavla_view.jpg"), "Sunset over the Sahyadri hills"),
        (us("1512917774080-9991f1c4c750"), "Private pool"),
    ]),
    "Pinecone Studio Cabin with Heated Jacuzzi": (2400, 200, [
        (us("1449158743715-0a90ebb6d2d8"), "Wooden cabin among the pines"),
        (wm("6/6d/Old_manali.jpg"), "Manalsu river, Old Manali"),
        (wm("d/de/Snow_Rohtang_Range_Manali_May24_A7CR_00128.jpg"), "Snow peaks above Manali"),
        (LIVING_MINIMAL, "Cabin interior"),
    ]),
    "Anjuna Boho Studio Apartment near Flea Market": (1000, 100, [
        (us("1522708323590-d24dbb6b0267"), "Studio living and kitchen"),
        (us("1493809842364-78817add7ffb"), "Lounge area"),
        (wm("c/cf/Anjuna_Beach%2C_Goa%2C_India%2C_Legendary_Curlies_beach_shack.jpg"), "Anjuna Beach shacks"),
        (us("1507652313519-d4e9174996dd"), "Bathroom"),
    ]),
    "Casa Portuguesa - Heritage Villa with Frangipani Courtyard": (3200, 300, [
        (wm("6/6d/House_of_Monsignor_Herculano_Damasceno_Olivet_Xavier_Gonsalves%2C_Cana%2C_Benaulim%2C_Goa.jpg"), "Portuguese-era house in Benaulim"),
        (wm("f/f0/2008-03-09_Colva_Beach.jpg"), "Colva Beach nearby"),
        (LIVING_MODERN, "Living room"),
    ]),
    "Whispering Pines A-Frame Wooden Chalet": (1900, 150, [
        (wm("8/83/Shimla%2C_India%2C_Panoramic_view_of_Shimla_hills.jpg"), "Panoramic view of the Shimla hills"),
        (wm("1/17/Shimla_4.jpg"), "Pine-covered slopes of Shimla"),
        (wm("6/69/Longwood_%28Shimla%29.jpg"), "Shimla in winter snow"),
    ]),
    "Munnar Cloud Valley Tea Plantation Bungalow": (1700, 150, [
        (wm("9/94/Munnar_tea_garden_Nov-2026_1.jpg"), "Munnar tea gardens"),
        (wm("9/98/Munnar_tea_garden_Nov-2026_2.jpg"), "Rolling tea estates"),
        (wm("0/09/Munnar_-_Tea_Plantations.jpg"), "Tea plantations around Munnar"),
        (LIVING_GREEN, "Living room"),
    ]),
    "The Blue City Heritage Haveli with Mehrangarh View": (1200, 100, [
        (wm("6/64/Jodhpur_the_blue_city_view_over_the_maze_of_houses_India_25Aug2006.jpg"), "The blue city of Jodhpur"),
        (wm("e/e1/Jodhpur%2C_India%2C_Old_City_and_Mehrangarh_Fort.jpg"), "Old city lane with Mehrangarh Fort"),
        (wm("1/13/Jodhpur%2C_India%2C_Blue_City.jpg"), "Blue-washed lanes of the old city"),
        (BEDROOM_CLASSIC, "Guest room"),
    ]),
    "Coorg Misty Pines Coffee Plantation Cottage": (2000, 200, [
        (wm("4/40/Nakoor_Volkot_Suntikoppa_Coorg_Apr24_A7C_10727.jpg"), "Estate bungalow, Suntikoppa, Coorg"),
        (wm("a/a3/Road_Coffee_Estate_Inakanahalli_Coorg_Jun24_A7CR_01542.jpg"), "Coffee estate trail"),
        (wm("0/0d/Madikeri_village.jpg"), "Misty hills near Madikeri"),
        (wm("c/c5/Beans_Drying_Coffee_Robusta_Balamuri_Coorg_Feb24_A7C_09491.jpg"), "Coffee beans drying on the estate"),
    ]),
    "White Town French Quarter Villa near Promenade": (2800, 250, [
        (wm("4/49/Pondicherry_-_55327893753.jpg"), "French colonial villa, White Town"),
        (wm("3/34/Pondicherry_-_55326819627.jpg"), "Heritage street in the French Quarter"),
        (wm("8/8c/Pondicherry_Beach_view.jpg"), "Promenade Beach"),
        (wm("6/60/Pondicherry_-_55327894363.jpg"), "Colonial architecture nearby"),
    ]),
    "Wayanad Canopy Luxury Treehouse & Nature Stay": (2600, 250, [
        (wm("1/12/Thunacadavu_Tree_House_tourism_03.jpg"), "Kerala forest treehouse"),
        (wm("9/94/Huts_in_En_Ooru%2C_Pookode%2C_Wayanad_3.jpg"), "Hillside huts in Pookode, Wayanad"),
        (wm("e/e1/Chembra_Peak_Heart_Lake.jpg"), "Heart Lake on Chembra Peak, Wayanad"),
    ]),
    "Alibaug Coastal Palms Beachfront Farmhouse": (4200, 400, [
        (us("1600596542815-ffad4c1539a9"), "Farmhouse with private pool"),
        (wm("7/71/Alibag_Beach_in_November.JPG"), "Alibag Beach"),
        (wm("2/24/Alibag_Beach_-_panoramio_%281%29.jpg"), "Palm-lined seafront, Alibag"),
        (us("1512917774080-9991f1c4c750"), "Pool and garden"),
    ]),
    "Dharamshala Cedar Heights Mountain Chalet": (1800, 150, [
        (wm("a/a6/Flowering_Trees_in_spring_in_DHARAMSHALA%28HP-INDIA%29_Dhauladhar_Ranges_in_Kangra_velley.jpg"), "Spring blossoms below the Dhauladhar, Dharamshala"),
        (wm("5/5f/Dhauladhar_alpenglow_above_Dharamshala%2C_India.jpg"), "Dhauladhar alpenglow above Dharamshala"),
        (wm("e/e7/Main_Street_Temple_-_McLeod_Ganj_-_Himachal_Pradesh_-_India_%2826207379983%29.jpg"), "Main Street temple, McLeod Ganj"),
        (wm("9/97/The_Dhauladhar_Range.jpg"), "The Dhauladhar range"),
    ]),
    "Varanasi Assi Ghat Heritage Ganga Suite": (1100, 100, [
        (wm("3/3a/Varanasi_Munshi_Ghat3.jpg"), "Heritage ghats on the Ganga, Varanasi"),
        (wm("7/7c/Assi_Ghat_Varanasi_%282%29.jpg"), "Assi Ghat"),
        (wm("b/b1/Varanasi_2010_ghats3.jpg"), "Morning boats along the ghats"),
        (BEDROOM_CLASSIC, "Suite bedroom"),
    ]),
}


def candidate_urls(source):
    kind, ref = source
    if kind == "us":
        return [f"https://images.unsplash.com/photo-{ref}?w=1280&q=85"]
    name = ref.rsplit("/", 1)[1]
    return [
        f"https://upload.wikimedia.org/wikipedia/commons/thumb/{ref}/1280px-{name}",
        f"https://upload.wikimedia.org/wikipedia/commons/{ref}",  # original, if smaller than 1280px
    ]


def download(source):
    for url in candidate_urls(source):
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=40) as resp:
                    data = resp.read()
                if len(data) > 5000:
                    return data
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(5 * (attempt + 1))
                    continue
                break
            except Exception:
                time.sleep(2)
    return None


class Command(BaseCommand):
    help = "Replace sample listing photos with location-accurate images and reset prices (from Rs 1,000/night)."

    def add_arguments(self, parser):
        parser.add_argument("--prices-only", action="store_true", help="Only update prices, leave photos alone.")

    def handle(self, *args, **options):
        for title, (price, cleaning, photos) in LISTINGS.items():
            listing = Listing.objects.filter(title=title).first()
            if not listing:
                self.stdout.write(self.style.WARNING(f"Skipping (not found): {title}"))
                continue

            listing.price_per_night = Decimal(price)
            listing.cleaning_fee = Decimal(cleaning)
            listing.save(update_fields=["price_per_night", "cleaning_fee"])
            self.stdout.write(f"{listing.city:<12} Rs {price:>5}/night  {title}")

            if options["prices_only"]:
                continue

            # Download everything first so a network failure never leaves a listing without photos.
            downloaded = []
            for source, caption in photos:
                data = download(source)
                if data is None:
                    self.stdout.write(self.style.WARNING(f"  failed: {candidate_urls(source)[0]}"))
                    continue
                downloaded.append((data, caption))
                time.sleep(1)  # be polite to Wikimedia

            if not downloaded:
                self.stdout.write(self.style.ERROR("  no photos downloaded; keeping existing ones"))
                continue

            for old in listing.images.all():
                old.image.delete(save=False)
                old.delete()

            for idx, (data, caption) in enumerate(downloaded):
                name = f"{listing.slug}_{'cover' if idx == 0 else f'gallery_{idx}'}.jpg"
                img = ListingImage(listing=listing, is_cover=(idx == 0), caption=caption)
                img.image.save(name, ContentFile(data), save=True)
            self.stdout.write(self.style.SUCCESS(f"  {len(downloaded)}/{len(photos)} photos saved"))

        low = Listing.objects.order_by("price_per_night").first()
        if low:
            self.stdout.write(self.style.SUCCESS(f"Done. Prices now start at Rs {int(low.price_per_night)}/night."))
