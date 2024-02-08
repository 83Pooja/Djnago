from django.shortcuts import render,HttpResponseRedirect
from django.contrib.auth.models import User
from django.db.models.query_utils import Q
from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.mail import send_mail,send_mass_mail 
from random import randint 
from django.contrib.auth.decorators import login_required
from razorpay.resources import payment 
from django.contrib.sites.shortcuts import get_current_site
from karma.settings import RAZORPAY_API_KEY,RAZORPAY_API_SECRET_KEY
from django.contrib.auth.forms import AuthenticationForm,PasswordChangeForm,SetPasswordForm
from django.contrib.auth import authenticate,login,logout,update_session_auth_hash 

import razorpay
from .models import *
from datetime import datetime
# Create your views here.

def index(request):
    data = Product.objects.all()
    if(request.method=="POST"):
        nl=NewsLetter()
        nl.email=request.POST.get('email')
        subject="Newsletter Subscription Successfully"
        body="""
            Hello!!!
            Thank to subscribe our Newsletter Service
            Now you got an email when a  new product 
            in listed in our website.
            """
        myemail="vikas.gupta.hackers@gmail.com"
        send_mail(subject,body,myemail,[nl.email,],fail_silently=False)
        
        nl.save()
        return HttpResponseRedirect("/")
    return render(request, 'index.html', {'Data': data})
@login_required(login_url='/login/')
def cartPage(request): 
    status=request.session.get("status",None)
    if(status==True):
        request.session['cart']={} 
    cart=request.session.get("cart",None)
    if(request.method=="POST"):
        q=int(request.POST.get('q'))
        if(q>0):
            num=request.POST.get('pid')
            cart[str(num)]=q
            request.session['cart']=cart
    cart=request.session.get("cart",None)
    
    if(cart):
        keys=cart.keys()
        product=[]
        sum=0
        for i in keys:
            p=Product.objects.get(pid=i)
            product.append(p)
            sum=sum+p.finalprice*cart[i]
        if(sum<1000):
            shipping=150
            final=sum+shipping
            
        else:
            shipping=False
            final=sum
    else:
        product=[]
        sum=0
        final=0
        shipping=False
    return render(request, 'cart.html',{"Product":product,
                                        "Total":sum,
                                        "Shipping":shipping,
                                         "Final":final})

def deleteCart(request,num):
    cart=request.session.get("cart",None)
    if(cart):
        cart.pop(str (num))
        request.session["cart"]=cart
    return HttpResponseRedirect('/cart/')


client=razorpay.Client(auth=(RAZORPAY_API_KEY,RAZORPAY_API_SECRET_KEY))
@login_required(login_url='/login/')
def checkOutPage(request):
    buyer=Buyer.objects.get(username=request.user)
    cart=request.session.get("cart",None)
    keys=cart.keys()
    product=[]
    sum=0
    for i in keys:       
        p=Product.objects.get(pid=i)
        product.append(p)
        sum=sum+p.finalprice*cart[i]
    if(sum<1000):
        shipping=150
        final=sum+shipping
    else:
        shipping=False
        final=sum    
    if(request.method=="POST"):
        check=CheckOut()
        check.buyer=buyer
        check.total=0
        check.shipping=0
        check.final=0
        check.active=False
        check.save()
        check=CheckOut.objects.filter(buyer=buyer)
        check=check[::-1]
        check=check[0]
        check.buyer=buyer
        for i in product:
            check.product.add(i.pid)
        check.total=sum
        check.shipping=shipping
        check.final=final
        for i in product:
            check.q=check.q+str(i.pid)+":"+str(cart[str(i.pid)])
        check.mode=request.POST.get("mode")
        if(check.mode=="cod"):        
            check.active=True
            check.save()
            if(request.session.get("status",None)!=None):
                request.session['status']=True
            subject="Your Order is placed Successfully"
            body="""Hello!!!
                    Thank to for Shopping qith us 
                    Team: Karma"""
            #send_mail(subject,body,"vikas.gupta.hackers@gmail.com",[buyer.email,],fail_silently=False)
            return HttpResponseRedirect('/confirmation/')
        else:
            check.active=True
            check.save()
            orderAmount=check.final*100
            orderCurrency="INR"
            paymentOrder=client.order.create(dict(amount=orderAmount,currency=orderCurrency,payment_capture=1))
            print(paymentOrder)
            paymentId=paymentOrder['id'] 
            return render(request, 'pay.html',{
                "amount":orderAmount,
                "api-key":RAZORPAY_API_KEY,
                "order_id":paymentId,
                "User":buyer
            })
             
    return render(request, 'checkout.html',{"User":buyer,"Total":sum,"Shipping":shipping,
                            "Final":final,"Product":product})

@login_required(login_url='/login/')
def productDetails(request,num):
    product=Product.objects.get(pid=num)
    if(request.method=="POST"):
        q=int(request.POST.get('qty'))
        cart=request.session.get('cart',None)
        if(cart):
            cartProducts=cart.keys()
            if(product.pid in cartProducts):
                cart[product.pid]=q
            else:
                cart.setdefault(product.pid,q)
        else:
            cart={product.pid:q}
        try:
            buyer=Buyer.objects.get(username=request.user)    
            wish=WishList.objects.get(buyer=buyer,product=product)
            wish.delete()
        except:
            pass
        request.session["cart"]=cart
        request.session['status']=False
        return HttpResponseRedirect("/cart/")
    return render(request, 'single-product.html',{'Product':product})

@login_required(login_url='/login/')
def paymentSuccess(request,rppid,rpoid,rpsid):
    buyer=Buyer.objects.get(username=request.user)
    check=CheckOut.objects.filter(buyer=buyer)
    check=check[::-1]
    check=check[0]
    check.razorpay_payment_id=rppid
    check.razorpay_order_id=rpoid
    check.razorpay_signature=rpsid
    check.payment_status=1
    check.save()
    if(request.session.get("status",None)!=None):
            request.session['status']=True
            subject="Your Order is placed Successfully"
            body="""Hello!!!
                    Thank to for Shopping qith us 
                    Team: Karma localhost:8000"""
            #send_mail(subject,body,"vikas.gupta.hackers@gmail.com",[buyer.email,],fail_silently=False)
            return HttpResponseRedirect(request, '/confirmation/')
    
#tracking code
@login_required(login_url='/login/')
def tracking(request):
    return render (request,'tracking.html')

@login_required(login_url='/login/')
def paymentFail(request):
    buyer=Buyer.objects.get(username=request.user)
    check=CheckOut.objects.filter(buyer=buyer)
    check=check[::-1]
    check=check[0]
    
    check.payment_status=2
    check.save()
    if(request.session.get("status",None)!=None):
            request.session['status']=True
            subject="Your Payment is Fail"
            body="""Oops Payment is fail!!!
        
                    please try again
                    Team: Karma localhost:8000"""
            #send_mail(subject,body,"vikas.gupta.hackers@gmail.com",[buyer.email,],fail_silently=False)
            return render(request, 'paymentfail.html')

@login_required(login_url='/login/')
def confirmation(request):
    buyer = Buyer.objects.get(username=request.user)
    check = CheckOut.objects.filter(buyer=buyer).order_by('-created_at').first()
    product = [p for p in check.product.all()]
    total = check.total
    shipping = check.shipping
    final = check.final
    order_date = check.created_at
    return render(request, "confirmation.html", {
        "OrderNo": check.cid,
        "Product": product,
        "Total": total,
        "Shipping": shipping,
        "Final": final,
        "Buyer": buyer,
        "OrderDate": order_date,
    })

def contactPage(request):
    if(request.method=="POST"):
       c=ContactUs()
       c.name=request.POST.get("name")
       c.email=request.POST.get("email")
       c.subject=request.POST.get("subject")
       c.message=request.POST.get("message")
       c.save()
       return HttpResponseRedirect("/")
    return render(request, 'contact.html')

def shopPage(request,mc,sc,br):
    mainCat = MainCategory.objects.all()
    subCat = SubCategory.objects.all()
    brand = Brand.objects.all()
    if(mc == 'None' and sc == "None" and br == "None"):
        products = Product.objects.all()
    elif(mc != 'None' and sc == "None" and br == "None"):
        products = Product.objects.filter(mainCat=mc)
    elif(mc == 'None' and sc != "None" and br == "None"):
        products = Product.objects.filter(subCat=sc)
    elif(mc == 'None' and sc == "None" and br != "None"):
        products = Product.objects.filter(brand=br)
    elif(mc != 'None' and sc != "None" and br == "None"):
        products = Product.objects.filter(mainCat=mc,subCat=sc)
    elif(mc != 'None' and sc == "None" and br != "None"):
        products = Product.objects.filter(mainCat=mc,brand=br)
    elif(mc == 'None' and sc != "None" and br != "None"):
        products = Product.objects.filter(subCat=sc,brand=br)
    else:
        products = Product.objects.filter(mainCat=mc,subCat=sc,brand=br)

    #context Data
    return render(request, 'shop.html', {"MainCat": mainCat, "SubCat": subCat, "Brand": brand,
     "MC":mc,"SC":sc,"BR":br,"Product":products})

def loginPage(request):    
    if(request.method == "POST"):
        uname = request.POST.get("username") 
        pword = request.POST.get("password")
        user = auth.authenticate(username=uname, password=pword)
 
        if(user is not None):
            e=auth.login(request, user)
            if(user.is_superuser):
                return HttpResponseRedirect("/admin/")
            else:
                return HttpResponseRedirect("/profile/")
        else:
            messages.error(request, "Username or password wrong")
    return render(request, "login.html")
@login_required(login_url='/login/')
def profile(request):
    # print(request.user,"\n\n")    
    user =User.objects.get(username=request.user)
    # 
    if(user.is_superuser):
        return HttpResponseRedirect('/admin/')
    else:
        try:
            seller=Seller.objects.get(username=request.user)
            return HttpResponseRedirect("/sellerprofile/",)
        except:
            buyer=Buyer.objects.get(username=request.user)
            return HttpResponseRedirect("/buyerprofile/")
@login_required(login_url='/login/')
def sellerProfile(request):
    seller=Seller.objects.get(username=request.user)
    product=Product.objects.filter(seller=seller)    
    return render(request,"sellerprofile.html",{"User":seller,"Product":product})

@login_required(login_url='/login/')
def buyerProfile(request):
    buyer=Buyer.objects.get(username=request.user)
    product=WishList.objects.filter(buyer=buyer)
    return render(request,'buyerprofile.html',{"User":buyer,
                                                "Product":product
                                                })
#registrations
def signup(request):
    print("He")
    if(request.method == "POST"):
        actype = request.POST.get("accountType")
        print(actype)
        if(actype == "seller"):
            s = Seller()
            s.name = request.POST.get("name")
            uname=s.username = request.POST.get("username")
            s.email = request.POST.get("email")
            s.phone = request.POST.get("mobile")
            password = request.POST.get("password")
            user = User.objects.create_user(
                username=uname, password=password)
            user.save()   
            s.save()
            print(s)
            return HttpResponseRedirect("/profile/")
        else:
            b=Buyer()
            b.name = request.POST.get("name")
            uname=b.username = request.POST.get("username")
            b.email = request.POST.get("email")
            b.phone = request.POST.get("mobile")
            password = request.POST.get("password")
            user = User.objects.create_user(
                username=uname, password=password)
            user.save()   
            b.save()
            print(b)
            return HttpResponseRedirect("/profile/")
    return render(request, "signup.html")

def addProduct(request):
  if(request.method=="POST"):
    p=Product()
    p.name=request.POST.get("productname")
    p.baseprice=int(request.POST.get("baseprice"))
    p.discount=int(request.POST.get("discount"))
    p.finalprice=p.baseprice-p.baseprice*p.discount/100
    p.mainCat=MainCategory.objects.get(name=request.POST.get("mc"))
    p.subCat=SubCategory.objects.get(name=request.POST.get("sc"))
    p.brand=Brand.objects.get(name=request.POST.get("brand"))
    p.seller=Seller.objects.get(username=request.user)
    p.stock=bool(request.POST.get("stock"))
    p.desc=request.POST.get("description")
    p.specification=request.POST.get("specification")
    p.color=request.POST.get("color")
    p.number=request.POST.get("size")
    p.pic1=request.FILES.get("pic1")
    p.pic2=request.FILES.get("pic2")
    p.pic3=request.FILES.get("pic3")
    p.pic4=request.FILES.get("pic4")
    p.pic5=request.FILES.get("pic5")
    p.save()
    return HttpResponseRedirect("/profile/")
  mc=MainCategory.objects.all()
  sc=SubCategory.objects.all()
  brand=Brand.objects.all()

  return render(request,'addproduct.html',{"MC":mc,
                                            "SC":sc,
                                            "Brand":brand}) 
@login_required(login_url='/login/')                                    
def editProduct(request,num):
  p=Product.objects.get(pid=num)
  if(request.method=="POST"):
    p=Product()
    p.name=request.POST.get("productname")
    p.baseprice=int(request.POST.get("baseprice"))
    p.discount=int(request.POST.get("discount"))
    p.finalprice=p.baseprice-p.baseprice*p.discount/100
    p.mainCat=MainCategory.objects.get(name=request.POST.get("mc"))
    p.subCat=SubCategory.objects.get(name=request.POST.get("sc"))
    p.brand=Brand.objects.get(name=request.POST.get("brand"))
    p.seller=Seller.objects.get(username=request.user)
    p.stock=bool(request.POST.get("stock"))
    p.desc=request.POST.get("descripton")
    p.specification=request.POST.get("specification")
    p.color=request.POST.get("color")
    p.number=request.POST.get("size")
    if(not request.FILES.get("pic1")==None):
        p.pic1=request.FILES.get("pic1")
    if(not request.FILES.get("pic2")==None):
        p.pic2=request.FILES.get("pic2")
    if(not request.FILES.get("pic3")==None):
        p.pic3=request.FILES.get("pic3")
    if(not request.FILES.get("pic4")==None):
        p.pic4=request.FILES.get("pic4")
    if(not request.FILES.get("pic5")==None):
        p.pic5=request.FILES.get("pic5")
    p.save()
  mc=MainCategory.objects.all()
  sc=SubCategory.objects.all()
  brand=Brand.objects.all()
  return render(request,'editproduct.html',{"Product":p,"MC":mc,
                                            "SC":sc,
                                            "Brand":brand})
@login_required(login_url='/login/')
def deleteProduct(request,num):  
    product=Product.objects.get(pid=num)
    seller=Seller.objects.get(username=request.user)
    if(product.seller==seller):
        product.delete()
        return HttpResponseRedirect("/sellerprofile/")
    return HttpResponseRedirect("/")



@login_required(login_url='/login/')
def editSellerProfile(request):
    s=Seller.objects.get(username=request.user)
    if(request.method=="POST"):
        s.name=request.POST.get("name")
        s.email=request.POST.get("name")
        s.phone=request.POST.get("name")
        if(not request.FIlES.get("pic")==None):
            s.pic=request.POST.get("pic")
        
        s.save()
        return HttpResponseRedirect("/profile/")
    return render(request,'editsellerprofile.html',{"User":s})

@login_required(login_url='/login/')
def editBuyerProfile(request):
    
    b=Buyer.objects.get(username=request.user)
    
    if(request.method=="POST"):
        b.name=request.POST.get("name")
        b.email=request.POST.get("email")
        b.phone=request.POST.get("phone")
        if(not request.FILES.get("pic")):
            b.pic=request.POST.get("pic")
        b.address1=request.POST.get("add1")
        b.address2=request.POST.get("add2")
        b.pin=request.POST.get("pin")
        b.city=request.POST.get("city")
        b.state=request.POST.get("state")
        b.save()
        return HttpResponseRedirect("/profile/")
    return render(request,'editbuyerprofile.html',{"User":b})

#wishlist
@login_required(login_url='/login/')
def wishlistPage(request,num):
    product=Product.objects.get(pid=num)
    buyer=Buyer.objects.get(username=request.user)
    w=WishList()
    w.product=product
    w.buyer=buyer
    
    w.save()    
    return HttpResponseRedirect("/buyerprofile/")

@login_required(login_url='/login/')
def deletewishlist(request,num):  
    wishlist=WishList.objects.get(wid=num)
    buyer=Buyer.objects.get(username=request.user)
    
    if(wishlist.buyer==buyer):
        wishlist.delete()
        # Product.delete()
        return HttpResponseRedirect("/buyerprofile/")
    # return HttpResponseRedirect("/")
@login_required(login_url='/login/')
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/")


#forgot Password Code
def changepass(request):
      
 # if user has already login 
 if(request.user.is_authenticated):     
   if(request.method=="POST"):
      changepwd=SetPasswordForm(user=request.user,data=request.POST)
      if(changepwd.is_valid()):
            changepwd.save() 
            update_session_auth_hash(request,changepwd.user)
            messages.success(request,"Password has been changed successfully!!!!")
            return HttpResponseRedirect('/login/')
   else:   
        changepwd=SetPasswordForm(user=request.user)
   return render(request,'changepass.html',{"Change":changepwd})
 else:
       # if user not login 
      return HttpResponseRedirect('/login/')


def forgetPassword(request):
    return render(request,'index.html')
def enterOtp(request):
    return render(request,'index.html')
def resetPassword(request):
    return render(request,'index.html')