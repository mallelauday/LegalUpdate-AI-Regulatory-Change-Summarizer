import hashlib
import uuid
import logging
from flask import Blueprint, request
from database.firebase_db import FirestoreManager, get_utc_now
from utils.helpers import api_response, generate_jwt_token, token_required, roles_required
import firebase_admin
from firebase_admin import auth as firebase_auth

logger = logging.getLogger("legalupdate.auth")
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login endpoint. Supports:
    1. Firebase Client ID Token: {"id_token": "..."}
    2. Local Email/Password: {"email": "...", "password": "..."}
    """
    data = request.get_json() or {}
    db = FirestoreManager.get_db()

    # Case 1: Firebase ID Token Login
    id_token = data.get("id_token")
    if id_token and FirestoreManager.is_live_firebase():
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            uid = decoded_token.get("uid")
            email = decoded_token.get("email", "")

            # Look up or create user record in Firestore
            user_doc = db.collection("users").document(uid).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
            else:
                user_data = {
                    "uid": uid,
                    "email": email,
                    "display_name": decoded_token.get("name") or email.split("@")[0],
                    "role": "reviewer",  # Default new user role
                    "department": "Legal Compliance",
                    "created_at": get_utc_now(),
                    "last_login_at": get_utc_now()
                }
                db.collection("users").document(uid).set(user_data)

            # Generate app session JWT
            token = generate_jwt_token(
                user_id=uid,
                email=user_data.get("email"),
                role=user_data.get("role", "reviewer"),
                name=user_data.get("display_name", "")
            )

            return api_response(
                data={"token": token, "user": user_data},
                message="Firebase authentication successful."
            )
        except Exception as e:
            logger.error("Firebase ID Token verification error: %s", e)
            return api_response(error=f"Firebase authentication failed: {str(e)}", status_code=401)

    # Case 2: Email & Password
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return api_response(error="Email and password are required.", status_code=400)

    # Find user in Firestore users collection
    user_match = None
    for doc in db.collection("users").where("email", "==", email).limit(1).stream():
        user_match = doc.to_dict()
        break

    if not user_match:
        return api_response(error="Invalid email or password.", status_code=401)

    hashed_pw = hash_password(password)
    stored_hash = user_match.get("password_hash")

    if stored_hash and stored_hash != hashed_pw:
        return api_response(error="Invalid email or password.", status_code=401)

    # Update last login
    uid = user_match.get("uid", user_match.get("id"))
    db.collection("users").document(uid).update({"last_login_at": get_utc_now()})

    token = generate_jwt_token(
        user_id=uid,
        email=user_match.get("email"),
        role=user_match.get("role", "reviewer"),
        name=user_match.get("display_name", user_match.get("name", "User"))
    )

    clean_user = dict(user_match)
    clean_user.pop("password_hash", None)

    return api_response(
        data={"token": token, "user": clean_user},
        message="Login successful."
    )

@auth_bp.route("/register", methods=["POST"])
def register():
    """Create a new user account."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    name = data.get("name", "").strip() or email.split("@")[0]
    department = data.get("department", "Corporate Legal & Compliance")
    role = data.get("role", "reviewer")

    if not email or not password:
        return api_response(error="Email and password are required.", status_code=400)

    db = FirestoreManager.get_db()
    for doc in db.collection("users").where("email", "==", email).limit(1).stream():
        return api_response(error="User with this email already exists.", status_code=409)

    uid = f"usr-{uuid.uuid4().hex[:8]}"
    new_user = {
        "uid": uid,
        "email": email,
        "display_name": name,
        "role": role if role in ("admin", "reviewer", "viewer") else "reviewer",
        "department": department,
        "password_hash": hash_password(password),
        "created_at": get_utc_now(),
        "last_login_at": get_utc_now()
    }
    db.collection("users").document(uid).set(new_user)

    token = generate_jwt_token(
        user_id=uid,
        email=email,
        role=new_user["role"],
        name=name
    )

    clean_user = dict(new_user)
    clean_user.pop("password_hash", None)

    return api_response(
        data={"token": token, "user": clean_user},
        message="Account created successfully.",
        status_code=201
    )

@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user():
    """Return currently authenticated user information."""
    curr = request.current_user
    db = FirestoreManager.get_db()
    doc = db.collection("users").document(curr["sub"]).get()
    if not doc.exists:
        return api_response(data=curr, message="User profile retrieved.")

    user_data = doc.to_dict()
    user_data.pop("password_hash", None)
    return api_response(data=user_data, message="User profile retrieved.")

@auth_bp.route("/users", methods=["GET"])
@token_required
@roles_required("admin")
def list_users():
    """List all registered users (Admin only)."""
    db = FirestoreManager.get_db()
    users = []
    for doc in db.collection("users").stream():
        u = doc.to_dict()
        u.pop("password_hash", None)
        users.append(u)
    return api_response(data=users, message="Users list retrieved.")

@auth_bp.route("/users/<uid>/role", methods=["PUT"])
@token_required
@roles_required("admin")
def update_user_role(uid):
    """Change a user's role (Admin only)."""
    data = request.get_json() or {}
    new_role = data.get("role")
    if new_role not in ("admin", "reviewer", "viewer"):
        return api_response(error="Invalid role. Must be 'admin', 'reviewer', or 'viewer'.", status_code=400)

    db = FirestoreManager.get_db()
    doc_ref = db.collection("users").document(uid)
    if not doc_ref.get().exists:
        return api_response(error=f"User {uid} not found.", status_code=404)

    doc_ref.update({"role": new_role})
    return api_response(message=f"User role updated to '{new_role}'.")

