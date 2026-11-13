import hashlib
import difflib
import datetime
import jwt
from functools import wraps
from flask import request, jsonify
from bson import ObjectId
from config import Config

def get_utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def generate_content_hash(text: str) -> str:
    """Generate SHA-256 hash for normalized content to detect modifications."""
    if not text:
        return ""
    # Normalize whitespace
    normalized = " ".join(text.split()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def compute_text_diff(old_text: str, new_text: str):
    """Compute unified diff and change metrics between two document versions."""
    if not old_text:
        return {
            "has_changes": True,
            "additions": len(new_text.splitlines()),
            "deletions": 0,
            "diff_lines": ["+ " + line for line in new_text.splitlines()[:50]]
        }
    
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    
    diff = list(difflib.unified_diff(
        old_lines, new_lines,
        fromfile="Previous Version",
        tofile="Current Version",
        lineterm=""
    ))
    
    additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    
    return {
        "has_changes": additions > 0 or deletions > 0,
        "additions": additions,
        "deletions": deletions,
        "diff_lines": diff[:200]  # Cap for responsive UI
    }

def serialize_mongo(obj):
    """Recursively convert MongoDB ObjectId and datetime objects to JSON-serializable types."""
    if isinstance(obj, list):
        return [serialize_mongo(item) for item in obj]
    elif isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            if k == "_id":
                new_dict["id"] = str(v)
            else:
                new_dict[k] = serialize_mongo(v)
        return new_dict
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    return obj

def api_response(data=None, message="Success", status_code=200, error=None, meta=None):
    """Standardized JSON response payload."""
    payload = {
        "success": error is None and status_code < 400,
        "message": message,
        "data": serialize_mongo(data),
        "error": error
    }
    if meta is not None:
        payload["meta"] = meta
    return jsonify(payload), status_code

def generate_jwt_token(user_id: str, email: str, role: str, name: str) -> str:
    """Generate JWT auth token valid for 7 days."""
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "name": name,
        "exp": exp
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")

def decode_jwt_token(token: str):
    """Decode and validate JWT token."""
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not auth_header.startswith("Bearer "):
            return api_response(error="Authorization token missing or invalid", status_code=401)
        
        token = auth_header.split(" ")[1]
        decoded = decode_jwt_token(token)
        if not decoded:
            return api_response(error="Session expired or token invalid. Please log in again.", status_code=401)
        
        request.current_user = decoded
        return f(*args, **kwargs)
    return decorated

def roles_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(request, "current_user", None)
            if not user or user.get("role") not in allowed_roles:
                return api_response(
                    error=f"Access denied. Required roles: {', '.join(allowed_roles)}",
                    status_code=403
                )
            return f(*args, **kwargs)
        return decorated
    return decorator

