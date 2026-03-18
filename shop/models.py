from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.db.models import Index, UniqueConstraint
from django.contrib.auth.models import User

def get_total_cost(self):
    return sum(item.price * item.quantity for item in self.items.all())
class Order(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.first_name} {self.last_name}"

    # ← ADD THIS METHOD
    def get_total_cost(self):
        return sum(item.price * item.quantity for item in self.items.all())
class Category(models.Model):
    """Product categories for organizing the shop"""
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])


class Product(models.Model):
    """Product model for all items in the shop"""
    PRODUCT_TYPE_CHOICES = [
        ('women', 'Women'),
        ('kids', 'Kids'),
    ]

    STYLE_CHOICES = [
        ('traditional', 'Traditional'),
        ('western', 'Western'),
        ('fusion', 'Fusion'),
    ]

    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, db_index=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='women')
    style = models.CharField(max_length=20, choices=STYLE_CHOICES, default='traditional')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    available = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    featured = models.BooleanField(default=False)
    
    # Additional product details
    material = models.CharField(max_length=100, blank=True)
    care_instructions = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [Index(fields=['id', 'slug'])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])

    def get_display_price(self):
        """Return the price to display (discount price if available)"""
        return self.discount_price if self.discount_price else self.price

    def get_discount_percentage(self):
        """Calculate discount percentage"""
        if self.discount_price and self.price > self.discount_price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0


class ProductImage(models.Model):
    """Multiple images for each product"""
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'created_at']

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductSize(models.Model):
    """Available sizes for products"""
    SIZE_CHOICES = [
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Double Extra Large'),
    ]

    product = models.ForeignKey(Product, related_name='sizes', on_delete=models.CASCADE)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    available = models.BooleanField(default=True)

    class Meta:
        constraints = [UniqueConstraint(fields=['product', 'size'], name='unique_product_size')]
        ordering = ['size']

    def __str__(self):
        return f"{self.product.name} - {self.get_size_display()}"



class Contact(models.Model):
    """Contact form submissions"""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200, choices=[
        ('order', 'Order Related'),
        ('return', 'Return & Exchange'),
        ('feedback', 'Feedback'),
        ('partnership', 'Partnership'),
        ('other', 'Other'),
    ])
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=10, blank=True, null=True)  # ✅ add this
    created_at = models.DateTimeField(auto_now_add=True)

class Blog(models.Model):
    """User-posted blogs/articles"""
    author = models.ForeignKey(User, related_name='blogs', on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    description = models.TextField()
    image = models.ImageField(upload_to='blogs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.author.username}"


class Offer(models.Model):
    """Special offers and promotions"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='offers/', blank=True, null=True)
    discount_percentage = models.PositiveIntegerField(blank=True, null=True, help_text="Discount percentage (e.g., 20 for 20%)")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Fixed discount amount")
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0, help_text="Higher priority offers appear first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return self.title

    def is_valid(self):
        """Check if the offer is currently valid"""
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_until

    def get_discount_display(self):
        """Return a display string for the discount"""
        if self.discount_percentage:
            return f"{self.discount_percentage}% OFF"
        elif self.discount_amount:
            return f"₹{self.discount_amount} OFF"
        return ""
 