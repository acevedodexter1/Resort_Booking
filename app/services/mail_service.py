"""
Email service using Python's built-in smtplib.
Configure via environment variables (or a .env file loaded by your run.py):

  SMTP_SERVER  — e.g.  smtp.gmail.com
  SMTP_PORT    — e.g.  587
  SMTP_USER    — your Gmail / SMTP address
  SMTP_PASS    — Gmail App Password (Settings → Security → App Passwords)
  SMTP_FROM    — display name shown to recipient, e.g. Paradise Resort

If any of the required vars are missing, all functions silently return False
so the app works normally even without email configured.
"""
import smtplib, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── helpers ───────────────────────────────────────────────────
def _cfg():
    return {
        'server': os.environ.get('SMTP_SERVER', ''),
        'port':   int(os.environ.get('SMTP_PORT', 587)),
        'user':   os.environ.get('SMTP_USER', ''),
        'pwd':    os.environ.get('SMTP_PASS', ''),
        'sender': os.environ.get('SMTP_FROM', 'Paradise Resort'),
    }

def is_configured():
    c = _cfg()
    return bool(c['server'] and c['user'] and c['pwd'])

def _send(cfg, to_email, subject, html):
    """Low-level send — raises on failure, caller catches."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = f'{cfg["sender"]} <{cfg["user"]}>'
    msg['To']      = to_email
    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP(cfg['server'], cfg['port']) as s:
        s.starttls()
        s.login(cfg['user'], cfg['pwd'])
        s.sendmail(cfg['user'], to_email, msg.as_string())

def _header(title, subtitle=''):
    return f"""
    <div style="background:linear-gradient(135deg,#0b3d26,#156635);
                padding:28px 24px;text-align:center;
                border-radius:12px 12px 0 0">
      <div style="font-size:32px;margin-bottom:8px">🌴</div>
      <h1 style="color:#fff;margin:0;font-size:22px;font-weight:700;
                 font-family:Georgia,serif">{title}</h1>
      {"<p style='color:rgba(255,255,255,.8);margin:6px 0 0;font-size:14px'>"+subtitle+"</p>" if subtitle else ""}
    </div>"""

def _footer(year=None):
    y = year or datetime.now().year
    return f"""
    <div style="background:#f5f5f5;padding:14px 24px;text-align:center;
                font-size:12px;color:#999;border-radius:0 0 12px 12px;
                border-top:1px solid #e0e0e0">
      © {y} Paradise Resort · Surigao del Sur, Philippines
    </div>"""

def _wrap(inner_html):
    return f"""<!DOCTYPE html><html><body style="margin:0;padding:20px;
    background:#f0f0f0;font-family:Arial,Helvetica,sans-serif">
    <div style="max-width:540px;margin:auto;background:#fff;
                border-radius:12px;overflow:hidden;
                box-shadow:0 4px 20px rgba(0,0,0,.12)">
      {inner_html}
    </div></body></html>"""

def _row(label, value, shaded=False):
    bg = 'background:#e8f7ee;' if shaded else ''
    return f"""<tr>
      <td style="padding:10px 14px;font-weight:600;color:#333;font-size:14px;
                 border-bottom:1px solid #f0f0f0;{bg}width:38%">{label}</td>
      <td style="padding:10px 14px;color:#444;font-size:14px;
                 border-bottom:1px solid #f0f0f0;{bg}">{value}</td>
    </tr>"""


# ── PUBLIC FUNCTIONS ───────────────────────────────────────────

def send_welcome_email(to_email, username):
    """Sent when a new guest account is created."""
    if not to_email or not is_configured():
        return False
    cfg = _cfg()
    try:
        body = f"""
        {_header('Welcome to Paradise Resort!', 'Your account is ready 🎉')}
        <div style="padding:28px 24px">
          <p style="color:#333;margin:0 0 12px">Hi <strong>{username}</strong>,</p>
          <p style="color:#555;margin:0 0 20px;line-height:1.6">
            Welcome aboard! Your account has been created and you can now
            browse and book our accommodations instantly.
          </p>
          <div style="text-align:center;margin:24px 0">
            <a href="#" style="background:#156635;color:#fff;padding:12px 28px;
               border-radius:8px;text-decoration:none;font-weight:700;
               font-size:15px;display:inline-block">🌴 Start Booking</a>
          </div>
          <p style="color:#aaa;font-size:12px;margin-top:20px">
            If you didn't create this account, please ignore this email.
          </p>
        </div>
        {_footer()}"""
        _send(cfg, to_email, 'Welcome to Paradise Resort!', _wrap(body))
        return True
    except Exception as e:
        print(f'[Mail Error - welcome] {e}'); return False


def send_booking_confirmation(to_email, receipt):
    """
    Sent immediately after a guest confirms a booking.
    receipt dict keys: id, cottage, guest, date, shift,
                       payment, reference, total, num_guests
    """
    if not to_email or not is_configured():
        return False
    cfg = _cfg()
    try:
        rid       = receipt.get('id', '')
        cottage   = receipt.get('cottage', '')
        guest     = receipt.get('guest', '')
        date      = receipt.get('date', '')
        shift     = receipt.get('shift', '')
        payment   = receipt.get('payment', '')
        reference = receipt.get('reference', '')
        total     = receipt.get('total', 0)
        num_g     = receipt.get('num_guests', 1)

        shift_label   = '🌙 Night Tour (6pm–12mn)' if 'Night' in shift else '☀️ Day Tour (8am–5pm)'
        payment_label = '📱 GCash / Bank Transfer' if payment == 'bank' else '💵 Cash'

        rows = (
            _row('Booking #',    f'<strong>#{rid}</strong>', shaded=True) +
            _row('Cottage',      cottage) +
            _row('Guest',        guest, shaded=True) +
            _row('Date',         date) +
            _row('Shift',        shift_label, shaded=True) +
            _row('Guests',       f'{num_g} person{"s" if num_g > 1 else ""}') +
            _row('Payment',      payment_label, shaded=True) +
            (f'<tr><td style="padding:10px 14px;font-size:14px;border-bottom:1px solid #f0f0f0">Reference</td>'
             f'<td style="padding:10px 14px;font-size:14px;border-bottom:1px solid #f0f0f0">{reference}</td></tr>'
             if reference else '') +
            f"""<tr style="background:#0b3d26">
                  <td style="padding:12px 14px;font-weight:700;color:#fff;font-size:16px">TOTAL</td>
                  <td style="padding:12px 14px;font-weight:700;color:#f0b429;font-size:16px">
                    ₱{total:,.2f}</td>
                </tr>"""
        )

        body = f"""
        {_header('Booking Confirmed! ✅', f'Reservation #{rid} · Paradise Resort')}
        <div style="padding:24px">
          <p style="color:#333;margin:0 0 8px">Dear <strong>{guest}</strong>,</p>
          <p style="color:#555;margin:0 0 20px;line-height:1.6">
            Your booking is confirmed! Here are your reservation details:
          </p>
          <table style="width:100%;border-collapse:collapse;border-radius:8px;
                        overflow:hidden;border:1px solid #e0e0e0">
            {rows}
          </table>

          <div style="margin-top:20px;background:#e8f7ee;border:1px solid #cce5d4;
                      border-radius:8px;padding:14px 16px">
            <p style="margin:0;color:#156635;font-size:13px;line-height:1.6">
              <strong>💸 Refund Policy:</strong> You may cancel anytime and receive a
              <strong>full refund</strong> within 3–5 business days via your original
              payment method.
            </p>
          </div>

          <p style="color:#888;font-size:13px;margin-top:20px;text-align:center">
            We look forward to seeing you at Paradise Resort! 🌴
          </p>
        </div>
        {_footer()}"""

        _send(cfg, to_email,
              f'Booking Confirmed — Paradise Resort #{rid}',
              _wrap(body))
        return True
    except Exception as e:
        print(f'[Mail Error - booking] {e}'); return False


def send_cancellation_email(to_email, reservation):
    """
    Sent when a guest cancels their booking.
    reservation dict keys: id, cottage_name, date, shift,
                           total_price, payment_method, guest_username
    """
    if not to_email or not is_configured():
        return False
    cfg = _cfg()
    try:
        rid     = reservation.get('id', '')
        cottage = reservation.get('cottage_name', reservation.get('cottage', ''))
        guest   = reservation.get('guest_username', reservation.get('guest', ''))
        date    = reservation.get('date', '')
        shift   = reservation.get('shift', '')
        total   = reservation.get('total_price', reservation.get('total', 0))
        payment = reservation.get('payment_method', reservation.get('payment', ''))

        shift_label   = '🌙 Night Tour' if 'Night' in shift else '☀️ Day Tour'
        payment_label = '📱 GCash / Bank Transfer' if payment == 'bank' else '💵 Cash'

        rows = (
            _row('Booking #',     f'<strong>#{rid}</strong>', shaded=True) +
            _row('Cottage',       cottage) +
            _row('Date',          date, shaded=True) +
            _row('Shift',         shift_label) +
            _row('Payment Method', payment_label, shaded=True) +
            f"""<tr style="background:#0b3d26">
                  <td style="padding:12px 14px;font-weight:700;color:#fff;font-size:16px">Refund Amount</td>
                  <td style="padding:12px 14px;font-weight:700;color:#f0b429;font-size:16px">
                    ₱{total:,.2f}</td>
                </tr>"""
        )

        body = f"""
        {_header('Booking Cancelled', f'Reservation #{rid} has been cancelled')}
        <div style="padding:24px">
          <p style="color:#333;margin:0 0 8px">Dear <strong>{guest}</strong>,</p>
          <p style="color:#555;margin:0 0 20px;line-height:1.6">
            Your booking has been successfully cancelled. Here is a summary:
          </p>
          <table style="width:100%;border-collapse:collapse;border-radius:8px;
                        overflow:hidden;border:1px solid #e0e0e0">
            {rows}
          </table>

          <div style="margin-top:20px;background:#e8f7ee;border:1px solid #cce5d4;
                      border-radius:8px;padding:16px">
            <p style="margin:0 0 6px;color:#156635;font-weight:700;font-size:14px">
              💸 Your Refund
            </p>
            <p style="margin:0;color:#333;font-size:13px;line-height:1.7">
              A full refund of <strong>₱{total:,.2f}</strong> will be processed
              within <strong>3–5 business days</strong> via your original
              payment method ({payment_label}).
            </p>
            <p style="margin:8px 0 0;color:#555;font-size:12px">
              If you paid by cash, please visit the resort front desk to collect your refund.
            </p>
          </div>

          <p style="color:#888;font-size:13px;margin-top:20px;text-align:center">
            We hope to welcome you again soon. 🌴
          </p>
        </div>
        {_footer()}"""

        _send(cfg, to_email,
              f'Booking Cancelled & Refund Initiated — Paradise Resort #{rid}',
              _wrap(body))
        return True
    except Exception as e:
        print(f'[Mail Error - cancel] {e}'); return False
