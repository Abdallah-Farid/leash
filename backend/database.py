import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    # Users table with extended profile fields
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            bio TEXT,
            location TEXT,
            website TEXT,
            avatar_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Posts table with additional fields
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'published',
            views INTEGER DEFAULT 0,
            FOREIGN KEY (author) REFERENCES users(username)
        )
    ''')
    
    # Comments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Subscribers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Tags table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Post-Tags relationship table
    c.execute('''
        CREATE TABLE IF NOT EXISTS post_tags (
            post_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (post_id, tag_id),
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
    ''')
    
    # Pets table
    c.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            breed TEXT,
            age REAL,
            bio TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
    ''')
    
    # User Activities table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            target_id INTEGER,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_post(title, content, image_url, category, author):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        INSERT INTO posts (title, content, image_url, created_at, updated_at, author, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, content, image_url, now, now, author, category))
    post_id = c.lastrowid
    conn.commit()
    conn.close()
    return post_id

def update_post(post_id, title, content, image_url, category):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        UPDATE posts 
        SET title = ?, content = ?, image_url = ?, updated_at = ?, category = ?
        WHERE id = ?
    ''', (title, content, image_url, now, category, post_id))
    conn.commit()
    conn.close()

def delete_post(post_id):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()

def get_post(post_id):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('''
        SELECT p.*, u.email 
        FROM posts p 
        JOIN users u ON p.author = u.username 
        WHERE p.id = ?
    ''', (post_id,))
    post = c.fetchone()
    
    if post:
        # Increment view count
        c.execute('UPDATE posts SET views = views + 1 WHERE id = ?', (post_id,))
        conn.commit()
    
    conn.close()
    return post

def get_posts(limit=None):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    query = '''
        SELECT p.*, u.email 
        FROM posts p 
        JOIN users u ON p.author = u.username 
        WHERE p.status = 'published' 
        ORDER BY p.created_at DESC
    '''
    
    if limit:
        query += ' LIMIT ?'
        c.execute(query, (limit,))
    else:
        c.execute(query)
    
    posts = c.fetchall()
    conn.close()
    return posts

def get_paginated_posts(limit, offset):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('''
        SELECT p.*, u.email 
        FROM posts p 
        JOIN users u ON p.author = u.username 
        WHERE p.status = 'published' 
        ORDER BY p.created_at DESC 
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    posts = c.fetchall()
    conn.close()
    return posts

def add_subscriber(email):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT INTO subscribers (email, subscribed_at) VALUES (?, ?)', (email, now))
    conn.commit()
    conn.close()

def add_comment(post_id, user_id, content):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        INSERT INTO comments (post_id, user_id, content, created_at)
        VALUES (?, ?, ?, ?)
    ''', (post_id, user_id, content, now))
    conn.commit()
    conn.close()

def get_post_comments(post_id):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('''
        SELECT c.*, u.username 
        FROM comments c 
        JOIN users u ON c.user_id = u.id 
        WHERE c.post_id = ? 
        ORDER BY c.created_at DESC
    ''', (post_id,))
    comments = c.fetchall()
    conn.close()
    return comments

def add_tag(name):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()

def add_post_tag(post_id, tag_name):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    # First, ensure tag exists
    c.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag_name,))
    
    # Get tag ID
    c.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
    tag_id = c.fetchone()[0]
    
    # Add relationship
    c.execute('INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)', (post_id, tag_id))
    
    conn.commit()
    conn.close()

def get_post_tags(post_id):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('''
        SELECT t.name 
        FROM tags t 
        JOIN post_tags pt ON t.id = pt.tag_id 
        WHERE pt.post_id = ?
    ''', (post_id,))
    tags = [row[0] for row in c.fetchall()]
    conn.close()
    return tags

def update_user_profile(user_id, bio=None, location=None, website=None, avatar_url=None):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    updates = []
    values = []
    
    if bio is not None:
        updates.append('bio = ?')
        values.append(bio)
    if location is not None:
        updates.append('location = ?')
        values.append(location)
    if website is not None:
        updates.append('website = ?')
        values.append(website)
    if avatar_url is not None:
        updates.append('avatar_url = ?')
        values.append(avatar_url)
    
    if updates:
        values.append(user_id)
        query = f'UPDATE users SET {", ".join(updates)} WHERE id = ?'
        c.execute(query, values)
        conn.commit()
    
    conn.close()

def get_user_profile(username):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, username, email, bio, location, website, avatar_url, created_at, last_login
        FROM users
        WHERE username = ?
    ''', (username,))
    profile = c.fetchone()
    conn.close()
    return profile

def get_user_stats(user_id):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    # Get number of pets
    c.execute('SELECT COUNT(*) FROM pets WHERE owner_id = ?', (user_id,))
    pets_count = c.fetchone()[0]
    
    # Get number of posts
    c.execute('SELECT COUNT(*) FROM posts WHERE author = ?', (user_id,))
    posts_count = c.fetchone()[0]
    
    # Get number of comments
    c.execute('SELECT COUNT(*) FROM comments WHERE user_id = ?', (user_id,))
    comments_count = c.fetchone()[0]
    
    # Get number of likes received
    c.execute('''
        SELECT COUNT(*) FROM user_activities 
        WHERE activity_type = 'like' AND target_id IN (
            SELECT id FROM posts WHERE author = ?
        )
    ''', (user_id,))
    likes_count = c.fetchone()[0]
    
    conn.close()
    
    return {
        'pets': pets_count,
        'posts': posts_count,
        'comments': comments_count,
        'likes': likes_count
    }

def add_pet(owner_id, name, type, breed=None, age=None, bio=None, image_url=None):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    c.execute('''
        INSERT INTO pets (owner_id, name, type, breed, age, bio, image_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (owner_id, name, type, breed, age, bio, image_url, now))
    
    pet_id = c.lastrowid
    conn.commit()
    conn.close()
    return pet_id

def get_user_pets(user_id):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, name, type, breed, age, bio, image_url, created_at
        FROM pets
        WHERE owner_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    pets = c.fetchall()
    conn.close()
    return pets

def update_pet(pet_id, name=None, type=None, breed=None, age=None, bio=None, image_url=None):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    updates = []
    values = []
    
    if name is not None:
        updates.append('name = ?')
        values.append(name)
    if type is not None:
        updates.append('type = ?')
        values.append(type)
    if breed is not None:
        updates.append('breed = ?')
        values.append(breed)
    if age is not None:
        updates.append('age = ?')
        values.append(age)
    if bio is not None:
        updates.append('bio = ?')
        values.append(bio)
    if image_url is not None:
        updates.append('image_url = ?')
        values.append(image_url)
    
    if updates:
        values.append(pet_id)
        query = f'UPDATE pets SET {", ".join(updates)} WHERE id = ?'
        c.execute(query, values)
        conn.commit()
    
    conn.close()

def delete_pet(pet_id):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('DELETE FROM pets WHERE id = ?', (pet_id,))
    conn.commit()
    conn.close()

def get_user_activities(user_id, limit=10):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('''
        SELECT a.id, a.activity_type, a.target_id, a.content, a.created_at,
               CASE 
                   WHEN a.activity_type = 'post' THEN p.title
                   WHEN a.activity_type IN ('comment', 'like') THEN (
                       SELECT title FROM posts WHERE id = a.target_id
                   )
               END as post_title
        FROM user_activities a
        LEFT JOIN posts p ON a.target_id = p.id AND a.activity_type = 'post'
        WHERE a.user_id = ?
        ORDER BY a.created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    activities = c.fetchall()
    conn.close()
    return activities

def add_user_activity(user_id, activity_type, target_id=None, content=None):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    c.execute('''
        INSERT INTO user_activities (user_id, activity_type, target_id, content, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, activity_type, target_id, content, now))
    
    activity_id = c.lastrowid
    conn.commit()
    conn.close()
    return activity_id

if __name__ == '__main__':
    init_db()
