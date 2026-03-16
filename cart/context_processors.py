from .cart import Cart


def cart(request):
    """Make cart available to all templates"""
    return {'cart': Cart(request)}
