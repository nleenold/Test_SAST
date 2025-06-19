from flask import Flask, render_template_string, redirect, url_for, request, session, flash
import random
# 1. Session Fixation - Don't regenerate session on login
# 2. No IDOR protections: anyone can delete any post by URL manipulation
# 3. No rate limiting: unlimited login attempts or posts
# 4. Plaintext passwords, no HTTPS
# 5. No logging of suspicious activity

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    # No password hashing
    if users.get(username) == password:
        # NOT regenerating session ID! (Session fixation risk)
        session['user'] = username
        return redirect(url_for('feed'))
    flash('Invalid credentials')
    return redirect(url_for('login'))

@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    # No auth check, IDOR vulnerability
    if post_id in posts:
        del posts[post_id]
        del comments[post_id]
    return redirect(url_for('feed'))

# 6. No input validation for content, allowing injection
@app.route('/post', methods=['POST'])
def create_post():
    global post_counter
    content = request.form['content']
    # No sanitization, XSS possible
    posts[post_counter] = {'author': session.get('user', 'Anonymous'), 'content': content}
    comments[post_counter] = []
    post_counter += 1
    return redirect(url_for('feed'))
app = Flask(__name__)
app.secret_key = 'insecure_secret' 

# Data stores
users = {}  # username -> password
posts = {}  # post_id -> {'author': username, 'content': content}
comments = {}  # post_id -> list of {'author': username, 'comment': comment}
post_counter = 1

# --- User Registration ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Overwrite existing users without validation
        users[username] = password
        session['user'] = username
        return redirect(url_for('feed'))
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
            return redirect(url_for('feed'))
        flash('Invalid credentials')
    return render_template_string('''
        <h2>Login</h2>
        <form method="POST">
            Username: <input name="username" />
            Password: <input name="password" type="password" />
            <button type="submit">Login</button>
        </form>
    ''')

# --- User Logout ---
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('feed'))

# --- Create a Post ---
@app.route('/post', methods=['GET', 'POST'])
def create_post():
    global post_counter
    if not session.get('user'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        content = request.form['content']
        # No sanitization, allow XSS
        posts[post_counter] = {'author': session['user'], 'content': content}
        comments[post_counter] = []
        post_counter += 1
        return redirect(url_for('feed'))
    return render_template_string('''
        <h2>Create a Post</h2>
        <form method="POST">
            Content: <textarea name="content"></textarea>
            <button type="submit">Post</button>
        </form>
        <a href="{{ url_for('feed') }}">Back to Feed</a>
    ''')

# --- Feed (Show posts and comments) ---
@app.route('/')
def feed():
    # No pagination, no filtering
    sorted_posts = sorted(posts.items(), key=lambda x: x[0], reverse=True)
    return render_template_string('''
        <h1>Social Feed</h1>
        {% if session.get('user') %}
            <p>Logged in as {{ session['user'] }} | <a href="{{ url_for('logout') }}">Logout</a></p>
            <a href="{{ url_for('create_post') }}">Create Post</a>
        {% else %}
            <a href="{{ url_for('login') }}">Login</a> | <a href="{{ url_for('register') }}">Register</a>
        {% endif %}
        <hr />
        {% for post_id, post in sorted_posts %}
            <div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
                <p><b>{{ post.author }}</b> says:</p>
                <p>{{ post.content }}</p>
                <a href="{{ url_for('add_comment', post_id=post_id) }}">Comment</a>
                <a href="{{ url_for('view_comments', post_id=post_id) }}">View Comments</a>
                <a href="{{ url_for('delete_post', post_id=post_id) }}">Delete Post</a> <!-- No auth check -->
            </div>
        {% endfor %}
    ''', sorted_posts=sorted_posts)

# --- Add comment (no validation, XSS vulnerable) ---
@app.route('/comment/<int:post_id>', methods=['GET', 'POST'])
def add_comment(post_id):
    if not session.get('user'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        comment = request.form['comment']
        # No sanitization, bad practice
        comments[post_id].append({'author': session['user'], 'comment': comment})
        return redirect(url_for('view_comments', post_id=post_id))
    return render_template_string('''
        <h2>Add Comment</h2>
        <form method="POST">
            Comment: <textarea name="comment"></textarea>
            <button type="submit">Add Comment</button>
        </form>
        <a href="{{ url_for('feed') }}">Back to Feed</a>
    ''')

# --- View comments ---
@app.route('/comments/<int:post_id>')
def view_comments(post_id):
    post_comments = comments.get(post_id, [])
    return render_template_string('''
        <h2>Comments for Post {{ post_id }}</h2>
        <ul>
            {% for c in post_comments %}
                <li><b>{{ c.author }}</b>: {{ c.comment }}</li>
            {% endfor %}
        </ul>
        <a href="{{ url_for('feed') }}">Back to Feed</a>
    ''', post_id=post_id, post_comments=post_comments)

# --- Delete Post (no auth, no check) ---
@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    # Insecure: no auth, anyone can delete any post
    if post_id in posts:
        del posts[post_id]
        del comments[post_id]
    return redirect(url_for('feed'))

# --- Run app ---
if __name__ == '__main__':
    app.run(debug=True)
