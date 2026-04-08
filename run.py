import os

# ── Load .env file automatically (no extra packages needed) ────
def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip blank lines and comments
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, _, value = line.partition('=')
            key   = key.strip()
            value = value.strip()
            # Remove surrounding quotes if present
            if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
                value = value[1:-1]
            # Only set if not already set by OS environment
            if key and key not in os.environ:
                os.environ[key] = value

_load_env()

from app import create_app
from app.models.resort_model import init_db

app = create_app()

if __name__ == '__main__':
    init_db()

    # Show email config status on startup
    smtp_user   = os.environ.get('SMTP_USER', '')
    smtp_server = os.environ.get('SMTP_SERVER', '')
    email_ok    = bool(smtp_server and smtp_user and os.environ.get('SMTP_PASS',''))

    print("=" * 52)
    print("  Paradise Resort running on http://0.0.0.0:5000")
    print("  Access via: http://localhost:5000")
    print(f"  Email: {'✅ Configured (' + smtp_user + ')' if email_ok else '⚠️  Not configured (edit .env file)'}")
    print("  Default login: admin / admin123")
    print("=" * 52)

    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
