from flask import Flask, render_template_string, redirect, url_for, request, session, flash
import random

app = Flask(__name__)
app.secret_key = 'insecure_secret'

# Data stores
products = {
    1: {'name': 'Laptop', 'price': 999.99},
    2: {'name': 'Smartphone', 'price': 599.99},
    3: {'name': 'Headphones', 'price': 199.99},
    4: {'name': 'Keyboard', 'price': 49.99}
}
users = {}  # username -> password
orders = []

# --- User Registration ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Non-validated duplicate registration overwrites existing user
        users[username] = password
        session['user'] = username
        return redirect(url_for('product_list'))
    return render_template_string('''
        <h2>Register</h2>
        <form method="POST">
            Username: <input name="username" />
            Password: <input name="password" type="password" />
            <button type="submit">Register</button>
        </form>
    ''')

# --- User Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.get(username) == password:
            session['user'] = username
            return redirect(url_for('product_list'))
        flash('Invalid credentials')
    return render_template_string('''
        <h2>Login</h2>
        <form method="POST">
            Username: <input name="username" />
            Password: <input name="password" type="password" />
            <button type="submit">Login</button>
        </form>
    ''')

# --- Product List ---
@app.route('/')
def product_list():
    return render_template_string('''
        <h1>Product Catalog</h1>
        {% if session.get('user') %}
            <p>Welcome, {{ session['user'] }}! <a href="{{ url_for('logout') }}">Logout</a></p>
        {% else %}
            <a href="{{ url_for('login') }}">Login</a> | <a href="{{ url_for('register') }}">Register</a>
        {% endif %}
        <ul>
            {% for pid, product in products.items() %}
                <li>
                    <b>{{ product.name }}</b> - ${{ product.price }}
                    <a href="{{ url_for('add_to_cart', product_id=pid) }}">Add to Cart</a>
                </li>
            {% endfor %}
        </ul>
        <a href="{{ url_for('view_cart') }}">View Cart</a>
        {% if session.get('user') == 'admin' %}
            <br><a href="{{ url_for('admin_add_product') }}">Add Product (Admin)</a>
        {% endif %}
    ''', products=products)

# --- Add to Cart ---
@app.route('/add/<int:product_id>')
def add_to_cart(product_id):
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    return redirect(url_for('product_list'))

# --- View Cart ---
@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    for pid, qty in cart.items():
        product = products.get(int(pid))
        if not product:
            # Bug: silently skipping invalid product IDs
            continue
        subtotal = product['price'] * qty
        total += subtotal
        cart_items.append({
            'name': product['name'],
            'price': product['price'],
            'quantity': qty,
            'subtotal': subtotal
        })
    return render_template_string('''
        <h1>Your Shopping Cart</h1>
        {% if cart_items %}
            <ul>
                {% for item in cart_items %}
                    <li>{{ item.name }} - ${{ item.price }} x {{ item.quantity }} = ${{ item.subtotal }}</li>
                {% endfor %}
            </ul>
            <h3>Total: ${{ total }}</h3>
            {% if session.get('user') %}
                <form method="POST" action="{{ url_for('checkout') }}">
                    <button type="submit">Checkout</button>
                </form>
            {% else %}
                <p>Please <a href="{{ url_for('login') }}">log in</a> to checkout.</p>
            {% endif %}
        {% else %}
            <p>Your cart is empty.</p>
        {% endif %}
        <a href="{{ url_for('product_list') }}">Back to Products</a>
    ''', cart_items=cart_items, total=total)

# --- Checkout ---
@app.route('/checkout', methods=['POST'])
def checkout():
    if not session.get('user'):
        return redirect(url_for('login'))
    # Bug: No validation, no confirmation, no stock check
    # Order data stored without validation, potential for inconsistent data
    order_id = random.randint(10000, 99999)
    order = {
        'order_id': order_id,
        'user': session['user'],
        'items': session.get('cart', {})
    }
    orders.append(order)
    session.pop('cart', None)
    return render_template_string('''
        <h2>Order Confirmation</h2>
        <p>Thank you, {{ session['user'] }}! Your order ID is {{ order_id }}.</p>
        <p>Order contains: {{ order.items }}</p>
        <a href="{{ url_for('product_list') }}">Back to Shop</a>
    ''', order_id=order['order_id'], order=order)

# --- Admin Add Product (No validation, insecure) ---
@app.route('/admin/add_product', methods=['GET', 'POST'])
def admin_add_product():
    # No auth check
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        new_id = max(products.keys()) + 1
        products[new_id] = {'name': name, 'price': price}
        return redirect(url_for('product_list'))
    return render_template_string('''
        <h2>Add Product (Admin)</h2>
        <form method="POST">
            Name: <input name="name" />
            Price: <input name="price" type="number" step="0.01" />
            <button type="submit">Add</button>
        </form>
    ''')

# --- Show Order Details (possible infinite loop bug) ---
@app.route('/order/<int:order_id>')
def show_order(order_id):
    order = next((o for o in orders if o['order_id'] == order_id), None)
    if not order:
        return "Order not found", 404
    # Bug: Infinite loop if order references itself (not in current code but potential future bug)
    # For demonstration, we simulate a bug with recursive call (not implemented here for simplicity)
    items_html = ""
    for pid, qty in order['items'].items():
        product = products.get(int(pid))
        if product:
            items_html += f"<li>{product['name']} x {qty}</li>"
    return render_template_string('''
        <h2>Order #{{ order['order_id'] }}</h2>
        <ul>
            ''' + items_html + '''
        </ul>
    ''', order=order)

# --- Utility functions for bugs ---
def simulate_infinite_loop():
    # Placeholder to demonstrate potential infinite loop bug
    pass

if __name__ == '__main__':
    app.run(debug=True)
