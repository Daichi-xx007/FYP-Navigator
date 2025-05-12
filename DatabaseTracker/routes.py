from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash
from sqlalchemy import or_

from app import app, db
from models import User, Student, Supervisor, Coordinator, Project, Comment, Notification, ChatRoom, ChatMessage
from forms import (LoginForm, RegistrationForm, ProjectForm, ProjectApprovalForm, 
                  CommentForm, TeamFormationForm, ChatMessageForm)
from utils import check_role_access, is_duplicate_project, create_notification, get_unread_notifications_count

@app.context_processor
def inject_global_variables():
    """Inject global variables into all templates."""
    from datetime import datetime
    return dict(
        unread_notifications=get_unread_notifications_count(current_user),
        now=datetime.now()
    )

@app.route('/')
def index():
    return render_template('index.html', title='FYP Navigator - Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    
    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            registration_number=form.registration_number.data,
            role=form.role.data,
            faculty=form.faculty.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.flush()  # Get the user ID without committing
        
        # Create role-specific profile
        if form.role.data == 'student':
            student = Student(
                user_id=user.id,
                degree=form.degree.data,
                skills=form.skills.data
            )
            db.session.add(student)
        
        elif form.role.data == 'supervisor':
            supervisor = Supervisor(
                user_id=user.id,
                department=form.department.data,
                specialization=form.specialization.data
            )
            db.session.add(supervisor)
        
        elif form.role.data == 'coordinator':
            coordinator = Coordinator(
                user_id=user.id,
                department=form.department.data
            )
            db.session.add(coordinator)
        
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Route to appropriate dashboard based on user role."""
    if current_user.role == 'student':
        return redirect(url_for('student_dashboard'))
    elif current_user.role == 'supervisor':
        return redirect(url_for('supervisor_dashboard'))
    elif current_user.role == 'coordinator':
        return redirect(url_for('coordinator_dashboard'))
    else:
        flash('Invalid user role.', 'danger')
        return redirect(url_for('index'))

@app.route('/dashboard/student')
@login_required
@check_role_access(['student'])
def student_dashboard():
    # Get projects created by the student
    created_projects = Project.query.filter_by(creator_id=current_user.student.id).all()
    
    # Get projects the student is a member of
    joined_projects = current_user.student.projects
    
    # Get recent notifications
    notifications = current_user.student.notifications.order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('dashboard_student.html', title='Student Dashboard',
                          created_projects=created_projects,
                          joined_projects=joined_projects,
                          notifications=notifications)

@app.route('/dashboard/supervisor')
@login_required
@check_role_access(['supervisor'])
def supervisor_dashboard():
    # Get projects supervised by this supervisor
    supervised_projects = current_user.supervisor.supervised_projects.all()
    
    # Get pending projects that need a supervisor
    pending_projects = Project.query.filter_by(status='pending', 
                                              supervisor_id=None).all()
    
    # Get recent notifications
    notifications = current_user.supervisor.notifications.order_by(
        Notification.created_at.desc()).limit(5).all()
    
    return render_template('dashboard_supervisor_new.html', title='Supervisor Dashboard',
                          supervised_projects=supervised_projects,
                          pending_projects=pending_projects,
                          notifications=notifications)

@app.route('/dashboard/coordinator')
@login_required
@check_role_access(['coordinator'])
def coordinator_dashboard():
    # Get all projects for review
    pending_projects = Project.query.filter_by(status='pending').all()
    approved_projects = Project.query.filter_by(status='approved').all()
    rejected_projects = Project.query.filter_by(status='rejected').all()
    
    # Get recent notifications
    notifications = current_user.coordinator.notifications.order_by(
        Notification.created_at.desc()).limit(5).all()
    
    return render_template('dashboard_coordinator_new.html', title='Coordinator Dashboard',
                          pending_projects=pending_projects,
                          approved_projects=approved_projects,
                          rejected_projects=rejected_projects,
                          notifications=notifications)

@app.route('/projects/new', methods=['GET', 'POST'])
@login_required
@check_role_access(['student'])
def create_project():
    form = ProjectForm()
    
    # Populate supervisors dropdown
    supervisors = Supervisor.query.all()
    form.supervisor_id.choices = [(0, 'Select a Supervisor (Optional)')] + [(s.id, s.user.full_name) for s in supervisors]
    
    if form.validate_on_submit():
        # Check for duplicate projects
        existing_projects = Project.query.all()
        if is_duplicate_project(form.title.data, form.description.data, existing_projects):
            flash('Similar project already exists. Please submit a different idea.', 'warning')
            return render_template('project_form.html', title='Create Project', form=form)
        
        # Create new project
        project = Project(
            title=form.title.data,
            description=form.description.data,
            required_skills=form.required_skills.data,
            creator_id=current_user.student.id,
            max_members=form.max_members.data
        )
        
        # Set supervisor if selected
        if form.supervisor_id.data != 0:
            project.supervisor_id = form.supervisor_id.data
            
            # Notify supervisor
            supervisor = Supervisor.query.get(form.supervisor_id.data)
            if supervisor:
                create_notification(
                    db,
                    "New Project Supervision Request",
                    f"Student {current_user.full_name} has requested you to supervise their project '{form.title.data}'.",
                    supervisor.user
                )
        
        # Add student as first team member
        project.team_members.append(current_user.student)
        
        db.session.add(project)
        db.session.commit()
        
        # Notify coordinator
        coordinators = User.query.filter_by(role='coordinator').all()
        for coordinator in coordinators:
            create_notification(
                db,
                "New Project Proposal",
                f"A new project '{project.title}' has been submitted by {current_user.full_name} and needs review.",
                coordinator
            )
        
        flash('Your project has been created and is pending approval.', 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('project_form.html', title='Create Project', form=form)

@app.route('/projects/<int:project_id>')
@login_required
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    comment_form = CommentForm()
    
    # For team formation (if user is creator and project is approved)
    can_add_members = (current_user.role == 'student' and 
                      current_user.student.id == project.creator_id and
                      project.status == 'approved' and
                      project.team_members.count() < project.max_members)
    
    team_formation_form = None
    if can_add_members:
        team_formation_form = TeamFormationForm()
        # Get students not already in the team
        team_formation_form.project_id.data = project_id
        
        # Get IDs of students already in the team
        team_member_ids = [member.id for member in project.team_members]
        
        # Find students not in the team
        available_students = Student.query.filter(
            Student.id != current_user.student.id,
            ~Student.id.in_(team_member_ids)
        ).all()
        
        team_formation_form.students.choices = [(s.id, f"{s.user.full_name} ({s.user.registration_number})") 
                                           for s in available_students]
    
    # Check if user can approve project (coordinator)
    can_approve = current_user.role == 'coordinator'
    approval_form = ProjectApprovalForm() if can_approve else None
    
    if approval_form:
        approval_form.project_id.data = project_id
    
    # Get project comments
    comments = Comment.query.filter_by(project_id=project.id).order_by(Comment.created_at.desc()).all()
    
    # Get or create chat room for this project
    chat_room = ChatRoom.query.filter_by(project_id=project.id).first()
    if not chat_room:
        chat_room = ChatRoom(project_id=project.id, name=f"Chat: {project.title}")
        db.session.add(chat_room)
        db.session.commit()
    
    # Get chat messages for this project
    chat_messages = ChatMessage.query.filter_by(chat_room_id=chat_room.id).order_by(ChatMessage.created_at).all()
    chat_form = ChatMessageForm()
    chat_form.chat_room_id.data = chat_room.id
    
    # Check if user is part of the project team or is the supervisor/coordinator
    is_team_member = False
    if current_user.role == 'student':
        is_team_member = current_user.student in project.team_members or current_user.student.id == project.creator_id
    elif current_user.role == 'supervisor' and project.supervisor_id:
        is_team_member = current_user.supervisor.id == project.supervisor_id
    elif current_user.role == 'coordinator':
        is_team_member = True

    return render_template('project_details.html', 
                          title=project.title, 
                          project=project,
                          comments=comments,
                          comment_form=comment_form,
                          team_formation_form=team_formation_form,
                          approval_form=approval_form,
                          can_add_members=can_add_members,
                          can_approve=can_approve,
                          chat_room=chat_room,
                          chat_messages=chat_messages,
                          chat_form=chat_form,
                          is_team_member=is_team_member)

@app.route('/projects')
@login_required
def list_projects():
    # Get filter parameters
    status = request.args.get('status', 'all')
    supervisor_id = request.args.get('supervisor_id', 'all')
    search = request.args.get('search', '')
    
    # Base query
    query = Project.query
    
    # Apply filters
    if status != 'all':
        query = query.filter_by(status=status)
    
    if supervisor_id != 'all' and supervisor_id.isdigit():
        query = query.filter_by(supervisor_id=int(supervisor_id))
    
    if search:
        query = query.filter(
            or_(
                Project.title.ilike(f'%{search}%'),
                Project.description.ilike(f'%{search}%')
            )
        )
    
    # Get projects
    projects = query.all()
    
    # Get all supervisors for the filter dropdown
    supervisors = Supervisor.query.all()
    
    return render_template('projects_list.html', 
                          title='Projects List',
                          projects=projects,
                          supervisors=supervisors,
                          status=status,
                          supervisor_id=supervisor_id,
                          search=search)

@app.route('/projects/<int:project_id>/approve', methods=['POST'])
@login_required
@check_role_access(['coordinator'])
def approve_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectApprovalForm()
    
    if form.validate_on_submit():
        project.status = form.status.data
        
        # Add a comment if provided
        if form.comment.data:
            comment = Comment(
                content=form.comment.data,
                project_id=project.id,
                user_id=current_user.id
            )
            db.session.add(comment)
        
        db.session.commit()
        
        # Notify project creator
        status_message = "approved" if form.status.data == 'approved' else "rejected" if form.status.data == 'rejected' else "updated"
        create_notification(
            db,
            f"Project {status_message.capitalize()}",
            f"Your project '{project.title}' has been {status_message} by the coordinator.",
            project.creator.user
        )
        
        flash(f'Project status updated to {form.status.data}.', 'success')
        return redirect(url_for('view_project', project_id=project.id))
    
    flash('Error updating project status.', 'danger')
    return redirect(url_for('view_project', project_id=project.id))

@app.route('/projects/<int:project_id>/comment', methods=['POST'])
@login_required
def add_comment(project_id):
    project = Project.query.get_or_404(project_id)
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            project_id=project.id,
            user_id=current_user.id
        )
        db.session.add(comment)
        db.session.commit()
        
        # Notify project creator if commenter is not the creator
        if current_user.id != project.creator.user_id:
            create_notification(
                db,
                "New Comment on Your Project",
                f"{current_user.full_name} commented on your project '{project.title}'.",
                project.creator.user
            )
        
        flash('Comment added successfully.', 'success')
    else:
        flash('Error adding comment.', 'danger')
    
    return redirect(url_for('view_project', project_id=project.id))

@app.route('/projects/<int:project_id>/join', methods=['POST'])
@login_required
@check_role_access(['student'])
def join_project(project_id):
    """Allow a student to join an existing project."""
    project = Project.query.get_or_404(project_id)
    
    # Check if project is approved and has space
    if project.status != 'approved':
        flash('You can only join approved projects.', 'danger')
        return redirect(url_for('view_project', project_id=project_id))
    
    if project.team_members.count() >= project.max_members:
        flash('This project team is already full.', 'danger')
        return redirect(url_for('view_project', project_id=project_id))
    
    # Check if user is not already part of the team and not the creator
    if current_user.student in project.team_members or current_user.student.id == project.creator_id:
        flash('You are already part of this project team.', 'info')
        return redirect(url_for('view_project', project_id=project_id))
    
    # Add student to the team
    project.team_members.append(current_user.student)
    db.session.commit()
    
    # Create notifications
    # Notify project creator
    create_notification(
        db,
        "New team member",
        f"{current_user.full_name} has joined your project: {project.title}",
        project.creator
    )
    
    # Notify supervisor if assigned
    if project.supervisor_id:
        create_notification(
            db,
            "New team member",
            f"{current_user.full_name} has joined project: {project.title}",
            project.supervisor
        )
    
    flash('You have successfully joined the project team!', 'success')
    return redirect(url_for('view_project', project_id=project_id))


@app.route('/projects/<int:project_id>/team/add', methods=['POST'])
@login_required
@check_role_access(['student'])
def add_team_member(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check if current user is the project creator
    if current_user.student.id != project.creator_id:
        flash('Only the project creator can add team members.', 'danger')
        return redirect(url_for('view_project', project_id=project.id))
    
    # Check if project is approved
    if project.status != 'approved':
        flash('Team members can only be added to approved projects.', 'danger')
        return redirect(url_for('view_project', project_id=project.id))
    
    form = TeamFormationForm()
    
    # Get all students
    students = Student.query.all()
    form.students.choices = [(s.id, s.user.full_name) for s in students]
    
    if form.validate_on_submit():
        student_id = form.students.data
        student = Student.query.get(student_id)
        
        if not student:
            flash('Student not found.', 'danger')
            return redirect(url_for('view_project', project_id=project.id))
        
        # Check if team is full
        if project.team_members.count() >= project.max_members:
            flash('Team is already full.', 'warning')
            return redirect(url_for('view_project', project_id=project.id))
        
        # Check if student is already in the team
        if student in project.team_members:
            flash('Student is already in the team.', 'warning')
            return redirect(url_for('view_project', project_id=project.id))
        
        # Add student to team
        project.team_members.append(student)
        db.session.commit()
        
        # Notify the added student
        create_notification(
            db,
            "Added to Project Team",
            f"You have been added to the project team for '{project.title}' by {current_user.full_name}.",
            student.user
        )
        
        flash(f'{student.user.full_name} added to the team.', 'success')
    else:
        flash('Error adding team member.', 'danger')
    
    return redirect(url_for('view_project', project_id=project.id))

@app.route('/chat/send', methods=['POST'])
@login_required
def send_chat_message():
    """Send a chat message to a project chat room."""
    form = ChatMessageForm()
    if form.validate_on_submit():
        chat_room = ChatRoom.query.get_or_404(form.chat_room_id.data)
        project = Project.query.get_or_404(chat_room.project_id)
        
        # Verify user has access to this chat room
        has_access = False
        if current_user.role == 'student':
            has_access = current_user.student in project.team_members or current_user.student.id == project.creator_id
        elif current_user.role == 'supervisor' and project.supervisor_id:
            has_access = current_user.supervisor.id == project.supervisor_id
        elif current_user.role == 'coordinator':
            has_access = True
            
        if not has_access:
            flash('You do not have permission to send messages in this chat.', 'danger')
            return redirect(url_for('view_project', project_id=project.id))
        
        # Create the new message
        message = ChatMessage(
            chat_room_id=chat_room.id,
            user_id=current_user.id,
            content=form.content.data
        )
        db.session.add(message)
        db.session.commit()
        
        flash('Message sent successfully.', 'success')
        
        # Create notification for team members
        if current_user.role == 'student':
            # Notify supervisor if assigned
            if project.supervisor_id:
                create_notification(
                    db,
                    f"New message in {project.title}",
                    f"{current_user.full_name} sent a message in the project chat: '{form.content.data[:50]}...'",
                    project.supervisor
                )
            
            # Notify team members (except sender)
            for student in project.team_members:
                if student.id != current_user.student.id:
                    create_notification(
                        db, 
                        f"New message in {project.title}",
                        f"{current_user.full_name} sent a message in the project chat: '{form.content.data[:50]}...'",
                        student
                    )
            
            # Notify creator if not the sender
            if project.creator_id != current_user.student.id:
                create_notification(
                    db,
                    f"New message in {project.title}",
                    f"{current_user.full_name} sent a message in the project chat: '{form.content.data[:50]}...'",
                    project.creator
                )
                
        elif current_user.role == 'supervisor':
            # Notify all team members
            for student in project.team_members:
                create_notification(
                    db, 
                    f"New message from supervisor in {project.title}",
                    f"{current_user.full_name} sent a message in the project chat: '{form.content.data[:50]}...'",
                    student
                )
            
            # Notify creator
            create_notification(
                db,
                f"New message from supervisor in {project.title}",
                f"{current_user.full_name} sent a message in the project chat: '{form.content.data[:50]}...'",
                project.creator
            )
            
        elif current_user.role == 'coordinator':
            # Notify all team members
            for student in project.team_members:
                create_notification(
                    db, 
                    f"New message from coordinator in {project.title}",
                    f"{current_user.full_name} sent a message in the project chat: '{form.content.data[:50]}...'",
                    student
                )
            
            # Notify creator
            create_notification(
                db,
                f"New message from coordinator in {project.title}",
                f"{current_user.full_name} sent a message in the project chat: '{form.content.data[:50]}...'",
                project.creator
            )
            
            # Notify supervisor if assigned
            if project.supervisor_id:
                create_notification(
                    db,
                    f"New message from coordinator in {project.title}",
                    f"{current_user.full_name} sent a message in the project chat: '{form.content.data[:50]}...'",
                    project.supervisor
                )
        
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "danger")
    
    return redirect(url_for('view_project', project_id=chat_room.project_id))


@app.route('/notifications')
@login_required
def view_notifications():
    if current_user.role == 'student' and current_user.student:
        notifications = current_user.student.notifications.order_by(Notification.created_at.desc()).all()
    elif current_user.role == 'supervisor' and current_user.supervisor:
        notifications = current_user.supervisor.notifications.order_by(Notification.created_at.desc()).all()
    elif current_user.role == 'coordinator' and current_user.coordinator:
        notifications = current_user.coordinator.notifications.order_by(Notification.created_at.desc()).all()
    else:
        notifications = []
    
    # Mark all as read
    for notification in notifications:
        notification.read = True
    
    db.session.commit()
    
    return render_template('notifications.html', title='Notifications', notifications=notifications)

@app.route('/error')
def error_page():
    return render_template('error.html', title='Error')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', title='Page Not Found', error_code=404,
                          error_message='The page you are looking for does not exist.'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', title='Forbidden', error_code=403,
                          error_message='You do not have permission to access this resource.'), 403

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', title='Server Error', error_code=500,
                          error_message='An internal server error occurred.'), 500
