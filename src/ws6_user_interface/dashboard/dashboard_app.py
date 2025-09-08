"""
Web Dashboard Application

This module implements the main web dashboard application using Flask and
Jinja2 templates, providing a user-friendly interface for interacting with
the True-Asset-ALLUSE system.
"""

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from src.ws6_user_interface.authentication import AuthManager, rbac, Role
from .user import User

class DashboardApp:
    """
    Main Web Dashboard Application.
    """
    
    def __init__(self, auth_manager: AuthManager):
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "super-secret-key"
        self.auth_manager = auth_manager
        
        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)
        self.login_manager.login_view = "login"
        
        self._register_routes()
        self._configure_login_manager()
    
    def _register_routes(self):
        """Register all Flask routes."""
        self.app.route("/")(self.index)
        self.app.route("/login", methods=["GET", "POST"])(self.login)
        self.app.route("/logout")(self.logout)
        self.app.route("/dashboard")(self.dashboard)
    
    def _configure_login_manager(self):
        """Configure Flask-Login."""
        @self.login_manager.user_loader
        def load_user(user_id):
            # In a real application, you would load the user from a database
            # For now, we'll just create a dummy user
            return User(user_id)
    
    def index(self):
        return redirect(url_for("login"))
    
    def login(self):
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            
            # In a real application, you would verify the user against a database
            if self.auth_manager.verify_password(password, self.auth_manager.get_password_hash("password")):
                user = User(username)
                login_user(user)
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid username or password")
        
        return render_template("login.html")
    
    @login_required
    def logout(self):
        logout_user()
        return redirect(url_for("login"))
    
    @login_required
    def dashboard(self):
        return render_template("dashboard.html", user=current_user)
    
    def get_app(self) -> Flask:
        """Get the Flask application instance."""
        return self.app


