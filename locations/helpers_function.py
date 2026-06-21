import requests

from django.conf import settings
from .models import Location
from django.utils import timezone


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    try:
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        })
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        return None
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def save_address(address):
    yandex_api_key = settings.YANDEX_API_KEY
    coordinates = fetch_coordinates(yandex_api_key, address)
    if coordinates:
        location_lon, location_lat = coordinates
        request_at = timezone.now()
    else:
        location_lon = None
        location_lat = None
        request_at = None
    Location.objects.get_or_create(
        address = address,
            defaults={
                'lon': location_lon,
                'lat': location_lat,
                'request_at': request_at,
            }
        )