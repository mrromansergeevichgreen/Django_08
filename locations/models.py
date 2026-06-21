from django.db import models


class Location(models.Model):
    address = models.CharField(
        'адрес',
        max_length=200,
        unique=True,
    )
    lat = models.FloatField(blank=True, null=True, verbose_name="Широта")
    lon = models.FloatField(blank=True, null=True, verbose_name="Долгота")
    request_at = models.DateTimeField(blank=True, null=True, db_index=True,)

    class Meta:
        verbose_name = 'адрес'
        verbose_name_plural = 'адреса'

    def __str__(self):
        return self.address
        
