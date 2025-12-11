from firebase_admin import auth
from functools import wraps
from firebase_functions import https_fn
from config.firebase_config import db


def verify_admin_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        if not decoded_token.get("admin", False):
            raise ValueError("User is not an admin")
        return decoded_token
    except Exception as e:
        raise ValueError(f"Invalid admin token: {str(e)}")


def require_admin(handler):
    @wraps(handler)
    def decorated_function(req: https_fn.Request, *args, **kwargs):
        if not req.headers.get("Authorization"):
            return https_fn.Response("No authorization token provided", status=401)

        try:
            auth_header = req.headers.get("Authorization")
            if not auth_header.startswith("Bearer "):
                raise ValueError("Invalid authorization header format")

            id_token = auth_header.split("Bearer ")[1]
            decoded_token = verify_admin_token(id_token)
            req.admin_token = decoded_token
            return handler(req, *args, **kwargs)
        except ValueError as e:
            return https_fn.Response({"error": str(e)}, status=401)
        except Exception as e:
            return https_fn.Response({"error": str(e)}, status=500)

    return decorated_function


def verify_admin_service(req: https_fn.CallableRequest) -> dict:
    """Handles checking if a user is an admin"""
    if not req.auth:
        return {"isAdmin": False}

    try:
        user_ref = db.collection("users").document(req.auth.uid)
        user_data = user_ref.get().to_dict() or {}

        return {
            "isAdmin": user_data.get("isAdmin", False),
            "role": user_data.get("role", "user"),
        }

    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error verifying admin status: {str(e)}",
        )
