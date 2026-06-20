from django.db import models
from django.utils import timezone
from django.db.models import F, Sum
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import Case, Value, When


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=300,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def price(self):
        return self.exclude(status='done').annotate(
            price=Sum(F('order_products__product__price') * F('order_products__quantity'))
        )


    def status_order(self):
        return self.annotate(
            status_order=Case(
                When(status='new', then=Value(1)),
                When(status='cook', then=Value(2)),
                When(status='delivery', then=Value(3)),
                When(status='done', then=Value(4)),
            )
        ).order_by('status_order')


class Order(models.Model):
    address = models.CharField(
        max_length=50,
        verbose_name='адрес',
        db_index=True,
    )
    firstname = models.CharField(
        max_length=50,
        verbose_name='имя',
        db_index=True,
    )
    lastname = models.CharField(
        max_length=50,
        verbose_name='фамилия',
        db_index=True,
    )
    phonenumber = PhoneNumberField(
        region="RU",
        verbose_name='номер телефона',
    )
    status = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name='Статус',
        choices=(
            ('new', 'Необработанный'),
            ('cook', 'В сборке'),
            ('delivery', 'В пути'),
            ('done', 'Доставлен'),
        ),
        default='new',
    )
    pay_method = models.CharField(
        max_length=20,
        db_index=True,
        blank=True,
        verbose_name='Способ оплаты',
        choices=(
            ('online', 'Онлайн'),
            ('cash', 'наличными'),
        ),
    )
    comment = models.TextField(verbose_name='Комментарий', blank=True)
    created_at = models.DateTimeField(
        verbose_name='Заказ создан',
        default=timezone.now,
        db_index=True,)
    called_at = models.DateTimeField(
        verbose_name='Звонок покупателю',
        blank=True,
        null=True,
        db_index=True,
    )
    delivery_at = models.DateTimeField(
        verbose_name='Передан в доставку',
        blank=True,
        null=True,
        db_index=True,
    )
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='orders',
        verbose_name="ресторан",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f"{self.firstname} {self.lastname}; {self.address}; {self.phonenumber}"


class OrderProduct(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='order_products',
        verbose_name="заказ",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_products',
        verbose_name='продукт',
    )
    quantity = models.IntegerField(
        verbose_name='количество',
        validators=[MinValueValidator(1)],
    )
    cost = models.DecimalField(
        verbose_name='стоимость',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )


    class Meta:
        verbose_name = 'продукт в заказе'
        verbose_name_plural = 'продукты в заказе'
        unique_together = [
            ['order', 'product']
        ]

    def __str__(self):
        return f"{self.order.firstname} {self.order.lastname} - {self.product.name}"
