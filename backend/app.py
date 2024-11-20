from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from database import init_db, add_post, get_posts, get_paginated_posts, update_post, delete_post, add_subscriber
import os
from werkzeug.utils import secure_filename
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Custom template filters
@app.template_filter('datetime')
def format_datetime(value):
    date = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    return date.strftime('%B %d, %Y')

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    featured_posts = get_featured_posts()
    return render_template('index.html', featured_posts=featured_posts)

@app.route('/blog')
def blog():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    limit = 9  # Posts per page
    offset = (page - 1) * limit
    
    # Get posts with search and category filters
    posts = get_filtered_posts(search, category, limit, offset)
    total_posts = get_total_posts(search, category)
    
    total_pages = (total_posts + limit - 1) // limit
    return render_template('blog.html', 
                         posts=posts,
                         page=page,
                         total_pages=total_pages,
                         search=search,
                         category=category)

@app.route('/blog/post/<int:post_id>')
def view_post(post_id):
    post = get_post(post_id)
    if not post:
        abort(404)
    related_posts = get_related_posts(post_id, post[6])  # Assuming post[6] is category
    return render_template('post.html', post=post, related_posts=related_posts)

@app.route('/add-post', methods=['GET', 'POST'])
@login_required
@admin_required
def add_post_page():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        image = request.files.get('image')
        
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return redirect(request.url)
        
        image_url = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
            image_url = f'/static/uploads/{filename}'
        
        try:
            add_post(title, content, image_url, category, session['username'])
            flash('Post created successfully!', 'success')
            return redirect(url_for('blog'))
        except Exception as e:
            flash(f'Error creating post: {str(e)}', 'danger')
            return redirect(request.url)
            
    return render_template('add_post.html')

@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_post(post_id):
    post = get_post(post_id)
    if not post:
        abort(404)
        
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        image = request.files.get('image')
        
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return redirect(request.url)
        
        image_url = post[3]  # Keep existing image
        if image and allowed_file(image.filename):
            # Delete old image if it exists
            if image_url:
                old_image_path = os.path.join(app.static_folder, image_url.lstrip('/static/'))
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
            image_url = f'/static/uploads/{filename}'
        
        try:
            update_post(post_id, title, content, image_url, category)
            flash('Post updated successfully!', 'success')
            return redirect(url_for('view_post', post_id=post_id))
        except Exception as e:
            flash(f'Error updating post: {str(e)}', 'danger')
            return redirect(request.url)
            
    return render_template('edit_post.html', post=post)

@app.route('/delete-post/<int:post_id>', methods=['POST'])
@login_required
@admin_required
def delete_post_route(post_id):
    post = get_post(post_id)
    if not post:
        abort(404)
    
    # Delete associated image if it exists
    if post[3]:
        image_path = os.path.join(app.static_folder, post[3].lstrip('/static/'))
        if os.path.exists(image_path):
            os.remove(image_path)
    
    try:
        delete_post(post_id)
        flash('Post deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting post: {str(e)}', 'danger')
    
    return redirect(url_for('blog'))

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    if not email:
        flash('Please enter an email address.', 'danger')
        return redirect(request.referrer or url_for('home'))
    
    try:
        add_subscriber(email)
        flash('Thank you for subscribing to our newsletter!', 'success')
    except sqlite3.IntegrityError:
        flash('You are already subscribed!', 'info')
    except Exception as e:
        flash(f'Error subscribing: {str(e)}', 'danger')
    
    return redirect(request.referrer or url_for('home'))

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_featured_posts():
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    try:
        c.execute('''
            SELECT id, title, content, created_at, author, category 
            FROM posts 
            ORDER BY created_at DESC 
            LIMIT 3
        ''')
        posts = c.fetchall()
        return posts
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def get_filtered_posts(search, category, limit, offset):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    query = '''
        SELECT id, title, content, image_url, created_at, author, category 
        FROM posts 
        WHERE 1=1
    '''
    params = []
    
    if search:
        query += ' AND (title LIKE ? OR content LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    c.execute(query, params)
    posts = c.fetchall()
    conn.close()
    return posts

def get_total_posts(search, category):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    query = 'SELECT COUNT(*) FROM posts WHERE 1=1'
    params = []
    
    if search:
        query += ' AND (title LIKE ? OR content LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    c.execute(query, params)
    count = c.fetchone()[0]
    conn.close()
    return count

def get_post(post_id):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, title, content, image_url, created_at, author, category 
        FROM posts 
        WHERE id = ?
    ''', (post_id,))
    post = c.fetchone()
    conn.close()
    return post

def get_related_posts(post_id, category):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, title, content, image_url, created_at, author, category 
        FROM posts 
        WHERE category = ? AND id != ? 
        ORDER BY created_at DESC 
        LIMIT 3
    ''', (category, post_id))
    posts = c.fetchall()
    conn.close()
    return posts

if __name__ == '__main__':
    app.run(debug=True)
