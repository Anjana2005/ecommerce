from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from shop.models import Product
from .cart import Cart
from django.contrib import messages
from shop.models import Order, OrderItem


@require_POST
def cart_add(request, product_id):
    """Add product to cart"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity, override_quantity=False)
    messages.success(request, f'{product.name} added to cart!')
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    """Remove product from cart"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, f'{product.name} removed from cart!')
    return redirect('cart:cart_detail')


def cart_detail(request):
    """Display cart contents"""
    cart = Cart(request)
    
    # Calculate subtotal and recommended shipping
    for item in cart:
        item['update_quantity_form'] = {
            'quantity': item['quantity'],
            'override': True
        }
    
    context = {
        'cart': cart,
    }
    return render(request, 'cart/detail.html', context)


@require_POST
def cart_update(request, product_id):
    """Update product quantity in cart"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart.add(product=product, quantity=quantity, override_quantity=True)
        messages.success(request, 'Cart updated!')
    else:
        cart.remove(product)
        messages.success(request, f'{product.name} removed from cart!')
    
    return redirect('cart:cart_detail')


def checkout(request):
    """Checkout page"""
    cart = Cart(request)
    
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty!')
        return redirect('shop:product_list')
    
    if request.method == 'POST':
        # Create Order and OrderItems from cart
        try:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            city = request.POST.get('city')
            postal = request.POST.get('postal')
            country = request.POST.get('country')
            payment = request.POST.get('payment')

            order = Order.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                postal_code=postal,
                country=country,
                paid=(payment != 'cod')
            )

            # Create order items
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item.get('product'),
                    price=item.get('price'),
                    quantity=item.get('quantity')
                )

            messages.success(request, 'Order placed successfully!')
            cart.clear()
            return redirect('shop:home')
        except Exception as e:
            messages.error(request, f'Error placing order: {str(e)}')
    
    context = {
        'cart': cart,
    }
    return render(request, 'cart/checkout.html', context)