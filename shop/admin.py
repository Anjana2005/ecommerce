from django.contrib import admin
from .models import Category, Product, ProductImage, ProductSize, Blog


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1




@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_filter = ['created_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'product_type', 'style', 'price', 
                    'discount_price', 'stock', 'available', 'featured', 'created_at']
    list_filter = ['available', 'featured', 'product_type', 'style', 
                   'created_at', 'updated_at', 'category']
    list_editable = ['price', 'discount_price', 'available', 'featured', 'stock']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    inlines = [ProductImageInline, ProductSizeInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Classification', {
            'fields': ('product_type', 'style')
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'discount_price', 'stock', 'available', 'featured')
        }),
        ('Product Details', {
            'fields': ('material', 'care_instructions'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name', 'alt_text']


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ['product', 'size', 'available']
    list_filter = ['size', 'available']
    search_fields = ['product__name']





@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'author']
    search_fields = ['title', 'description', 'author__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Blog Information', {
            'fields': ('title', 'description', 'image')
        }),
        ('Author & Dates', {
            'fields': ('author', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )