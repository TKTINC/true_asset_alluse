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



    def __init__(self, auth_manager: AuthManager):
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "super-secret-key"
        self.auth_manager = auth_manager
        
        # Initialize PWA functionality
        self.pwa_config = PWAConfig()
        self.pwa_manager = PWAManager(self.pwa_config)
        self.notification_service = NotificationService(self.pwa_manager)
        
        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)
        self.login_manager.login_view = "login"
        
        self._register_routes()
        self._configure_login_manager()
        
        # Initialize PWA
        asyncio.create_task(self._initialize_pwa())
    
    async def _initialize_pwa(self):
        """Initialize PWA functionality."""
        try:
            await self.pwa_manager.initialize()
            await self.notification_service.start()
            print("PWA functionality initialized successfully")
        except Exception as e:
            print(f"Failed to initialize PWA: {e}")
    
    def _register_routes(self):
        """Register all Flask routes."""
        self.app.route("/")(self.index)
        self.app.route("/login", methods=["GET", "POST"])(self.login)
        self.app.route("/logout")(self.logout)
        self.app.route("/dashboard")(self.dashboard)
        
        # PWA routes
        self.app.route("/manifest.json")(self.manifest)
        self.app.route("/sw.js")(self.service_worker)
        
        # Notification API routes
        self.app.route("/api/notifications/subscribe", methods=["POST"])(self.subscribe_notifications)
        self.app.route("/api/notifications/unsubscribe", methods=["POST"])(self.unsubscribe_notifications)
        self.app.route("/api/notifications/preferences", methods=["GET", "POST"])(self.notification_preferences)
        self.app.route("/api/notifications/history")(self.notification_history)
        self.app.route("/api/notifications/test", methods=["POST"])(self.test_notification)
    
    def manifest(self):
        """Serve web app manifest."""
        try:
            with open("src/ws6_user_interface/dashboard/static/manifest.json", "r") as f:
                manifest_data = json.load(f)
            return jsonify(manifest_data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    def service_worker(self):
        """Serve service worker."""
        try:
            with open("src/ws6_user_interface/dashboard/static/js/sw.js", "r") as f:
                sw_content = f.read()
            return sw_content, 200, {"Content-Type": "application/javascript"}
        except Exception as e:
            return f"console.error('Service worker error: {e}');", 500, {"Content-Type": "application/javascript"}
    
    @login_required
    def subscribe_notifications(self):
        """Subscribe user to push notifications."""
        try:
            subscription_data = request.get_json()
            user_id = current_user.get_id()
            
            # Subscribe user
            success = asyncio.run(self.pwa_manager.subscribe_user(user_id, subscription_data))
            
            if success:
                return jsonify({"success": True, "message": "Subscribed to notifications"})
            else:
                return jsonify({"success": False, "message": "Failed to subscribe"}), 400
                
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    @login_required
    def unsubscribe_notifications(self):
        """Unsubscribe user from push notifications."""
        try:
            user_id = current_user.get_id()
            success = asyncio.run(self.pwa_manager.unsubscribe_user(user_id))
            
            if success:
                return jsonify({"success": True, "message": "Unsubscribed from notifications"})
            else:
                return jsonify({"success": False, "message": "Failed to unsubscribe"}), 400
                
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    
    @login_required
    def notification_preferences(self):
        """Get or update notification preferences."""
        user_id = current_user.get_id()
        
        if request.method == "GET":
            preferences = self.pwa_manager.get_user_preferences(user_id)
            return jsonify(preferences)
        
        elif request.method == "POST":
            try:
                preferences = request.get_json()
                success = asyncio.run(self.pwa_manager.update_user_preferences(user_id, preferences))
                
                if success:
                    return jsonify({"success": True, "message": "Preferences updated"})
                else:
                    return jsonify({"success": False, "message": "Failed to update preferences"}), 400
                    
            except Exception as e:
                return jsonify({"success": False, "message": str(e)}), 500
    
    @login_required
    def notification_history(self):
        """Get notification history."""
        try:
            user_id = current_user.get_id()
            limit = request.args.get("limit", 50, type=int)
            
            history = self.pwa_manager.get_notification_history(user_id, limit)
            return jsonify({"notifications": history})
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @login_required
    def test_notification(self):
        """Send test notification."""
        try:
            user_id = current_user.get_id()
            
            # Send test notification
            asyncio.run(self.notification_service.emit_event(
                SystemEvent.SYSTEM_STATUS,
                {
                    "status": "TEST",
                    "message": "This is a test notification from True-Asset-ALLUSE"
                }
            ))
            
            return jsonify({"success": True, "message": "Test notification sent"})
            
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

