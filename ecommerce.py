from flask import Flask, render_template_string, redirect, url_for, request, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Sample product data
products = {
    1: {'name': 'Laptop', 'price': 999.99},
    2: {'name': 'Smartphone', 'price': 599.99},
    3: {'name': 'Headphones', 'price': 199.99},
    4: {'name': 'Keyboard', 'price': 49.99}
}

# Home page - product listing
@app.route('/')
def product_list():
    return render_template_string('''
    <h1>Product List</h1>
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

# Add product to cart
@app.route('/add/<int:product_id>')
def add_to_cart(product_id):
    cart = session.get('cart', {})
    cart[product_id] = cart.get(product_id, 0) + 1
    session['cart'] = cart
    return redirect(url_for('product_list'))

# View cart
@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    for pid, quantity in cart.items():
        product = products[pid]
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
        <form action="{{ url_for('checkout') }}" method="post">
            <button type="submit">Checkout</button>
        </form>
    {% else %}
        <p>Your cart is empty.</p>
    {% endif %}
    <a href="{{ url_for('product_list') }}">Continue Shopping</a>
    ''', cart_items=cart_items, total=total)

# Checkout
@app.route('/checkout', methods=['POST'])
def checkout():
    session.pop('cart', None)
    return render_template_string('''
    <h1>Order Placed!</h1>
    <p>Thank you for your purchase.</p>
    <a href="{{ url_for('product_list') }}">Back to Shop</a>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
