from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from backend.database import (
    get_user_profile, update_user_profile, get_user_stats,
    get_user_pets, add_pet, update_pet, delete_pet,
    get_user_activities, add_user_activity
)
from backend.auth import login_required
from backend.utils import allowed_file, save_image

profile_bp = Blueprint('profile', __name__)

UPLOAD_FOLDER = 'frontend/static/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

@profile_bp.route('/profile/<username>')
def view_profile(username):
    user = get_user_profile(username)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('main.index'))
    
    user_id = user[0]  # Get user ID from profile tuple
    stats = get_user_stats(user_id)
    pets = get_user_pets(user_id)
    activities = get_user_activities(user_id)
    
    return render_template('profile.html',
                         user=user,
                         stats=stats,
                         pets=pets,
                         activities=activities)

@profile_bp.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, 'avatars', filename)
            
            # Save the image and get the URL
            avatar_url = save_image(file, filepath)
        else:
            avatar_url = None
    else:
        avatar_url = None
    
    bio = request.form.get('bio')
    location = request.form.get('location')
    website = request.form.get('website')
    
    # Get user ID from session
    user = get_user_profile(session['username'])
    user_id = user[0]
    
    # Update profile
    update_user_profile(user_id,
                       bio=bio,
                       location=location,
                       website=website,
                       avatar_url=avatar_url)
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile.view_profile', username=session['username']))

@profile_bp.route('/pets/add', methods=['POST'])
@login_required
def add_new_pet():
    name = request.form.get('name')
    pet_type = request.form.get('type')
    breed = request.form.get('breed')
    age = request.form.get('age')
    bio = request.form.get('bio')
    
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, 'pets', filename)
            
            # Save the image and get the URL
            image_url = save_image(file, filepath)
        else:
            image_url = None
    else:
        image_url = None
    
    # Get user ID from session
    user = get_user_profile(session['username'])
    user_id = user[0]
    
    # Add pet
    pet_id = add_pet(user_id, name, pet_type, breed, age, bio, image_url)
    
    # Add activity
    add_user_activity(user_id, 'pet_added', pet_id, f"Added a new pet: {name}")
    
    flash('Pet added successfully!', 'success')
    return redirect(url_for('profile.view_profile', username=session['username']))

@profile_bp.route('/pets/<int:pet_id>/edit', methods=['POST'])
@login_required
def edit_pet(pet_id):
    name = request.form.get('name')
    pet_type = request.form.get('type')
    breed = request.form.get('breed')
    age = request.form.get('age')
    bio = request.form.get('bio')
    
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, 'pets', filename)
            
            # Save the image and get the URL
            image_url = save_image(file, filepath)
        else:
            image_url = None
    else:
        image_url = None
    
    # Update pet
    update_pet(pet_id,
              name=name,
              type=pet_type,
              breed=breed,
              age=age,
              bio=bio,
              image_url=image_url)
    
    flash('Pet updated successfully!', 'success')
    return redirect(url_for('profile.view_profile', username=session['username']))

@profile_bp.route('/pets/<int:pet_id>/delete', methods=['POST'])
@login_required
def delete_pet_route(pet_id):
    # Delete pet
    delete_pet(pet_id)
    
    flash('Pet deleted successfully!', 'success')
    return redirect(url_for('profile.view_profile', username=session['username']))
