import csv
import datetime

from django.http import HttpResponse
from django.shortcuts import render, redirect

from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from store.models.customer import Customer
from django.views import View

from store.models.product import Products
from store.models.orders import Order


class CheckOut(View):
    def post(self, request):
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        customer = request.session.get('customer')
        cart = request.session.get('cart')
        products = Products.get_products_by_id(list(cart.keys()))
        print(address, phone, customer, cart, products)

        for product in products:
            print(cart.get(str(product.id)))
            order = Order(customer=Customer(id=customer),
                          product=product,
                          price=product.price,
                          address=address,
                          phone=phone,
                          quantity=cart.get(str(product.id)))
            order.save()
        request.session['cart'] = {}

        return redirect('cart')


#Stripe
import stripe
from django.conf import settings
# This is your test secret API key.
stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

class CreateCheckoutSessionView(View):
    def post(self, request,  *args, **kwargs):
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        customer = request.session.get('customer')
        cart = request.session.get('cart')
        products = Products.get_products_by_id(list(cart.keys()))
        host = self.request.get_host()
        #order_id = request.POST.get('order-id')
        for product in products:
            order = Order(customer=Customer(id=customer),
                          product=product,
                          price=product.price,
                          address=address,
                          phone=phone,
                          quantity=cart.get(str(product.id)))
            #order = Order.objects.get(id=order_id)
            order.save()
        checkout_session = stripe.checkout.Session.create(

            line_items=[
                {
                    'price_data': {
                        'currency': 'eur',
                        'unit_amount': order.price * 100,
                        'product_data':{
                            'name': order.id,
                        },
                    },
                    'quantity': 1,
                },
            ],

            mode='payment',
            success_url=f"http://{host}{reverse('payment-success')}",
            cancel_url=f"http://{host}{reverse('payment-cancel')}",
        )
        request.session['cart'] = {}
        return redirect(checkout_session.url, code=303)


def paymentSuccess(request):
    context = {
        'payment_status': 'success'
    }
    return render(request, 'confirmation.html', context)

def paymentCancel(request):
    context = {
        'payment_status': 'cancel'
    }
    return render(request, 'confirmation.html', context)

@csrf_exempt
def my_webhook_view(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        if session.payment_status == "paid":
            #Fullfill the purchase
            line_item = session.list_line_items(session.id, limit=1).data[0]
            order_id = line_item['description']
            fulfill_order(order_id)

    # Passed signature verification
    return HttpResponse(status=200)

def fulfill_order(order_id):
    order = Order.objects.get(id=order_id)
    order.ordered = True
    order.orderDate = datetime.datetime.now()
    order.save()

    for item in order.items.all():
        product_var = Order.objects.get(id=item.product.id)
        product_var.stock -= item.quantity
        product_var.save()


def export(request):
    response = HttpResponse(content_type='text/csv')

    writer = csv.writer(response)
    writer.writerow(['Name', 'Price', 'Category', 'Description'])

    for product in Products.objects.all().values_list('name', 'price', 'category', 'description'):
        writer.writerow(product)

    response['Content-Disposition'] = 'attachment; filname="vodaproducts.csv"'

    return response