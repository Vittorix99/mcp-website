import pytest

from tests.integration.mailer_lite.conftest import _extract_id

from tests.integration.mailer_lite.conftest import _extract_id, _extract_list_data


@pytest.mark.integration
def test_groups_crud_service(mailerlite_clients, unique_group_name):
    """Verify groups CRUD operations via the service client."""
    groups_client = mailerlite_clients["groups"]

    created = groups_client.create(unique_group_name)
    group_id = _extract_id(created)
    assert group_id is not None

    listed = groups_client.list(params={"filter": {"name": unique_group_name}})
    data = _extract_list_data(listed)
    assert any(str(item.get("id")) == str(group_id) for item in data)

    groups_client.delete(group_id)


@pytest.mark.integration
def test_group_assign_unassign_service(mailerlite_clients, unique_group_name, unique_email):
    """Verify assigning/unassigning subscribers via the service client."""
    groups_client = mailerlite_clients["groups"]
    subscribers_client = mailerlite_clients["subscribers"]

    group_id = None
    subscriber_id = None
    try:
        created_group = groups_client.create(unique_group_name)
        group_id = _extract_id(created_group)
        assert group_id is not None

        created_sub = subscribers_client.create(
            unique_email,
            {"fields": {"birthdate": "01-01-1999", "phone": "+390000000000"}},
        )
        subscriber_id = _extract_id(created_sub)
        assert subscriber_id is not None

        groups_client.assign_subscriber(subscriber_id, group_id)
        groups_client.unassign_subscriber(subscriber_id, group_id)
    finally:
        if subscriber_id is not None:
            subscribers_client.delete_subscriber(subscriber_id)
        if group_id is not None:
            groups_client.delete(group_id)
