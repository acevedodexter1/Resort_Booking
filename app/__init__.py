from flask import Flask, session, request, jsonify
from datetime import timedelta
import os, secrets

def generate_csrf():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf():
    data  = request.get_json(silent=True) or {}
    token = data.get('csrf_token') \
            or request.form.get('csrf_token') \
            or request.headers.get('X-CSRFToken')
    if not token or token != session.get('_csrf_token'):
        # Always return JSON — never HTML — so JS can parse it properly
        resp = jsonify({'success': False, 'message': 'Session expired. Please refresh the page (F5).'})
        resp.status_code = 403
        from flask import abort
        abort(resp)

def create_app():
    app = Flask(__name__, template_folder='views/templates', static_folder='static')

    # STABLE key — use env var in production, fixed fallback in dev
    # This prevents session invalidation when Flask's reloader restarts the process
    app.config['SECRET_KEY']                  = os.environ.get('SECRET_KEY', 'paradise-resort-secret-key-2024-do-not-change')
    app.config['SESSION_COOKIE_HTTPONLY']      = True
    app.config['SESSION_COOKIE_SAMESITE']      = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME']   = timedelta(hours=2)
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.jinja_env.globals['csrf_token']        = generate_csrf

    from app.controllers.auth_controller  import auth_bp
    from app.controllers.guest_controller import guest_bp
    from app.controllers.admin_controller import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(guest_bp)
    app.register_blueprint(admin_bp)
    return app
