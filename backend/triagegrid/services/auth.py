import hashlib
from ..storage import connect, uid, now, new_session

DEMO_ACCOUNTS = {
    "demo@triagegrid.in": {
        "password": "TG@demo2024",
        "name": "Aarav Sharma",
        "phone": "+91 98765 43210",
    },
    "test@carecompass.in": {
        "password": "Care@1234",
        "name": "Priya Nair",
        "phone": "+91 91234 56789",
    },
}

DEMO_OTP = "112233"

def _hash_pass(password: str) -> str:
    return hashlib.sha256(f"triagegrid_salt_{password}".encode()).hexdigest()

def seed_demo_users():
    with connect() as db:
        for email, u in DEMO_ACCOUNTS.items():
            db.execute(
                """
                INSERT OR IGNORE INTO users (id, name, email, phone, password_hash, created)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (uid("U"), u["name"], email, u["phone"], _hash_pass(u["password"]), now()),
            )

seed_demo_users()

def authenticate_user(email: str, password: str):
    email = email.strip().lower()
    # Check default demo users first
    if email in DEMO_ACCOUNTS and DEMO_ACCOUNTS[email]["password"] == password:
        token = new_session()
        return {
            "name": DEMO_ACCOUNTS[email]["name"],
            "email": email,
            "phone": DEMO_ACCOUNTS[email]["phone"],
            "token": token,
        }

    # Check database
    hashed = _hash_pass(password)
    with connect() as db:
        row = db.execute(
            "SELECT name, email, phone FROM users WHERE email = ? AND password_hash = ?",
            (email, hashed),
        ).fetchone()
        if row:
            token = new_session()
            return {
                "name": row["name"],
                "email": row["email"],
                "phone": row["phone"] or "",
                "token": token,
            }
    return None

def register_user(name: str, email: str, phone: str, password: str):
    email = email.strip().lower()
    hashed = _hash_pass(password)
    with connect() as db:
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            db.execute(
                "UPDATE users SET name = ?, phone = ?, password_hash = ? WHERE email = ?",
                (name.strip(), phone.strip(), hashed, email),
            )
        else:
            db.execute(
                "INSERT INTO users (id, name, email, phone, password_hash, created) VALUES (?, ?, ?, ?, ?, ?)",
                (uid("U"), name.strip(), email, phone.strip(), hashed, now()),
            )
    token = new_session()
    return {
        "name": name.strip(),
        "email": email,
        "phone": phone.strip(),
        "token": token,
    }

def verify_otp(email: str, otp: str, name: str | None = None, phone: str | None = None, password: str | None = None):
    email = email.strip().lower()
    if otp.strip() != DEMO_OTP:
        return None

    if name and password:
        return register_user(name, email, phone or "", password)

    with connect() as db:
        row = db.execute("SELECT name, email, phone FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            token = new_session()
            return {
                "name": row["name"],
                "email": row["email"],
                "phone": row["phone"] or "",
                "token": token,
            }
        else:
            token = new_session()
            return {
                "name": name or (DEMO_ACCOUNTS.get(email, {}).get("name", "User")),
                "email": email,
                "phone": phone or (DEMO_ACCOUNTS.get(email, {}).get("phone", "")),
                "token": token,
            }
