from django.contrib import admin

from .models import (
    Project,
    Drawing,
    Material,
    MaterialPrice,
    Calculation,
    CalculationItem,
)


# =========================================================
# PROJECT
# =========================================================

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "user",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
        "user__username",
        "user__email",
    )

    list_editable = (
        "status",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-updated_at",
    )


# =========================================================
# DRAWING
# =========================================================

@admin.register(Drawing)
class DrawingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "original_name",
        "project",
        "file_type",
        "status",
        "created_at",
        "processed_at",
    )

    list_filter = (
        "status",
        "file_type",
        "created_at",
    )

    search_fields = (
        "original_name",
        "file",
        "project__name",
        "project__user__username",
    )

    list_editable = (
        "status",
    )

    readonly_fields = (
        "created_at",
        "processed_at",
    )

    autocomplete_fields = (
        "project",
    )

    ordering = (
        "-created_at",
    )


# =========================================================
# MATERIAL
# =========================================================

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "unit",
        "is_active",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "category",
        "unit",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
    )

    list_editable = (
        "category",
        "unit",
        "is_active",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "name",
    )


# =========================================================
# MATERIAL PRICE
# =========================================================

@admin.register(MaterialPrice)
class MaterialPriceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "material",
        "price",
        "unit",
        "region",
        "source",
        "valid_from",
        "created_at",
    )

    list_filter = (
        "region",
        "unit",
        "valid_from",
        "created_at",
    )

    search_fields = (
        "material__name",
        "source",
        "region",
    )

    autocomplete_fields = (
        "material",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )


# =========================================================
# CALCULATION
# =========================================================

@admin.register(Calculation)
class CalculationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "drawing",
        "status",
        "total_area",
        "total_wall_length",
        "total_material_cost",
        "currency",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "currency",
        "created_at",
    )

    search_fields = (
        "drawing__original_name",
        "drawing__project__name",
        "drawing__project__user__username",
        "error_message",
    )

    list_editable = (
        "status",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "drawing",
    )

    ordering = (
        "-created_at",
    )


# =========================================================
# CALCULATION ITEM
# =========================================================

@admin.register(CalculationItem)
class CalculationItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "calculation",
        "material",
        "quantity",
        "unit",
        "unit_price",
        "total_price",
        "created_at",
    )

    list_filter = (
        "unit",
        "material__category",
        "created_at",
    )

    search_fields = (
        "material__name",
        "calculation__drawing__original_name",
        "calculation__drawing__project__name",
    )

    autocomplete_fields = (
        "calculation",
        "material",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "id",
    )