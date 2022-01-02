from django.contrib import admin
from django.urls import path, include
from django.urls import path
from .views.home import Index , store
from .views.signup import Signup
from .views.login import Login , logout
from .views.cart import Cart
from .views.checkout import CheckOut, CreateCheckoutSessionView, paymentSuccess, paymentCancel, my_webhook_view, export
from .views.orders import OrderView
from .middlewares.auth import  auth_middleware


urlpatterns = [
    path('', Index.as_view(), name='homepage'),
    path('store', store , name='store'),
    path('signup', Signup.as_view(), name='signup'),
    path('login', Login.as_view(), name='login'),
    path('logout', logout , name='logout'),
    path('cart', auth_middleware(Cart.as_view()) , name='cart'),
    path('check-out', CheckOut.as_view() , name='checkout'),
    path('orders', auth_middleware(OrderView.as_view()), name='orders'),
    path('create-checkout-session', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('payment-success/', paymentSuccess, name='payment-success'),
    path('payment-cancel/', paymentCancel, name='payment-cancel'),
    path('webhook/stripe', my_webhook_view, name='webhook-stripe'),
    path('export', export, name='export')
]
