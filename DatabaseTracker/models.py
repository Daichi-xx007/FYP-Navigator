from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Association table for many-to-many relationship between Student and Project (team members)
team_members = db.Table('team_members',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    registration_number = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'supervisor', 'coordinator'
    faculty = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Role-specific relationship
    student = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    supervisor = db.relationship('Supervisor', backref='user', uselist=False, cascade='all, delete-orphan')
    coordinator = db.relationship('Coordinator', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    degree = db.Column(db.String(100), nullable=False)
    skills = db.Column(db.Text, nullable=True)  # Comma-separated skills
    
    # Projects where the student is a member
    projects = db.relationship('Project', secondary=team_members, backref=db.backref('team_members', lazy='dynamic'))
    
    # Projects created by this student
    created_projects = db.relationship('Project', backref='creator', lazy='dynamic', 
                                      foreign_keys='Project.creator_id')
    
    notifications = db.relationship('Notification', backref='student', lazy='dynamic')

    def __repr__(self):
        return f'<Student {self.user.username}>'


class Supervisor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=True)
    
    # Projects supervised by this supervisor
    supervised_projects = db.relationship('Project', backref='supervisor', lazy='dynamic',
                                         foreign_keys='Project.supervisor_id')
    
    notifications = db.relationship('Notification', backref='supervisor', lazy='dynamic')

    def __repr__(self):
        return f'<Supervisor {self.user.username}>'


class Coordinator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    
    notifications = db.relationship('Notification', backref='coordinator', lazy='dynamic')

    def __repr__(self):
        return f'<Coordinator {self.user.username}>'


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.Text, nullable=True)  # Comma-separated skills
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    
    creator_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=True)
    
    max_members = db.Column(db.Integer, default=4)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Comments on this project
    comments = db.relationship('Comment', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Project {self.title}>'


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with the User model
    user = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Comment {self.id}>'


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    
    # Polymorphic relationship - notification can be for any role
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=True)
    coordinator_id = db.Column(db.Integer, db.ForeignKey('coordinator.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.id}>'


class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False, default="Project Chat")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref=db.backref('chat_room', uselist=False))
    messages = db.relationship('ChatMessage', backref='chat_room', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ChatRoom {self.name} for Project {self.project_id}>'


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('chat_messages', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ChatMessage {self.id} by User {self.user_id}>'
