1. Project Overview
FYP Navigator is a comprehensive web-based platform designed to streamline the management of university final year projects. It facilitates collaboration between students, supervisors, and coordinators by providing tools for project proposal submission, team formation, communication, and project tracking. The system aims to replace traditional manual processes with a centralized digital solution that enhances transparency and efficiency in the FYP lifecycle.


2. Technology Stack
Frontend: HTML, CSS, REACT
Backend: Python, Flask
Database: PostgreSQL
Code Hosting: GitHub, VS-Code, Replit


3. Entity-Relationship Diagram (ERD)
Entities:
•	User (Base user class with role-based inheritance)
•	Student (Extends User)
•	Supervisor (Extends User)
•	Coordinator (Extends User)
•	Project
•	Comment
•	Notification
•	ChatRoom
•	ChatMessage

    
Key Relationships:
•	A Student can create and join multiple Projects (Many-to-Many via team_members)
•	A Supervisor can supervise multiple Projects (One-to-Many)
•	A Project can have multiple Comments (One-to-Many)
•	Each Project has one ChatRoom for team communication (One-to-One)
•	Users receive role-specific Notifications (Polymorphic relationship)
4. Database Schema
The database follows a normalized structure with appropriate foreign key relationships:
User Table:
sql
CREATE TABLE user (     id SERIAL PRIMARY KEY,     username VARCHAR(64) UNIQUE NOT NULL,     full_name VARCHAR(100) NOT NULL,     registration_number VARCHAR(20) UNIQUE NOT NULL,     email VARCHAR(120) UNIQUE NOT NULL,     password_hash VARCHAR(256) NOT NULL,     role VARCHAR(20) NOT NULL,     faculty VARCHAR(100) NOT NULL,     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP );
Student Table:
sql
CREATE TABLE student (     id SERIAL PRIMARY KEY,     user_id INTEGER NOT NULL,     degree VARCHAR(100) NOT NULL,     skills TEXT,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE );
Project Table:
sql
CREATE TABLE project (     id SERIAL PRIMARY KEY,     title VARCHAR(200) NOT NULL,     description TEXT NOT NULL,     required_skills TEXT,     status VARCHAR(20) DEFAULT 'pending',     creator_id INTEGER NOT NULL,     supervisor_id INTEGER,     max_members INTEGER DEFAULT 4,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES student(id),
    FOREIGN KEY (supervisor_id) REFERENCES supervisor(id) );
Team Members (Association Table):
sql
CREATE TABLE team_members (     student_id INTEGER NOT NULL,     project_id INTEGER NOT NULL,     PRIMARY KEY (student_id, project_id),
    FOREIGN KEY (student_id) REFERENCES student(id),
    FOREIGN KEY (project_id) REFERENCES project(id) );

5. Working System
The system features multiple user interfaces including:
•	Authentication Pages (Login/Registration)
•	Role-specific Dashboards for Students, Supervisors, and Coordinators
•	Project Creation and Detail Pages
•	Team Formation Interface
•	Project Chat System
•	Notification Center

6. Functionalities Implemented
User Authentication & Role Management
•	Secure registration and login system
•	Role-based access control (Student, Supervisor, Coordinator)
•	Profile management with role-specific information
Project Management
•	Project proposal submission and approval workflow
•	Project listing with advanced filtering
•	Project status tracking (pending, approved, rejected)
•	Duplicate project detection to prevent similar submissions
Team Formation
•	Team creation and management by project creator
•	Maximum team size enforcement
•	Student self-enrollment in approved projects
Communication System
•	Project-specific chat rooms
•	Commenting system on project pages
•	Role-based notification system for important updates
Coordinator Functions
•	Project approval/rejection with feedback Overview of all projects in the system
•	System-wide monitoring capabilities
Supervisor Functions
•	Project supervision assignment
•	Communication with project teams
•	Guidance through the chat system
7. GitHub & Code Structure
Code Organization:
app.py: Core application setup (Flask configuration, middleware, database initialization) models.py: Database models with SQLAlchemy ORM forms.py: Form classes using WTForms for data validation routes.py: Main application routes and view functions utils.py: Helper functions for access control, notifications, etc.
Design Patterns Used:
•	MVC Pattern: Clear separation of Models (database), Views (templates), and Controllers (routes)
•	Decorator Pattern: Custom decorators for role-based access control
•	Factory Pattern: Used in the creation of different types of notifications and user roles
Security Measures:
•	Password hashing using Werkzeug
•	Form validation to prevent malicious inputs
•	Role-based access checks for all protected routes
•	CSRF protection with Flask   
8. Challenges Faced Technical Challenges:
•	Polymorphic Relationships: Implementing the dashboards for different user roles required careful design of database relationships
•	Role-based Access Control: Ensuring users could only access appropriate resources based on their role
•	Chat System Integration: Building a real-time communication system within the project structure
Development Challenges:
•	User Experience Flow: Creating intuitive interfaces for the different roles
•	Notification Management: Determining when and how to notify users without overwhelming them Project Approval Workflow: Designing an efficient process for project proposals and approvals
Solutions Implemented:
Created custom decorators for role-based access control
•	Implemented a polymorphic relationship design for notifications
•	Designed a modular database schema that accommodates different user roles
•	Added proper error handling and user feedback mechanisms
9. Future Enhancements
Technical Improvements:
•	Implement WebSockets for real-time chat functionality
•	Add file upload capabilities for project documentation
•	Develop a mobile-responsive design for better access on smartphones
Feature Expansions:
•	Calendar integration for project milestones and deadlines
•	Progress tracking system with timeline visualization
•	Integration with plagiarism detection for project proposals
•	Automated reminder system for approaching deadlines
•	Advanced analytics dashboard for coordinators
User Experience Improvements:
•	Implement a rating system for completed projects
•	Create a knowledge base of past successful projects
•	Add email notifications for critical updates

11. Conclusion
The FYP Navigator system successfully addresses the challenges of managing final year projects in an academic environment. By digitizing the entire process from project proposal to completion, it enhances collaboration between students, supervisors, and coordinators while maintaining transparency throughout the project lifecycle.
The development of this system has demonstrated the application of database design principles, objectrelational mapping, authentication systems, and role-based access control in a real-world scenario. The modular architecture allows for future expansion and enhancement of features.
Key learnings from this project include the importance of proper database relationship design, the benefits of role-based system architecture, and the value of a well-structured notification system in collaborative applications.
