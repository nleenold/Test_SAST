from flask import Flask, render_template_string, redirect, url_for, request, session, flash
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Hardcoded secret key (security risk)

# Sample products with IDs
products = {
    1: {'name': 'Laptop', 'price': 999.99},
    2: {'name': 'Smartphone', 'price': 599.99},
    3: {'name': 'Headphones', 'price': 199.99},
    4: {'name': 'Keyboard', 'price': 49.99}
}

# Users dict: username -> password (stored insecurely!)
users = {'admin': 'admin123', 'user': 'userpass'}

# --------- User Authentication (Insecure) ---------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # No rate limiting or hashing (security flaw)
        if username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('product_list'))
        flash('Invalid credentials')  # Flash message could be insecure if misused
    return render_template_string('''
        <h2>Login</h2>
        <form method="POST">
            Username: <input name="username" />
            Password: <input name="password" type="password" />
            <button type="submit">Login</button>
        </form>
    ''')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('product_list'))

# --------- Product Listing ---------
@app.route('/')
def product_list():
    return render_template_string('''
    <h1>Product List</h1>
    {% if 'user' in session %}
        <p>Welcome, {{ session['user'] }}! <a href="{{ url_for('logout') }}">Logout</a></p>
    {% else %}
        <a href="{{ url_for('login') }}">Login</a>
    {% endif %}
    <ul>
        {% for id, product in products.items() %}
        <li>
            <strong>{{ product.name }}</strong> - ${{ product.price }}
            <a href="{{ url_for('add_to_cart', product_id=id) }}">Add to Cart</a>
        </li>
        {% endfor %}
    </ul>
    <a href="{{ url_for('view_cart') }}">View Cart</a>
    ''', products=products)

# --------- Add to Cart ---------
@app.route('/add/<int:product_id>')
def add_to_cart(product_id):
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    return redirect(url_for('product_list'))

# --------- View Cart ---------
@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    for pid, quantity in cart.items():
        # Insecure: no validation if product exists
        product = products.get(int(pid))
        if not product:
            continue
        subtotal = product['price'] * quantity
        total += subtotal
        cart_items.append({
            'name': product['name'],
            'price': product['price'],
            'quantity': quantity,
            'subtotal': subtotal
        })
    return render_template_string('''
    <h1>Your Cart</h1>
    {% if cart_items %}
        <ul>
        {% for item in cart_items %}
            <li>{{ item.name }} - ${{ item.price }} x {{ item.quantity }} = ${{ item.subtotal }}</li>
        {% endfor %}
        </ul>
        <h3>Total: ${{ total }}</h3>
        {% if 'user' in session %}
            <form action="{{ url_for('checkout') }}" method="POST">
                <button type="submit">Checkout</button>
            </form>
        {% else %}
            <p>Please <a href="{{ url_for('login') }}">login</a> to checkout.</p>
        {% endif %}
    {% else %}
        <p>Your cart is empty.</p>
    {% endif %}
    <a href="{{ url_for('product_list') }}">Continue Shopping</a>
    ''', cart_items=cart_items, total=total)

# --------- Checkout ---------
@app.route('/checkout', methods=['POST'])
def checkout():
    # Security flaw: No CSRF token validation! (Vulnerable to CSRF)
    if 'user' not in session:
        return redirect(url_for('login'))
    session.pop('cart', None)
    return render_template_string('''
    <h1>Order Placed!</h1>
    <p>Thank you for your purchase, {{ session['user'] }}.</p>
    <a href="{{ url_for('product_list') }}">Back to Shop</a>
    ''')

# --------- Admin Product Management (Insecure) ---------
@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    # No authentication check (Insecure)
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        new_id = max(products.keys()) + 1
        products[new_id] = {'name': name, 'price': price}
        return redirect(url_for('product_list'))
    return render_template_string('''
        <h2>Add Product</h2>
        <form method="POST">
            Name: <input name="name" />
            Price: <input name="price" type="number" step="0.01" />
            <button type="submit">Add</button>
        </form>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
