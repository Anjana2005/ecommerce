# from urllib import request
# from django.shortcuts import render, get_object_or_404, redirect
# from django.core.paginator import Paginator
# from django.contrib.auth import authenticate, login
# from django.contrib.auth.models import User
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from .models import Category, Product, Contact
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render
# from .models import Order
from urllib import request

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, Product, Contact, Order, Blog, Offer

# def cart_add(request, product_id):
#     product = Product.objects.get(id=product_id)
#     cart = request.session.get("cart", {})

#     size = request.POST.get("size") or cart.get(str(product_id), {}).get("size")
#     quantity = int(request.POST.get("quantity", 1))

#     print("=== CART ADD DEBUG ===")
#     print("Product:", product.name)
#     print("Size from POST:", request.POST.get("size"))
#     print("Quantity:", quantity)
#     print("Cart before:", cart)

#     cart[str(product_id)] = {
#         "name": product.name,
#         "price": float(product.get_display_price()),
#         "quantity": quantity,
#         "size": size,
#     }

#     request.session["cart"] = cart
#     request.session.modified = True

#     print("Cart after:", cart)
#     print("======================")

#     return redirect("cart:cart_detail")

@login_required
def profile(request):
    raw_orders = Order.objects.filter(email=request.user.email).order_by('-created_at')
    orders = []
    total_spent = 0
    for order in raw_orders:
        order.total = sum(item.price * item.quantity for item in order.items.all())
        total_spent += order.total
        orders.append(order)
    paid_count = sum(1 for o in orders if o.paid)
    return render(request, 'shop/profile.html', {
        'orders': orders,
        'total_spent': total_spent,
        'paid_count': paid_count,
    })

def product_list(request, category_slug=None):
    """Display list of products, optionally filtered by category"""
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    
    # Filter by category if provided
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Filter by product type
    product_type = request.GET.get('type')
    if product_type in ['women', 'kids']:
        products = products.filter(product_type=product_type)
    
    # Filter by style
    style = request.GET.get('style')
    if style in ['traditional', 'western', 'fusion']:
        products = products.filter(style=style)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'categories': categories,
        'page_obj': page_obj,
        'products': page_obj,
        'search_query': search_query,
    }
    return render(request, 'shop/product/list.html', context)


def product_detail(request, id, slug):
    """Display individual product details"""
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    
    # Get related products from the same category
    related_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'shop/product/detail.html', context)


def home(request):
    """Home page with featured products"""
    featured_products = Product.objects.filter(featured=True, available=True)[:8]
    categories = Category.objects.all()[:6]
    
    # Get latest products
    new_arrivals = Product.objects.filter(available=True).order_by('-created_at')[:8]
    
    # Get latest blogs
    latest_blogs = Blog.objects.all().order_by('-created_at')[:3]
    
    # Get active offers (prioritized)
    active_offers = Offer.objects.filter(is_active=True).order_by('-priority', '-created_at')[:3]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'new_arrivals': new_arrivals,
        'latest_blogs': latest_blogs,
        'active_offers': active_offers,
    }
    return render(request, 'shop/home.html', context)


def about(request):
    """About page"""
    return render(request, 'shop/about.html')


def contact(request):
    """Contact page"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        Contact.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )
        
        messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
        return redirect('shop:contact')
    
    return render(request, 'shop/contact.html')


def signup(request):
    """User signup page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('shop:signup')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return redirect('shop:signup')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return redirect('shop:signup')
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long!')
            return redirect('shop:signup')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        
        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('shop:login')
    
    return render(request, 'shop/signup.html')


def login_view(request):
    """User login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect admin to dashboard, regular users to product list
            if user.is_staff:
                return redirect('shop:admin_dashboard')
            else:
                return redirect('shop:product_list')
        else:
            messages.error(request, 'Invalid username or password!')
            return redirect('shop:login')
    
    return render(request, 'shop/login.html')


def logout_view(request):
    """User logout"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('shop:home')


# Admin Views
@login_required(login_url='shop:login')
def admin_dashboard(request):
    """Admin dashboard"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_contacts = Contact.objects.count()
    unread_contacts = Contact.objects.filter(read=False).count()
    
    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_contacts': total_contacts,
        'unread_contacts': unread_contacts,
    }
    return render(request, 'shop/admin/dashboard.html', context)


@login_required(login_url='shop:login')
def admin_products(request):
    """Manage products"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    products = Product.objects.all().order_by('-created_at')
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
    }
    return render(request, 'shop/admin/products.html', context)


@login_required(login_url='shop:login')
def admin_product_detail(request, id):
    """View/Edit product"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.discount_price = request.POST.get('discount_price') or None
        product.stock = request.POST.get('stock')
        product.available = request.POST.get('available') == 'on'
        product.featured = request.POST.get('featured') == 'on'
        product.material = request.POST.get('material')
        product.save()
        
        messages.success(request, 'Product updated successfully!')
        return redirect('shop:admin_products')
    
    context = {
        'product': product,
    }
    return render(request, 'shop/admin/product_detail.html', context)


@login_required(login_url='shop:login')
def admin_product_delete(request, id):
    """Delete product"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('shop:admin_products')
    
    context = {
        'product': product,
    }
    return render(request, 'shop/admin/product_delete.html', context)


@login_required(login_url='shop:login')
def admin_contacts(request):
    """Manage contact messages"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    contacts = Contact.objects.all().order_by('-created_at')
    paginator = Paginator(contacts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'contacts': page_obj,
    }
    return render(request, 'shop/admin/contacts.html', context)


@login_required(login_url='shop:login')
def admin_orders(request):
    """List all orders for admin"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')

    from .models import Order
    orders = Order.objects.all().order_by('-created_at')
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
    }
    return render(request, 'shop/admin/orders.html', context)


@login_required(login_url='shop:login')
def admin_order_detail(request, id):
    """View single order details"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')

    from .models import Order
    order = get_object_or_404(Order, id=id)

    # compute per-item line totals and order total
    from decimal import Decimal
    items = []
    total = Decimal('0.00')
    for item in order.items.all():
        try:
            line_total = (item.price or Decimal('0.00')) * item.quantity
        except Exception:
            line_total = Decimal('0.00')
        setattr(item, 'line_total', line_total)
        items.append(item)
        try:
            total += line_total
        except Exception:
            pass

    context = {
        'order': order,
        'items': items,
        'total_amount': total,
    }
    return render(request, 'shop/admin/order_detail.html', context)


@login_required(login_url='shop:login')
def admin_contact_detail(request, id):
    """View contact message"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    contact = get_object_or_404(Contact, id=id)
    contact.read = True
    contact.save()
    
    context = {
        'contact': contact,
    }
    return render(request, 'shop/admin/contact_detail.html', context)


@login_required(login_url='shop:login')
def admin_contact_delete(request, id):
    """Delete contact message"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    contact = get_object_or_404(Contact, id=id)
    
    if request.method == 'POST':
        contact.delete()
        messages.success(request, 'Contact message deleted successfully!')
        return redirect('shop:admin_contacts')
    
    context = {
        'contact': contact,
    }
    return render(request, 'shop/admin/contact_delete.html', context)


@login_required(login_url='shop:login')
def admin_product_create(request):
    """Create new product"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            category = get_object_or_404(Category, id=category_id)
            
            product = Product(
                category=category,
                name=request.POST.get('name'),
                product_type=request.POST.get('product_type'),
                style=request.POST.get('style'),
                description=request.POST.get('description'),
                price=request.POST.get('price'),
                discount_price=request.POST.get('discount_price') or None,
                stock=request.POST.get('stock'),
                available=request.POST.get('available') == 'on',
                featured=request.POST.get('featured') == 'on',
                material=request.POST.get('material'),
                care_instructions=request.POST.get('care_instructions'),
            )
            product.save()
            
            # Handle sizes
            from .models import ProductSize, ProductImage
            sizes = request.POST.getlist('sizes')
            for size in sizes:
                if size:
                    ProductSize.objects.create(product=product, size=size, available=True)
            
            # Handle image uploads
            images = request.FILES.getlist('images')
            for image in images:
                if image:
                    ProductImage.objects.create(product=product, image=image)
            
            messages.success(request, 'Product created successfully!')
            return redirect('shop:admin_product_detail', id=product.id)
        except Exception as e:
            messages.error(request, f'Error creating product: {str(e)}')
    
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'product_types': Product.PRODUCT_TYPE_CHOICES,
        'styles': Product.STYLE_CHOICES,
        'sizes': [('XS', 'Extra Small'), ('S', 'Small'), ('M', 'Medium'), ('L', 'Large'), ('XL', 'Extra Large'), ('XXL', 'Double Extra Large')],
    }
    return render(request, 'shop/admin/product_create.html', context)


@login_required(login_url='shop:login')
def admin_contact_reply(request, id):
    """Reply to contact message via email"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    contact = get_object_or_404(Contact, id=id)
    
    if request.method == 'POST':
        try:
            from django.core.mail import send_mail
            
            reply_message = request.POST.get('reply_message')
            subject = f"Re: {contact.get_subject_display()}"
            
            send_mail(
                subject,
                reply_message,
                'noreply@florafashion.com',
                [contact.email],
                fail_silently=False,
            )
            
            messages.success(request, f'Email reply sent to {contact.email}!')
            return redirect('shop:admin_contact_detail', id=contact.id)
        except Exception as e:
            messages.error(request, f'Error sending email: {str(e)}')
    
    contact.read = True
    contact.save()
    
    context = {
        'contact': contact,
    }
    return render(request, 'shop/admin/contact_reply.html', context)


# Category Management Views
@login_required(login_url='shop:login')
def admin_categories(request):
    """Manage categories"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    categories = Category.objects.all().order_by('name')
    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': page_obj,
    }
    return render(request, 'shop/admin/categories.html', context)


@login_required(login_url='shop:login')
def admin_category_create(request):
    """Create new category"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')

    if request.method == 'POST':
        try:
            category = Category(
                name=request.POST.get('name'),
                description=request.POST.get('description'),
            )
            if 'image' in request.FILES:
                category.image = request.FILES['image']
            category.save()

            messages.success(request, 'Category created successfully!')
            return redirect('shop:admin_categories')
        except Exception as e:
            messages.error(request, f'Error creating category: {str(e)}')

    context = {}
    return render(request, 'shop/admin/category_create.html', context)


@login_required(login_url='shop:login')
def admin_category_detail(request, id):
    """View/Edit category"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    category = get_object_or_404(Category, id=id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        if 'image' in request.FILES:
            category.image = request.FILES['image']
        category.save()

        messages.success(request, 'Category updated successfully!')
        return redirect('shop:admin_categories')

    context = {
        'category': category,
    }
    return render(request, 'shop/admin/category_detail.html', context)


@login_required(login_url='shop:login')
def admin_category_delete(request, id):
    """Delete category"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    category = get_object_or_404(Category, id=id)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('shop:admin_categories')
    
    context = {
        'category': category,
    }
    return render(request, 'shop/admin/category_delete.html', context)


@login_required(login_url='shop:login')
def admin_product_add_image(request, id):
    """Add images to product"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        try:
            from .models import ProductImage
            images = request.FILES.getlist('images')
            
            if not images:
                messages.warning(request, 'No images selected.')
            else:
                count = 0
                for image in images:
                    if image:
                        ProductImage.objects.create(product=product, image=image)
                        count += 1
                
                messages.success(request, f'{count} image(s) uploaded successfully!')
        except Exception as e:
            messages.error(request, f'Error uploading images: {str(e)}')
    
    return redirect('shop:admin_product_detail', id=product.id)


@login_required(login_url='shop:login')
def admin_product_delete_image(request, id):
    """Delete product image"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    from .models import ProductImage
    image = get_object_or_404(ProductImage, id=id)
    product_id = image.product.id
    
    if request.method == 'POST':
        try:
            image.delete()
            messages.success(request, 'Image deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting image: {str(e)}')
    
    return redirect('shop:admin_product_detail', id=product_id)


# ===========================
# BLOG VIEWS
# ===========================

@login_required(login_url='shop:login')
def create_blog(request):
    """Allow logged-in users to create blog posts"""
    if request.method == 'POST':
        from .models import Blog
        
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        image = request.FILES.get('image')
        
        # Validate input
        if not title or not description:
            messages.error(request, 'Title and description are required.')
            return redirect('shop:create_blog')
        
        try:
            blog = Blog(
                author=request.user,
                title=title,
                description=description,
                image=image if image else None
            )
            blog.save()
            messages.success(request, 'Blog post created successfully!')
            return redirect('shop:blog_list')
        except Exception as e:
            messages.error(request, f'Error creating blog: {str(e)}')
            return redirect('shop:create_blog')
    
    return render(request, 'shop/blog/create.html')


def blog_list(request):
    """Display blogs from other users (exclude current user's blogs)"""
    from .models import Blog
    
    # Get all blogs
    blogs = Blog.objects.all().order_by('-created_at')
    
    # Exclude current user's blogs if logged in
    if request.user.is_authenticated:
        blogs = blogs.exclude(author=request.user)
    
    # Pagination
    paginator = Paginator(blogs, 9)  # 9 blogs per page
    page_number = request.GET.get('page', 1)
    blogs = paginator.get_page(page_number)
    
    context = {
        'blogs': blogs,
        'total_count': paginator.count,
    }
    
    return render(request, 'shop/blog/list.html', context)


def blog_detail(request, id):
    """Display single blog post details"""
    from .models import Blog
    
    blog = get_object_or_404(Blog, id=id)
    
    context = {
        'blog': blog,
    }
    
    return render(request, 'shop/blog/detail.html', context)


@login_required(login_url='shop:login')
def edit_blog(request, id):
    """Allow users to edit their own blog posts"""
    from .models import Blog
    
    blog = get_object_or_404(Blog, id=id)
    
    # Check if user is the author
    if blog.author != request.user:
        messages.error(request, 'You do not have permission to edit this blog.')
        return redirect('shop:blog_list')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        image = request.FILES.get('image')
        
        if not title or not description:
            messages.error(request, 'Title and description are required.')
            return redirect('shop:edit_blog', id=id)
        
        try:
            blog.title = title
            blog.description = description
            if image:
                blog.image = image
            blog.save()
            messages.success(request, 'Blog post updated successfully!')
            return redirect('shop:blog_detail', id=blog.id)
        except Exception as e:
            messages.error(request, f'Error updating blog: {str(e)}')
            return redirect('shop:edit_blog', id=id)
    
    context = {
        'blog': blog,
        'is_edit': True,
    }
    
    return render(request, 'shop/blog/create.html', context)


@login_required(login_url='shop:login')
def delete_blog(request, id):
    """Allow users to delete their own blog posts"""
    from .models import Blog
    
    blog = get_object_or_404(Blog, id=id)
    
    # Check if user is the author
    if blog.author != request.user:
        messages.error(request, 'You do not have permission to delete this blog.')
        return redirect('shop:blog_list')
    
    if request.method == 'POST':
        try:
            blog.delete()
            messages.success(request, 'Blog post deleted successfully!')
            return redirect('shop:blog_list')
        except Exception as e:
            messages.error(request, f'Error deleting blog: {str(e)}')
    
    return render(request, 'shop/blog/delete_confirm.html', {'blog': blog})


# ===========================
# ADMIN BLOG MANAGEMENT
# ===========================

def admin_blogs(request):
    """Admin view to manage all blogs"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    from .models import Blog
    
    # Get all blogs with pagination
    blogs = Blog.objects.all().order_by('-created_at')
    
    paginator = Paginator(blogs, 10)
    page_number = request.GET.get('page', 1)
    blogs = paginator.get_page(page_number)
    
    context = {
        'blogs': blogs,
        'total_count': paginator.count,
    }
    
    return render(request, 'shop/admin/blogs.html', context)


def admin_blog_detail(request, id):
    """Admin view to see blog details"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    from .models import Blog
    
    blog = get_object_or_404(Blog, id=id)
    
    context = {
        'blog': blog,
    }
    
    return render(request, 'shop/admin/blog_detail.html', context)


def admin_blog_create(request):
    """Admin view to create blogs"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    from .models import Blog
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        author_id = request.POST.get('author')
        image = request.FILES.get('image')
        
        if not title or not description or not author_id:
            messages.error(request, 'Title, description, and author are required.')
            return redirect('shop:admin_blog_create')
        
        try:
            author = User.objects.get(id=author_id)
            blog = Blog(
                author=author,
                title=title,
                description=description,
                image=image if image else None
            )
            blog.save()
            messages.success(request, 'Blog post created successfully!')
            return redirect('shop:admin_blog_detail', id=blog.id)
        except User.DoesNotExist:
            messages.error(request, 'Selected author does not exist.')
            return redirect('shop:admin_blog_create')
        except Exception as e:
            messages.error(request, f'Error creating blog: {str(e)}')
            return redirect('shop:admin_blog_create')
    
    # Get all users for author selection
    users = User.objects.all().order_by('username')
    context = {
        'users': users,
    }
    
    return render(request, 'shop/admin/blog_create.html', context)


def admin_blog_edit(request, id):
    """Admin view to edit any blog"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    from .models import Blog
    
    blog = get_object_or_404(Blog, id=id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        author_id = request.POST.get('author')
        image = request.FILES.get('image')
        
        if not title or not description or not author_id:
            messages.error(request, 'Title, description, and author are required.')
            return redirect('shop:admin_blog_edit', id=id)
        
        try:
            author = User.objects.get(id=author_id)
            blog.title = title
            blog.description = description
            blog.author = author
            if image:
                blog.image = image
            blog.save()
            messages.success(request, 'Blog post updated successfully!')
            return redirect('shop:admin_blog_detail', id=blog.id)
        except User.DoesNotExist:
            messages.error(request, 'Selected author does not exist.')
            return redirect('shop:admin_blog_edit', id=id)
        except Exception as e:
            messages.error(request, f'Error updating blog: {str(e)}')
            return redirect('shop:admin_blog_edit', id=id)
    
    # Get all users for author selection
    users = User.objects.all().order_by('username')
    context = {
        'blog': blog,
        'users': users,
        'is_edit': True,
    }
    
    return render(request, 'shop/admin/blog_create.html', context)


def admin_blog_delete(request, id):
    """Admin view to delete any blog"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    from .models import Blog
    
    blog = get_object_or_404(Blog, id=id)
    
    if request.method == 'POST':
        try:
            blog.delete()
            messages.success(request, 'Blog post deleted successfully!')
            return redirect('shop:admin_blogs')
        except Exception as e:
            messages.error(request, f'Error deleting blog: {str(e)}')
    
    return render(request, 'shop/admin/blog_delete_confirm.html', {'blog': blog})


@login_required(login_url='shop:login')
def admin_offers(request):
    """Manage offers"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    offers = Offer.objects.all().order_by('-created_at')
    paginator = Paginator(offers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'offers': page_obj,
    }
    return render(request, 'shop/admin/offers.html', context)


@login_required(login_url='shop:login')
def admin_offer_create(request):
    """Create new offer"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    if request.method == 'POST':
        try:
            offer = Offer(
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                discount_percentage=request.POST.get('discount_percentage') or None,
                discount_amount=request.POST.get('discount_amount') or None,
                valid_from=request.POST.get('valid_from'),
                valid_until=request.POST.get('valid_until'),
                is_active=request.POST.get('is_active') == 'on',
                priority=request.POST.get('priority') or 0,
            )
            
            # Handle image upload
            if request.FILES.get('image'):
                offer.image = request.FILES.get('image')
            
            offer.save()
            
            messages.success(request, 'Offer created successfully!')
            return redirect('shop:admin_offer_detail', id=offer.id)
        except Exception as e:
            messages.error(request, f'Error creating offer: {str(e)}')
    
    context = {}
    return render(request, 'shop/admin/offer_create.html', context)


@login_required(login_url='shop:login')
def admin_offer_detail(request, id):
    """View/Edit offer"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    offer = get_object_or_404(Offer, id=id)
    
    if request.method == 'POST':
        try:
            offer.title = request.POST.get('title')
            offer.description = request.POST.get('description')
            offer.discount_percentage = request.POST.get('discount_percentage') or None
            offer.discount_amount = request.POST.get('discount_amount') or None
            offer.valid_from = request.POST.get('valid_from')
            offer.valid_until = request.POST.get('valid_until')
            offer.is_active = request.POST.get('is_active') == 'on'
            offer.priority = request.POST.get('priority') or 0
            
            # Handle image upload
            if request.FILES.get('image'):
                offer.image = request.FILES.get('image')
            
            offer.save()
            
            messages.success(request, 'Offer updated successfully!')
            return redirect('shop:admin_offers')
        except Exception as e:
            messages.error(request, f'Error updating offer: {str(e)}')
    
    context = {
        'offer': offer,
    }
    return render(request, 'shop/admin/offer_detail.html', context)


@login_required(login_url='shop:login')
def admin_offer_delete(request, id):
    """Delete offer"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('shop:home')
    
    offer = get_object_or_404(Offer, id=id)
    
    if request.method == 'POST':
        try:
            offer.delete()
            messages.success(request, 'Offer deleted successfully!')
            return redirect('shop:admin_offers')
        except Exception as e:
            messages.error(request, f'Error deleting offer: {str(e)}')
    
    return render(request, 'shop/admin/offer_delete.html', {'offer': offer})
# from django.shortcuts import render, redirect
# from urllib.parse import quote
# import random
# from .models import Product, Order, OrderItem

# def checkout(request):
#     cart = request.session.get('cart', {})

#     if request.method == "POST":
#         first_name = request.POST.get("first_name")
#         phone = request.POST.get("phone")
#         address = request.POST.get("address")

#         # Save order to database
#         order = Order.objects.create(
#             first_name=first_name,
#             last_name=request.POST.get("last_name", ""),
#             email=request.POST.get("email", ""),
#             phone=phone,
#             address=address,
#             city=request.POST.get("city", ""),
#             postal_code=request.POST.get("postal", ""),
#             country=request.POST.get("country", "India"),
#         )

#         # Save order items
#         for product_id, item in cart.items():
#             try:
#                 product = Product.objects.get(id=product_id)
#                 OrderItem.objects.create(
#                     order=order,
#                     product=product,
#                     price=item.get("price", 0),
#                     quantity=item.get("quantity", 1),
#                     size=item.get("size") or "",   # ✅ save size
#                 )
#             except Product.DoesNotExist:
#                 pass

#         order_id = f"FLORA{order.id}"

#         # Build WhatsApp message
#         message = f"🌸 *New Order - Flora*\n\n"
#         message += f"🆔 Order ID: {order_id}\n"
#         message += f"👤 Customer: {first_name}\n"
#         message += f"📞 Phone: {phone}\n"
#         message += f"📍 Address: {address}\n\n"
#         message += "🛍️ *Order Details:*\n"

#         total = 0
#         for item in cart.values():
#             name = item.get("name") or "Product"
#             size = item.get("size") or "Not selected"
#             qty = int(item.get("quantity") or 1)
#             price = float(item.get("price") or 0)
#             subtotal = price * qty
#             total += subtotal

#             message += f"• {name}\n"
#             message += f"   Size: {size}\n"
#             message += f"   Qty: {qty}\n"
#             message += f"   Price: ₹{subtotal:.2f}\n\n"

#         message += f"💰 *Total Amount:* ₹{total:.2f}\n\n"

#         maps_link = f"https://www.google.com/maps/search/?api=1&query={quote(address)}"
#         message += f"📍 Location Map:\n{maps_link}\n\n"

#         upi_link = f"upi://pay?pa=anjanakattungal@oksbi&pn=FloraStore&am={total:.2f}&cu=INR"
#         message += f"💳 Pay here:\n{upi_link}"

#         # Clear cart after order
#         request.session['cart'] = {}
#         request.session.modified = True

#         whatsapp_number = "919074860867"
#         whatsapp_url = f"https://wa.me/{whatsapp_number}?text={quote(message)}"

#         return redirect(whatsapp_url)

#     return render(request, "checkout.html", {"cart": cart})
from django.shortcuts import render, redirect
from urllib.parse import quote
from .models import Product, Order, OrderItem

def get_size_display(size_code):
    """Convert size code to display name"""
    size_map = {
        'XS': 'Extra Small',
        'S': 'Small',
        'M': 'Medium',
        'L': 'Large',
        'XL': 'Extra Large',
        'XXL': 'Double Extra Large',
    }
    return size_map.get(size_code, size_code if size_code else "Not selected")

def checkout(request):
    cart = request.session.get('cart', {})

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name", "")
        email = request.POST.get("email", "")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        city = request.POST.get("city", "")
        postal = request.POST.get("postal", "")
        country = request.POST.get("country", "India")

        # ✅ Save Order to database
        order = Order.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            postal_code=postal,
            country=country,
        )

        # ✅ Save each OrderItem to database
        for product_id, item in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item.get("price", 0),
                    quantity=item.get("quantity", 1),
                    size=item.get("size") or "",
                )
            except Product.DoesNotExist:
                pass

        # ✅ Fetch order items FROM DATABASE with all related data
        order_items = OrderItem.objects.select_related(
            'product', 'product__category'
        ).filter(order=order)

        # ✅ Build WhatsApp message from database
        order_id = f"FLORA{order.id}"

        message = f"🌸 *New Order - Flora*\n\n"
        message += f"🆔 Order ID: {order_id}\n"
        message += f"👤 Customer: {first_name} {last_name}\n"
        message += f"📞 Phone: {phone}\n"
        message += f"📍 Address: {address}, {city}\n\n"
        message += "🛍️ *Order Details:*\n"

        total = 0
        for item in order_items:
            category_name = item.product.category.name if item.product and item.product.category else "N/A"
            product_name  = item.product.name if item.product else "Deleted Product"
            size_code = item.size or ""
            
            # Fetch the display size name
            size_display = get_size_display(size_code) if size_code else None
            
            qty           = item.quantity
            price         = float(item.price)
            subtotal      = price * qty
            total        += subtotal

            message += f"• {product_name}\n"
            message += f"   Category: {category_name}\n"
            if size_display:
                message += f"   Size: {size_display}\n"
            message += f"   Qty: {qty}\n"
            message += f"   Price: ₹{subtotal:.2f}\n\n"

        message += f"💰 *Total Amount:* ₹{total:.2f}\n\n"

        maps_link = f"https://www.google.com/maps/search/?api=1&query={quote(address)}"
        message += f"📍 Location Map:\n{maps_link}\n\n"

        upi_link = f"upi://pay?pa=anjanakattungal@oksbi&pn=FloraStore&am={total:.2f}&cu=INR"
        message += f"💳 Pay here:\n{upi_link}"

        # ✅ Clear cart after order placed
        request.session['cart'] = {}
        request.session.modified = True

        whatsapp_number = "919074860867"
        whatsapp_url = f"https://wa.me/{whatsapp_number}?text={quote(message)}"

        return redirect(whatsapp_url)

    return render(request, "checkout.html", {"cart": cart})


def cart_add(request, product_id):
    product = Product.objects.get(id=product_id)
    cart = request.session.get("cart", {})

    size = request.POST.get("size")
    print("SIZE FROM POST:", repr(size))  # ← add this line

    quantity = int(request.POST.get("quantity", 1))

    cart[str(product_id)] = {
        "name": product.name,
        "price": float(product.get_display_price()),
        "quantity": quantity,
        "size": size,
    }

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart:cart_detail")