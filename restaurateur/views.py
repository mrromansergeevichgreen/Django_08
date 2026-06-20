import re

import requests
from geopy import distance

from django.conf import settings
from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.shortcuts import get_object_or_404

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
from locations.models import Location


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    yandex_api_key = settings.YANDEX_API_KEY
    orders = Order.objects.all().price().prefetch_related('products').status_order()
    restaurants = Restaurant.objects.all().prefetch_related('menu_items')
    for order in orders:
        available_restaurants = []
        order_coordinates = Location.objects.filter(address=order.address).first()
        products_in_order = order.products.values_list('product_id', flat=True)
        for restaurant in restaurants:
            restaurant_coordinates = Location.objects.filter(address=restaurant.address).first()
            if order_coordinates.lat and restaurant_coordinates.lat:
                distance_to_restaurant = f"{distance.distance(
                    (order_coordinates.lat, order_coordinates.lon),
                    (restaurant_coordinates.lat, restaurant_coordinates.lon),
                ).km:.3f} км"
            else:
                distance_to_restaurant = "Не удалось определить расстояние"
            products_in_restaurant = restaurant.menu_items.filter(availability=True).values_list(
                'product_id', flat=True
            )
            if set(products_in_order).issubset(set(products_in_restaurant)):
                available_restaurants.append(f"{restaurant.name} - {distance_to_restaurant}")
            if order_coordinates.lat and restaurant_coordinates.lat:
                available_restaurants = sorted(
                    available_restaurants,
                    key=lambda x: int(re.search(r'\d+', x).group())
                )
        order.available_restaurants = available_restaurants

    return render(request, template_name='order_items.html', context={
        "order_items": orders,
    })
