import pytest


@pytest.mark.integration
def test_documents_service_generates_membership_card(documents_service, membership_dto):
    """Creates a membership card PDF and stores it."""
    if documents_service.storage is None:
        pytest.skip("Storage bucket not configured for document generation")
    doc = documents_service.create_membership_card("mem-test", membership_dto)
    assert doc.storage_path
    assert doc.public_url
    blob = documents_service.storage.blob(doc.storage_path)
    assert blob.exists()
    blob.delete()


@pytest.mark.integration
def test_documents_service_generates_ticket(documents_service, event_dto, membership_dto):
    """Creates a ticket PDF and stores it."""
    if documents_service.storage is None:
        pytest.skip("Storage bucket not configured for document generation")
    participant_payload = membership_dto.to_payload()
    participant_payload["name"] = membership_dto.name or "Mario"
    participant_payload["surname"] = membership_dto.surname or "Rossi"
    doc = documents_service.create_ticket_document(
        participant_payload,
        event_dto.to_payload(),
        storage_path="tickets/integration/test_ticket.pdf",
    )
    assert doc.storage_path
    assert doc.public_url
    blob = documents_service.storage.blob(doc.storage_path)
    assert blob.exists()
    blob.delete()
