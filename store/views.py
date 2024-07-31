from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Sale, InventoryItem, Product, CartItem
from .forms import SaleForm, InventoryItemForm, UserRegistrationForm, UserLoginForm
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from django.db.models import Sum

def home(request):
    products = Product.objects.all()[:20]
    return render(request, 'store/home.html', {'products': products})

@login_required
def inventory_list(request):
    inventory = InventoryItem.objects.all()
    return render(request, 'store/inventory_list.html', {'inventory': inventory})

@login_required
def add_inventory(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory_list')
    else:
        form = InventoryItemForm()
    return render(request, 'store/add_inventory.html', {'form': form})

@login_required
def sales_analysis(request):
    sales_data = Sale.objects.values('product__name').annotate(total_quantity=Sum('quantity'), total_sales=Sum('total_price'))
    return render(request, 'store/sales_analysis.html', {'sales_data': sales_data})

@login_required
def record_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sales_analysis')
    else:
        form = SaleForm()
    return render(request, 'store/record_sale.html', {'form': form})

@login_required
def stock_prediction(request):
    sales = Sale.objects.all().values('product__name', 'quantity', 'date')
    df = pd.DataFrame(list(sales))
    
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    
    df['month'] = df.index.month
    df['year'] = df.index.year
    X = df[['month', 'year']]
    y = df['quantity']
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = LinearRegression()
    model.fit(X_scaled, y)
    
    next_month = pd.DataFrame({'month': [df['month'].max() + 1], 'year': [df['year'].max()]})
    next_month_scaled = scaler.transform(next_month)
    prediction = model.predict(next_month_scaled)
    
    return render(request, 'store/stock_prediction.html', {'prediction': prediction[0]})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'store/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'store/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    return render(request, 'store/cart.html', {'cart_items': cart_items})

@login_required
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')

@login_required
def checkout(request):
    if request.method == 'POST':
        CartItem.objects.filter(user=request.user).delete()
        return redirect('home')
    return render(request, 'store/checkout.html')
