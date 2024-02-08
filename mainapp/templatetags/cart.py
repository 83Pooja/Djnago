from django import template
from mainapp.models import Product
register =template.Library()
#Cart Quantity
@register.filter(name="cartQuantity")
def cartQuantity(request,pid):
    cart=request.session.get('cart',None)
    if(cart):
        for key,value in cart.items():
            if(str(pid)==key):
                return value
    
    return 0
#Cart Total
@register.filter(name="cartTotal")
def cartTotal(request,pid):
    cart=request.session.get('cart',None)
    p=Product.objects.get(pid=pid)
    if(cart):
        for key,value in cart.items():
            if(str(pid)==key):
                return value*p.finalprice
    
    return 0