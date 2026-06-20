from django.db import models
from .helpers_function import fetch_coordinates
from django.utils import timezone
from django.conf import settings


class Location(models.Model):
    address = models.CharField(
        'адрес',
        max_length=200,
        unique=True,
    )
    lat = models.FloatField(blank=True, null=True, verbose_name="Широта")
    lon = models.FloatField(blank=True, null=True, verbose_name="Долгота")
    request_at = models.DateTimeField(blank=True, null=True, db_index=True,)

    def save(self, *args, **kwargs):
        yandex_api_key = settings.YANDEX_API_KEY
        coordinates = fetch_coordinates(yandex_api_key, self.address)
        if coordinates:
            location_lon, location_lat = coordinates
            self.lat = location_lat
            self.lon = location_lon
            self.request_at = timezone.now()
        else:
            self.lat = None
            self.lon = None
            self.request_at = None
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'адрес'
        verbose_name_plural = 'адреса'

    def __str__(self):
        return self.address
        
