from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.controllers.auth_controller import login_required
from app.models.resort_model import CottageModel, ReservationModel, ReviewModel
from app.services.mail_service import (
    send_booking_confirmation,
    send_cancellation_email,
)
from app import validate_csrf
from datetime import date

guest_bp = Blueprint('guest', __name__, url_prefix='/guest')


@guest_bp.route('/dashboard')
@login_required
def dashboard():
    cottages = CottageModel.get_all()
    today    = date.today().isoformat()
    return render_template('dashboard.html', cottages=cottages,
                           user=session['user'], today=today)


@guest_bp.route('/booking/<int:cid>')
@login_required
def booking(cid):
    cottage = CottageModel.get_by_id(cid)
    if not cottage:
        return redirect(url_for('guest.dashboard'))
    reviews = CottageModel.get_reviews(cid)
    today   = date.today().isoformat()
    return render_template('booking.html', cottage=cottage, today=today,
                           user=session['user'], reviews=reviews)


@guest_bp.route('/booking/confirm', methods=['POST'])
@login_required
def confirm_booking():
    validate_csrf()
    data       = request.get_json(silent=True) or request.form
    cid        = data.get('cottage_id')
    dt         = str(data.get('date', '')).strip()
    shift      = str(data.get('shift', '')).strip()
    payment    = str(data.get('payment', '')).strip()
    ref        = str(data.get('reference', '')).strip()
    num_guests = int(data.get('num_guests', 1) or 1)

    if not all([cid, dt, shift, payment]):
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400

    try:
        d = date.fromisoformat(dt)
        if d < date.today():
            return jsonify({'success': False, 'message': 'Cannot book a past date.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format.'}), 400

    if payment == 'bank' and not ref:
        return jsonify({'success': False,
                        'message': 'Reference number required for bank payment.'}), 400

    cottage = CottageModel.get_by_id(cid)
    if not cottage:
        return jsonify({'success': False, 'message': 'Cottage not found.'}), 404

    max_g = cottage.get('max_guests') or 2
    if num_guests < 1 or num_guests > max_g:
        return jsonify({'success': False,
                        'message': f'Guest count must be between 1 and {max_g}.'}), 400

    if ReservationModel.is_booked(cid, dt, shift):
        return jsonify({'success': False,
                        'message': f'{cottage["name"]} is fully booked on {dt} ({shift}).'}), 409

    total  = cottage['price'] + (500 if 'Night' in shift else 0)
    email  = session.get('email', '')

    rid = ReservationModel.create(
        cid, session['user'], email, dt, shift,
        payment, ref, total, num_guests=num_guests
    )

    receipt = {
        'id':         rid,
        'cottage':    cottage['name'],
        'guest':      session['user'],
        'date':       dt,
        'shift':      shift,
        'payment':    payment,
        'reference':  ref,
        'total':      total,
        'num_guests': num_guests,
    }

    # ── Send booking confirmation email ──────────────────────
    email_sent = False
    if email:
        email_sent = send_booking_confirmation(email, receipt)

    return jsonify({
        'success':    True,
        'message':    'Booking confirmed!',
        'receipt':    receipt,
        'email_sent': email_sent,
        'guest_email': email,
    })


@guest_bp.route('/booking/reschedule/<int:rid>', methods=['POST'])
@login_required
def reschedule(rid):
    validate_csrf()
    data      = request.get_json(silent=True) or request.form
    new_date  = str(data.get('date', '')).strip()
    new_shift = str(data.get('shift', '')).strip()

    res = ReservationModel.get_by_id(rid)
    if not res or res['guest_username'] != session['user']:
        return jsonify({'success': False, 'message': 'Reservation not found.'}), 404
    if res['status'] != 'confirmed':
        return jsonify({'success': False,
                        'message': 'Only confirmed bookings can be rescheduled.'}), 400

    try:
        d = date.fromisoformat(new_date)
        if d < date.today():
            return jsonify({'success': False,
                            'message': 'Cannot reschedule to a past date.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format.'}), 400

    if ReservationModel.is_booked(res['cottage_id'], new_date, new_shift, exclude_id=rid):
        return jsonify({'success': False, 'message': 'That slot is already booked.'}), 409

    new_total = res['cottage_price'] + (500 if 'Night' in new_shift else 0)
    ReservationModel.reschedule(rid, session['user'], new_date, new_shift, new_total)

    return jsonify({
        'success':   True,
        'message':   'Booking rescheduled successfully!',
        'new_date':  new_date,
        'new_shift': new_shift,
        'new_total': new_total,
    })


@guest_bp.route('/my-bookings')
@login_required
def my_bookings():
    bookings = ReservationModel.get_by_user(session['user'])
    for b in bookings:
        b['has_review'] = ReviewModel.exists(b['id'])
    return render_template('my_bookings.html', bookings=bookings,
                           user=session['user'])


@guest_bp.route('/cancel/<int:rid>', methods=['POST'])
@login_required
def cancel_booking(rid):
    validate_csrf()

    # Fetch reservation BEFORE cancelling so we have all details for the email
    res = ReservationModel.get_by_id(rid)
    if not res or res['guest_username'] != session['user']:
        return jsonify({'success': False, 'message': 'Reservation not found.'}), 404

    ReservationModel.cancel(rid, session['user'])

    # ── Send cancellation + refund email ─────────────────────
    guest_email = res.get('guest_email') or session.get('email', '')
    email_sent = False
    if guest_email:
        email_sent = send_cancellation_email(guest_email, dict(res))

    return jsonify({'success': True, 'message': 'Booking cancelled.', 'email_sent': email_sent})


@guest_bp.route('/review/<int:rid>', methods=['POST'])
@login_required
def submit_review(rid):
    validate_csrf()
    data    = request.get_json(silent=True) or request.form
    rating  = int(data.get('rating', 0))
    comment = str(data.get('comment', '')).strip()

    if not 1 <= rating <= 5:
        return jsonify({'success': False, 'message': 'Rating must be 1–5 stars.'}), 400

    res = ReservationModel.get_by_id(rid)
    if not res or res['guest_username'] != session['user']:
        return jsonify({'success': False, 'message': 'Reservation not found.'}), 404
    if res['status'] != 'confirmed':
        return jsonify({'success': False,
                        'message': 'Only confirmed stays can be reviewed.'}), 400
    if ReviewModel.exists(rid):
        return jsonify({'success': False,
                        'message': 'You already reviewed this booking.'}), 409

    ReviewModel.create(rid, res['cottage_id'], session['user'], rating, comment)
    return jsonify({'success': True, 'message': 'Thank you for your review!'})


@guest_bp.route('/availability')
@login_required
def check_availability():
    cid   = request.args.get('cottage_id', '')
    dt    = request.args.get('date', '')
    shift = request.args.get('shift', '')
    if not all([cid, dt, shift]):
        return jsonify({'available': False, 'message': 'Missing parameters.'}), 400
    booked = ReservationModel.is_booked(cid, dt, shift)
    return jsonify({'available': not booked})


@guest_bp.route('/booked-dates/<int:cid>')
@login_required
def booked_dates(cid):
    dates = CottageModel.get_booked_dates(cid)
    return jsonify(dates)
