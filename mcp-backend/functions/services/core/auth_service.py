from firebase_admin import auth
from functools import wraps
from firebase_functions import https_fn
from typing import Optional

from interfaces.repositories import UserRepositoryProtocol
from repositories.user_repository import UserRepository


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


def verify_admin_service(
    req: https_fn.CallableRequest,
    user_repository: Optional[UserRepositoryProtocol] = None,
) -> dict:
    """Handles checking if a user is an admin"""
    if not req.auth:
        return {"isAdmin": False}

    try:
        repository = user_repository or UserRepository()
        user_profile = repository.get_by_id(req.auth.uid)

        return {
            "isAdmin": bool(user_profile.is_admin) if user_profile else False,
            "role": user_profile.role if user_profile else "user",
        }

    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error verifying admin status: {str(e)}",
        )
