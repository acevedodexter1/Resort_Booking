from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, Response, current_app
from app.controllers.auth_controller import admin_required
from app.models.resort_model import CottageModel, UserModel, ReservationModel, ReviewModel, NotificationModel
from app import validate_csrf
import os, uuid, csv, io

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
ALLOWED_EXTS = {'jpg','jpeg','png','gif','webp'}

def _allowed(fn): return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED_EXTS

def _get_upload_dir():
    """Always resolves correctly to static/images using Flask's static_folder."""
    return os.path.join(current_app.static_folder, 'images')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    stats        = ReservationModel.get_stats()
    cottages     = CottageModel.get_all_for_admin()
    users        = UserModel.get_all()
    reservations = ReservationModel.get_all()
    reviews      = ReviewModel.get_all()
    monthly      = ReservationModel.get_monthly_revenue()
    notifs       = NotificationModel.get_recent()
    unread       = NotificationModel.get_unread_count()
    return render_template('admin.html', stats=stats, cottages=cottages,
                           users=users, reservations=reservations, reviews=reviews,
                           monthly=monthly, notifs=notifs, unread=unread, admin=session['user'])

@admin_bp.route('/cottage/add', methods=['POST'])
@admin_required
def add_cottage():
    validate_csrf()
    name       = request.form.get('name','').strip()
    price_str  = request.form.get('price','').strip()
    inclusions = request.form.get('inclusions','').strip()
    max_guests = int(request.form.get('max_guests', 2) or 2)
    policy     = request.form.get('policy','').strip()
    image      = request.files.get('image')

    if not all([name, price_str, inclusions]):
        return jsonify({'success':False,'message':'All fields required.'}), 400
    try:
        price = float(price_str)
        if price <= 0: raise ValueError
    except ValueError:
        return jsonify({'success':False,'message':'Invalid price.'}), 400

    img_fn = 'welcome.jpg'
    if image and image.filename and _allowed(image.filename):
        ext        = image.filename.rsplit('.',1)[1].lower()
        img_fn     = f"{uuid.uuid4().hex}.{ext}"
        upload_dir = _get_upload_dir()
        os.makedirs(upload_dir, exist_ok=True)
        image.save(os.path.join(upload_dir, img_fn))

    if CottageModel.create(name, price, inclusions, img_fn, max_guests, policy):
        return jsonify({'success':True,'message':f'"{name}" added successfully.','image_fn':img_fn,'max_guests':max_guests})
    return jsonify({'success':False,'message':'Cottage name already exists.'}), 409

@admin_bp.route('/cottage/edit/<int:cid>', methods=['POST'])
@admin_required
def edit_cottage(cid):
    validate_csrf()
    name       = request.form.get('name','').strip()
    price_str  = request.form.get('price','').strip()
    inclusions = request.form.get('inclusions','').strip()
    max_guests = int(request.form.get('max_guests', 2) or 2)
    policy     = request.form.get('policy','').strip()
    image      = request.files.get('image')

    if not all([name, price_str, inclusions]):
        return jsonify({'success':False,'message':'All fields required.'}), 400
    try:
        price = float(price_str)
        if price <= 0: raise ValueError
    except ValueError:
        return jsonify({'success':False,'message':'Invalid price.'}), 400

    img_fn = None
    if image and image.filename and _allowed(image.filename):
        ext        = image.filename.rsplit('.',1)[1].lower()
        img_fn     = f"{uuid.uuid4().hex}.{ext}"
        upload_dir = _get_upload_dir()
        os.makedirs(upload_dir, exist_ok=True)
        image.save(os.path.join(upload_dir, img_fn))

    if CottageModel.update(cid, name, price, inclusions, img_fn, max_guests, policy):
        return jsonify({'success':True,'message':f'"{name}" updated successfully.'})
    return jsonify({'success':False,'message':'Update failed — name may already exist.'}), 409

@admin_bp.route('/cottage/delete/<int:cid>', methods=['POST'])
@admin_required
def delete_cottage(cid):
    validate_csrf()
    CottageModel.delete(cid)
    return jsonify({'success':True,'message':'Cottage deleted.'})

@admin_bp.route('/user/delete/<username>', methods=['POST'])
@admin_required
def delete_user(username):
    validate_csrf()
    if username == 'admin':
        return jsonify({'success':False,'message':'Cannot delete admin.'}), 403
    UserModel.delete(username)
    return jsonify({'success':True,'message':f'User "{username}" removed.'})

@admin_bp.route('/reservation/cancel/<int:rid>', methods=['POST'])
@admin_required
def cancel_reservation(rid):
    validate_csrf()
    ReservationModel.cancel(rid)
    return jsonify({'success':True,'message':f'Reservation #{rid} cancelled.'})

@admin_bp.route('/booking/walkin', methods=['POST'])
@admin_required
def walkin_booking():
    validate_csrf()
    data       = request.get_json(silent=True) or request.form
    guest_name = str(data.get('guest_name','')).strip()
    cid        = data.get('cottage_id')
    dt         = str(data.get('date','')).strip()
    shift      = str(data.get('shift','')).strip()
    payment    = str(data.get('payment','cash')).strip()
    reference  = str(data.get('reference','')).strip()
    num_guests = int(data.get('num_guests', 1) or 1)

    if not all([guest_name, cid, dt, shift]):
        return jsonify({'success':False,'message':'All required fields must be filled.'}), 400

    from datetime import date
    try:
        d = date.fromisoformat(dt)
        if d < date.today():
            return jsonify({'success':False,'message':'Cannot book a past date.'}), 400
    except ValueError:
        return jsonify({'success':False,'message':'Invalid date.'}), 400

    cottage = CottageModel.get_by_id(cid)
    if not cottage:
        return jsonify({'success':False,'message':'Cottage not found.'}), 404

    max_g = cottage.get('max_guests') or 2
    if num_guests < 1 or num_guests > max_g:
        return jsonify({'success':False,'message':f'Max {max_g} guests allowed for this cottage.'}), 400

    if ReservationModel.is_booked(cid, dt, shift):
        return jsonify({'success':False,'message':f'{cottage["name"]} is already booked for that slot.'}), 409

    total = cottage['price'] + (500 if 'Night' in shift else 0)
    rid   = ReservationModel.create(cid, guest_name, None, dt, shift, payment,
                                     reference, total, is_walkin=1, num_guests=num_guests)
    return jsonify({'success':True,'message':'Walk-in booking created!','id':rid,'total':total})

@admin_bp.route('/export/csv')
@admin_required
def export_csv():
    rows = ReservationModel.get_all_csv()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID','Cottage','Guest','Email','Date','Shift','Payment','Reference','Total','Guests','Status','Walk-in','Created'])
    for r in rows:
        writer.writerow([r['id'],r['cottage_name'],r['guest_username'],r.get('guest_email',''),
                         r['date'],r['shift'],r['payment_method'],r.get('reference_no',''),
                         r['total_price'],r.get('num_guests',1),r['status'],r['is_walkin'],r.get('created_at','')])
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition':'attachment;filename=reservations.csv'})

@admin_bp.route('/notifications')
@admin_required
def notifications():
    count = NotificationModel.get_unread_count()
    return jsonify({'count': count})

@admin_bp.route('/notifications/read', methods=['POST'])
@admin_required
def mark_read():
    validate_csrf()
    NotificationModel.mark_all_read()
    return jsonify({'success':True})
