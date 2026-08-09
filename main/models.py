from django.conf import settings
from django.db import models


class Project(models.Model):
    STATUS_CHOICES = [
        ("draft", "Qoralama"),
        ("active", "Faol"),
        ("completed", "Tugallangan"),
        ("archived", "Arxivlangan"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


class Drawing(models.Model):
    STATUS_CHOICES = [
        ("uploaded", "Yuklangan"),
        ("processing", "Hisoblanmoqda"),
        ("processed", "Tayyor"),
        ("failed", "Xatolik"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="drawings",
    )

    file = models.FileField(upload_to="drawings/%Y/%m/")
    original_name = models.CharField(max_length=255, blank=True)

    file_type = models.CharField(max_length=20, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="uploaded",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_name or self.file.name


class Material(models.Model):
    CATEGORY_CHOICES = [
        ("wall", "Devor materiali"),
        ("concrete", "Beton"),
        ("cement", "Sement"),
        ("sand", "Qum"),
        ("gravel", "Shag'al"),
        ("rebar", "Armatura"),
        ("other", "Boshqa"),
    ]

    name = models.CharField(max_length=150)

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="other",
    )

    unit = models.CharField(
        max_length=30,
        help_text="Masalan: dona, kg, tonna, m³, metr",
    )

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class MaterialPrice(models.Model):
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name="prices",
    )

    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    unit = models.CharField(max_length=30)

    source = models.CharField(
        max_length=200,
        blank=True,
        help_text="Narx manbasi yoki do'kon nomi",
    )

    region = models.CharField(
        max_length=100,
        blank=True,
        help_text="Masalan: Toshkent",
    )

    valid_from = models.DateField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.material.name} — {self.price} so'm"


class Calculation(models.Model):
    STATUS_CHOICES = [
        ("pending", "Kutilmoqda"),
        ("processing", "Hisoblanmoqda"),
        ("completed", "Tayyor"),
        ("failed", "Xatolik"),
    ]

    drawing = models.ForeignKey(
        Drawing,
        on_delete=models.CASCADE,
        related_name="calculations",
    )

    total_area = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="m²",
    )

    total_wall_length = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="metr",
    )

    total_material_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    currency = models.CharField(
        max_length=10,
        default="UZS",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Calculation #{self.id}"


class CalculationItem(models.Model):
    calculation = models.ForeignKey(
        Calculation,
        on_delete=models.CASCADE,
        related_name="items",
    )

    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="calculation_items",
    )

    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=3,
    )

    unit = models.CharField(max_length=30)

    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.material.name} — {self.quantity} {self.unit}"