from flask import flash, redirect, url_for
from functools import wraps
from flask_login import current_user

def check_role_access(allowed_roles):
    """Decorator to check if the current user has permission to access a route based on roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            
            if current_user.role not in allowed_roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def is_duplicate_project(title, description, existing_projects):
    """
    Check for potential duplicate project ideas based on title similarity
    and description keywords.
    
    This is a simplified implementation. In a production environment, consider 
    using more advanced techniques like TF-IDF or NLP algorithms.
    """
    title = title.lower().strip()
    description = description.lower().strip()
    
    for project in existing_projects:
        # Check if titles are very similar
        existing_title = project.title.lower().strip()
        if title == existing_title:
            return True
        
        # Check for high overlap in descriptions
        # This is a very basic implementation
        # In production, you would use NLP algorithms
        desc_words = set(description.split())
        existing_desc_words = set(project.description.lower().split())
        
        # Calculate Jaccard similarity
        overlap = len(desc_words.intersection(existing_desc_words))
        union = len(desc_words.union(existing_desc_words))
        
        similarity = overlap / union if union > 0 else 0
        
        # If similarity is above 70%, consider it a potential duplicate
        if similarity > 0.7:
            return True
    
    return False

def create_notification(db, title, message, recipient):
    """Create a notification for a specific user based on their role."""
    from models import Notification
    
    notification = Notification(title=title, message=message)
    
    # Set the recipient based on the user's role
    if recipient.role == 'student':
        notification.student_id = recipient.student.id
    elif recipient.role == 'supervisor':
        notification.supervisor_id = recipient.supervisor.id
    elif recipient.role == 'coordinator':
        notification.coordinator_id = recipient.coordinator.id
    
    db.session.add(notification)
    db.session.commit()
    
    return notification

def get_unread_notifications_count(user):
    """Get the count of unread notifications for a user."""
    if not user.is_authenticated:
        return 0
        
    if user.role == 'student' and user.student:
        return user.student.notifications.filter_by(read=False).count()
    elif user.role == 'supervisor' and user.supervisor:
        return user.supervisor.notifications.filter_by(read=False).count()
    elif user.role == 'coordinator' and user.coordinator:
        return user.coordinator.notifications.filter_by(read=False).count()
    
    return 0
