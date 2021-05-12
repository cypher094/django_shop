from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import json, datetime

from .models import *
from .utils import cookieCart, cartData, guestOrder
from .forms import OrderForm, CreateUserForm

from django.contrib.auth.decorators import login_required

def registerPage(request):
	form = CreateUserForm()

	if request.method == 'POST':
		form = CreateUserForm(request.POST)
		if form.is_valid():
			form.save()
			user = form.cleaned_data.get('username')
			messages.success(request, 'Account was created for ' + user)

			return redirect('login')

	context = {'form':form}
	return render(request, 'store/register.html', context)


def loginPage(request):
	if request.user.is_authenticated:
		return redirect('store')
	else:
		if request.method == 'POST':
			username = request.POST.get('username')
			password =request.POST.get('password')

			user = authenticate(request, username=username, password=password)

			if user is not None:
				login(request, user)
				return redirect('store')
			else:
				messages.info(request, 'Username OR password is incorrect')

		context = {}
		return render(request, 'store/login.html', context)

@login_required(login_url='login')
def logoutUser(request):
	logout(request)
	return redirect('login')

@login_required(login_url='login')
def store(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/store.html', context)

@login_required(login_url='login')
def cart(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.html', context)

@login_required(login_url='login')
def updateItem(request):
	data = json.loads(request.body)
	print(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

@login_required(login_url='login')
def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)

def detail(request, auction_id):
    print(auction_id)
    auction = get_object_or_404(Product, pk=auction_id)
    # auction.resolve()
    print(auction)
    already_bid = False
    data = cartData(request)
    cartItems = data['cartItems']
    items =  {'cartItems':cartItems}
    # if request.user.is_authenticated:
    #     if auction.author == request.user:
    #         own_auction = True
    #         return render(request, 'auctions/detail.html', {'auction': auction, 'own_auction': own_auction})

    #     user_bid = Bid.objects.filter(bidder=request.user).filter(auction=auction).first()
    #     if user_bid:
    #         already_bid = True
    #         bid_amount = user_bid.amount
    #         return render(request, 'auctions/detail.html', {'auction': auction, 'already_bid': already_bid, 'bid_amount': bid_amount})

    return render(request, 'store/detail.html', {**items, 'auction': auction, 'idi': auction_id })