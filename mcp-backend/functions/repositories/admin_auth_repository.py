from typing import Optional

from firebase_admin import auth

from errors.service_errors import ConflictError, NotFoundError, ServiceError, ValidationError


class AdminAuthRepository:
    def create_admin_user(self, email: str, password: str, display_name: str = "") -> str:
        try:
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=True,
            )
            return user.uid
        except auth.EmailAlreadyExistsError as exc:
            raise ConflictError("Email already exists") from exc
        except ValueError as exc:
            raise ValidationError(f"Invalid argument: {str(exc)}") from exc
        except Exception as exc:
            raise ServiceError("An error occurred while creating the admin user") from exc

    def set_admin_claims(self, admin_id: str) -> None:
        try:
            auth.set_custom_user_claims(admin_id, {"admin": True})
        except Exception as exc:
            raise ServiceError("An error occurred while assigning admin permissions") from exc

    def update_admin_user(
        self,
        admin_id: str,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> None:
        update_payload = {}
        if email is not None:
            update_payload["email"] = email
        if display_name is not None:
            update_payload["display_name"] = display_name
        if not update_payload:
            return
        try:
            auth.update_user(admin_id, **update_payload)
        except auth.UserNotFoundError as exc:
            raise NotFoundError("Admin user not found") from exc
        except ValueError as exc:
            raise ValidationError(f"Invalid argument: {str(exc)}") from exc
        except Exception as exc:
            raise ServiceError("An error occurred while updating the admin user") from exc

    def delete_admin_user(self, admin_id: str) -> None:
        try:
            auth.delete_user(admin_id)
        except auth.UserNotFoundError as exc:
            raise NotFoundError("Admin user not found") from exc
        except Exception as exc:
            raise ServiceError("An error occurred while deleting the admin user") from exc
