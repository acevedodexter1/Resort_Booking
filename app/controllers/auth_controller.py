from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.models.resort_model import UserModel
from app.services.mail_service import send_welcome_email
from app import validate_csrf
from datetime import datetime, timedelta
from collections import defaultdict
import re

auth_bp = Blueprint('auth', __name__)

# ── Rate Limiting (in-memory, 5 attempts → 15 min block) ──────
_attempts = defaultdict(list)
MAX_ATTEMPTS = 5
BLOCK_MIN    = 15

def _get_ip(): return request.headers.get('X-Forwarded-For', request.remote_addr or '0.0.0.0').split(',')[0].strip()

def _is_blocked(ip):
    cutoff = datetime.utcnow() - timedelta(minutes=BLOCK_MIN)
    _attempts[ip] = [t for t in _attempts[ip] if t > cutoff]
    return len(_attempts[ip]) >= MAX_ATTEMPTS

def _record_fail(ip): _attempts[ip].append(datetime.utcnow())
def _clear(ip): _attempts.pop(ip, None)

# ── Decorators ─────────────────────────────────────────────────
def login_required(f):
    from functools import wraps
    @wraps(f)
    def d(*a, **kw):
        if 'user' not in session: return redirect(url_for('auth.login'))
        return f(*a, **kw)
    return d

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def d(*a, **kw):
        if session.get('role') != 'admin': return redirect(url_for('auth.login'))
        return f(*a, **kw)
    return d

# ── Routes ─────────────────────────────────────────────────────
@auth_bp.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('admin.dashboard') if session.get('role')=='admin' else url_for('guest.dashboard'))
    return render_template('welcome.html')

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        if 'user' in session:
            return redirect(url_for('admin.dashboard') if session.get('role')=='admin' else url_for('guest.dashboard'))
        return render_template('login.html')

    validate_csrf()
    ip   = _get_ip()
    data = request.get_json(silent=True) or request.form
    u    = str(data.get('username','')).strip()
    p    = str(data.get('password','')).strip()

    if not u or not p:
        return jsonify({'success':False,'message':'Please fill in all fields.'}), 400

    if _is_blocked(ip):
        return jsonify({'success':False,'message':f'Too many failed attempts. Try again in {BLOCK_MIN} minutes.'}), 429

    user = UserModel.verify(u, p)
    if not user:
        _record_fail(ip)
        remaining = MAX_ATTEMPTS - len(_attempts[ip])
        msg = f'Incorrect username or password.' if remaining > 1 else f'Incorrect credentials. {remaining} attempt left before lockout.'
        return jsonify({'success':False,'message':msg}), 401

    _clear(ip)
    session.permanent = True
    session['user']   = user['username']
    session['role']   = user['role']
    session['email']  = dict(user).get('email') or ''
    return jsonify({'success':True,'redirect': url_for('admin.dashboard') if user['role']=='admin' else url_for('guest.dashboard'),'role':user['role']})

@auth_bp.route('/register', methods=['POST'])
def register():
    validate_csrf()
    data  = request.get_json(silent=True) or request.form
    u     = str(data.get('username','')).strip()
    p     = str(data.get('password','')).strip()
    conf  = str(data.get('confirm','')).strip()
    email = str(data.get('email','')).strip() or None

    if len(u) < 3:               return jsonify({'success':False,'message':'Username must be at least 3 characters.'}), 400
    if not re.match(r'^[a-zA-Z0-9_]+$', u): return jsonify({'success':False,'message':'Username: letters, numbers and _ only.'}), 400
    if len(p) < 6:               return jsonify({'success':False,'message':'Password must be at least 6 characters.'}), 400
    if p != conf:                return jsonify({'success':False,'message':'Passwords do not match.'}), 400
    if UserModel.find_by_username(u): return jsonify({'success':False,'message':'Username already taken.'}), 409

    if UserModel.create(u, p, email):
        if email: send_welcome_email(email, u)
        return jsonify({'success':True,'message':'Account created! You can now log in.'})
    return jsonify({'success':False,'message':'Registration failed.'}), 500

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))

@auth_bp.route('/ping', methods=['POST'])
@login_required
def ping():
    """Keep session alive — called by session timeout warning JS"""
    session.modified = True
    return jsonify({'ok': True})

@auth_bp.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method == 'GET':
        user = UserModel.find_by_username(session['user'])
        return render_template('profile.html', user=dict(user) if user else {})

    validate_csrf()
    data = request.get_json(silent=True) or request.form
    action = data.get('action','')

    if action == 'change_password':
        current = str(data.get('current','')).strip()
        new_pw  = str(data.get('new_pw','')).strip()
        confirm = str(data.get('confirm','')).strip()
        if not UserModel.verify(session['user'], current):
            return jsonify({'success':False,'message':'Current password is incorrect.'}), 400
        if len(new_pw) < 6:
            return jsonify({'success':False,'message':'New password must be at least 6 characters.'}), 400
        if new_pw != confirm:
            return jsonify({'success':False,'message':'Passwords do not match.'}), 400
        UserModel.update_password(session['user'], new_pw)
        return jsonify({'success':True,'message':'Password changed successfully.'})

    if action == 'update_email':
        email = str(data.get('email','')).strip()
        UserModel.update_email(session['user'], email or None)
        session['email'] = email
        return jsonify({'success':True,'message':'Email updated successfully.'})

    return jsonify({'success':False,'message':'Unknown action.'}), 400
