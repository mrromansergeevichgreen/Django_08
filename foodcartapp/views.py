import json
import pprint

import phonenumbers

from django.http import JsonResponse
from django.db import transaction
from django.templatetags.static import static
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings

from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer

from .models import Product
from .models import Order
from .models import OrderProduct
from .helpers_function import fetch_coordinates
from locations.models import Location


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


class OrderProductSerializer(ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = OrderProductSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = ['id', 'address', 'firstname', 'lastname', 'phonenumber', 'products']


@api_view(['POST'])
@transaction.atomic
def register_order(request):
    yandex_api_key = settings.YANDEX_API_KEY
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    order = serializer.validated_data
    order_from_db, created = Order.objects.get_or_create(
        address=order.get("address"),
        firstname=order.get("firstname"),
        lastname=order.get("lastname"),
        phonenumber=order.get("phonenumber"),
    )
    products = order.get("products")
    for product in products:
        product_from_db = product.get("product")
        OrderProduct.objects.get_or_create(
            order=order_from_db,
            product=product_from_db,
            quantity=product.get("quantity"),
            cost=product.get("quantity") * product_from_db.price
        )
    coordinates = fetch_coordinates(yandex_api_key, order.get("address"))
    if coordinates:
        location_lon, location_lat = coordinates
    else:
        location_lon, location_lat = None, None
    Location.objects.get_or_create(
        address = order.get("address"),
            defaults={
                'lon': location_lon,
                'lat': location_lat,
                'request_at': timezone.now(),
            }
        )
    content = OrderSerializer(order_from_db).data
    return Response(content)
