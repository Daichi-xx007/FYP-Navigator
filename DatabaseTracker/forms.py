from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, SubmitField, BooleanField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    registration_number = StringField('Registration Number', validators=[DataRequired(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[
        ('student', 'Student'), 
        ('supervisor', 'Supervisor'), 
        ('coordinator', 'Coordinator')
    ])
    faculty = StringField('Faculty', validators=[DataRequired()])
    
    # Student-specific fields
    degree = StringField('Degree Program')
    skills = TextAreaField('Skills (comma separated)')
    
    # Supervisor/Coordinator-specific fields
    department = StringField('Department')
    specialization = StringField('Specialization')
    
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')
            
    def validate_registration_number(self, registration_number):
        user = User.query.filter_by(registration_number=registration_number.data).first()
        if user:
            raise ValidationError('Registration number already registered.')

class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Project Description', validators=[DataRequired()])
    required_skills = TextAreaField('Required Skills (comma separated)', validators=[Optional()])
    supervisor_id = SelectField('Supervisor', coerce=int, validators=[Optional()])
    max_members = IntegerField('Maximum Team Members', default=4, validators=[DataRequired()])
    submit = SubmitField('Submit Project')

class ProjectApprovalForm(FlaskForm):
    project_id = HiddenField('Project ID')
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('approved', 'Approve'),
        ('rejected', 'Reject')
    ], validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[Optional()])
    submit = SubmitField('Update Status')

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Post Comment')

class TeamFormationForm(FlaskForm):
    project_id = HiddenField('Project ID', validators=[DataRequired()])
    students = SelectField('Add Student', coerce=int)
    submit = SubmitField('Add To Team')


class ChatMessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[DataRequired()])
    chat_room_id = HiddenField('Chat Room ID', validators=[DataRequired()])
    submit = SubmitField('Send')
