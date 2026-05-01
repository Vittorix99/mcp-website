from __future__ import annotations

from google.cloud import firestore

from dto.admin import AdminActionResponseDTO, AdminListResponseDTO, AdminResponseDTO, CreateAdminRequestDTO, UpdateAdminRequestDTO
from errors.service_errors import NotFoundError, ServiceError
from interfaces.repositories import AdminAuthRepositoryProtocol, AdminRepositoryProtocol
from repositories.admin_auth_repository import AdminAuthRepository
from repositories.admin_repository import AdminRepository


class AdminService:
    def __init__(
        self,
        admin_repository: AdminRepositoryProtocol | None = None,
        admin_auth_repository: AdminAuthRepositoryProtocol | None = None,
    ):
        self.admin_repository = admin_repository or AdminRepository()
        self.admin_auth_repository = admin_auth_repository or AdminAuthRepository()

    def create(self, dto: CreateAdminRequestDTO, created_by: str) -> AdminActionResponseDTO:
        admin_id = ""
        try:
            admin_id = self.admin_auth_repository.create_admin_user(
                email=str(dto.email),
                password=dto.password,
                display_name=dto.display_name,
            )
            self.admin_auth_repository.set_admin_claims(admin_id)

            admin_user = dto.to_model(created_by=created_by)
            admin_user.created_at = firestore.SERVER_TIMESTAMP
            self.admin_repository.create_with_id(admin_id, admin_user)

            return AdminActionResponseDTO(
                message="Admin user created successfully",
                uid=admin_id,
            )
        except Exception as exc:
            if admin_id:
                try:
                    self.admin_auth_repository.delete_admin_user(admin_id)
                except Exception:
                    pass
            if isinstance(exc, ServiceError):
                raise
            raise ServiceError("An error occurred while creating the admin user") from exc

    def get_all(self) -> AdminListResponseDTO:
        return AdminListResponseDTO.from_models(self.admin_repository.list_models())

    def get_by_id(self, admin_id: str) -> AdminResponseDTO:
        admin_user = self.admin_repository.get(admin_id)
        if not admin_user:
            raise NotFoundError("Admin user not found")
        return AdminResponseDTO.from_model(admin_user)

    def update(self, dto: UpdateAdminRequestDTO) -> AdminActionResponseDTO:
        admin_user = self.admin_repository.get(dto.uid)
        if not admin_user:
            raise NotFoundError("Admin user not found")

        self.admin_auth_repository.update_admin_user(
            dto.uid,
            email=str(dto.email) if dto.email is not None else None,
            display_name=dto.display_name,
        )
        updated_admin_user = dto.apply_to_model(admin_user)
        self.admin_repository.update_from_model(dto.uid, updated_admin_user)

        return AdminActionResponseDTO(
            message="Admin user updated successfully",
            uid=dto.uid,
        )

    def delete(self, admin_id: str) -> AdminActionResponseDTO:
        admin_user = self.admin_repository.get(admin_id)
        if not admin_user:
            raise NotFoundError("Admin user not found")

        self.admin_auth_repository.delete_admin_user(admin_id)
        self.admin_repository.delete(admin_id)

        return AdminActionResponseDTO(
            message="Admin user deleted successfully",
            uid=admin_id,
        )
