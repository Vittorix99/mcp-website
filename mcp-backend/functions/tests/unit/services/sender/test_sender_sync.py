from unittest.mock import MagicMock, patch

from models.event_participant import EventParticipant
from models.membership import Membership
from services.sender.sender_sync import (
    _find_or_create_group,
    delete_subscriber_from_sender,
    sync_membership_to_sender,
    sync_newsletter_signup_to_sender,
    sync_participant_to_sender,
    unsubscribe_from_sender,
)


class TestSyncParticipantToSender:
    """Unit tests for participant -> Sender sync flow."""

    def test_skips_if_no_newsletter_consent(self):
        participant = EventParticipant(email="x@test.com", name="Mario", surname="Rossi", newsletter_consent=False)

        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            sync_participant_to_sender("p1", participant, "event-1", "Summer")

            assert not MockSvc.return_value.upsert_subscriber.called

    def test_syncs_if_newsletter_consent_true(self):
        participant = EventParticipant(email="x@test.com", name="Mario", surname="Rossi", newsletter_consent=True)

        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.list_groups.return_value = {
                "data": [
                    {"id": "g-news", "title": "Newsletter"},
                    {"id": "g-event", "title": "Participant-Summer"},
                ]
            }

            sync_participant_to_sender("p1", participant, "event-1", "Summer")

            assert svc.upsert_subscriber.called
            kwargs = svc.upsert_subscriber.call_args.kwargs
            assert kwargs["email"] == "x@test.com"

    def test_adds_to_newsletter_group(self):
        participant = EventParticipant(email="x@test.com", name="Mario", surname="Rossi", newsletter_consent=True)

        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.list_groups.return_value = {
                "data": [
                    {"id": "g-news", "title": "Newsletter"},
                    {"id": "g-event", "title": "Participant-Summer"},
                ]
            }

            sync_participant_to_sender("p1", participant, "event-1", "Summer")

            kwargs = svc.upsert_subscriber.call_args.kwargs
            assert "g-news" in kwargs["groups"]

    def test_adds_to_participant_event_group(self):
        participant = EventParticipant(email="x@test.com", name="Mario", surname="Rossi", newsletter_consent=True)

        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.list_groups.return_value = {
                "data": [
                    {"id": "g-news", "title": "Newsletter"},
                    {"id": "g-event", "title": "Participant-Summer"},
                ]
            }

            sync_participant_to_sender("p1", participant, "event-1", "Summer")

            kwargs = svc.upsert_subscriber.call_args.kwargs
            assert "g-event" in kwargs["groups"]

    def test_invalid_email_skips(self):
        participant = EventParticipant(email="", name="Mario", surname="Rossi", newsletter_consent=True)

        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.list_groups.return_value = {"data": [{"id": "g-news", "title": "Newsletter"}]}

            sync_participant_to_sender("p1", participant, "event-1", "Summer")

            assert not svc.upsert_subscriber.called

    def test_never_raises_on_service_exception(self):
        participant = EventParticipant(email="x@test.com", name="Mario", surname="Rossi", newsletter_consent=True)

        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.list_groups.return_value = {"data": [{"id": "g-news", "title": "Newsletter"}]}
            svc.upsert_subscriber.side_effect = Exception("boom")

            sync_participant_to_sender("p1", participant, "event-1", None)


class TestSyncMembershipToSender:
    """Unit tests for membership -> Sender sync flow."""

    def test_syncs_email_firstname_lastname(self):
        membership = Membership(email="member@test.com", name="Mario", surname="Rossi")

        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.list_groups.return_value = {"data": [{"id": "g-members", "title": "Memberships"}]}

            sync_membership_to_sender("m-1", membership)

            kwargs = svc.upsert_subscriber.call_args.kwargs
            assert kwargs["email"] == "member@test.com"
            assert kwargs["firstname"] == "Mario"
            assert kwargs["lastname"] == "Rossi"

    def test_adds_to_memberships_group(self):
        membership = Membership(email="member@test.com", name="Mario", surname="Rossi")

        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.list_groups.return_value = {"data": [{"id": "g-members", "title": "Memberships"}]}

            sync_membership_to_sender("m-1", membership)

            kwargs = svc.upsert_subscriber.call_args.kwargs
            assert kwargs["groups"] == ["g-members"]

    def test_invalid_email_skips(self):
        membership = Membership(email="", name="Mario", surname="Rossi")

        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.list_groups.return_value = {"data": [{"id": "g-members", "title": "Memberships"}]}

            sync_membership_to_sender("m-1", membership)

            assert not svc.upsert_subscriber.called

    def test_never_raises_on_service_exception(self):
        membership = Membership(email="member@test.com", name="Mario", surname="Rossi")

        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.list_groups.side_effect = Exception("boom")
            svc.upsert_subscriber.side_effect = Exception("boom2")

            sync_membership_to_sender("m-1", membership)


class TestSyncNewsletterSignupToSender:
    """Unit tests for newsletter signup -> Sender sync flow."""

    def test_upserts_subscriber(self):
        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.list_groups.return_value = {"data": [{"id": "g-news", "title": "Newsletter"}]}

            sync_newsletter_signup_to_sender("x@test.com", "Mario Rossi")

            kwargs = svc.upsert_subscriber.call_args.kwargs
            assert kwargs["email"] == "x@test.com"

    def test_adds_to_newsletter_group(self):
        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.list_groups.return_value = {"data": [{"id": "g-news", "title": "Newsletter"}]}

            sync_newsletter_signup_to_sender("x@test.com", "Mario Rossi")

            kwargs = svc.upsert_subscriber.call_args.kwargs
            assert kwargs["groups"] == ["g-news"]

    def test_name_split_into_firstname(self):
        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.list_groups.return_value = {"data": [{"id": "g-news", "title": "Newsletter"}]}

            sync_newsletter_signup_to_sender("x@test.com", "Mario Rossi")

            kwargs = svc.upsert_subscriber.call_args.kwargs
            assert kwargs["firstname"] == "Mario"
            assert kwargs["lastname"] is None

    def test_never_raises(self):
        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.list_groups.side_effect = Exception("boom")
            svc.upsert_subscriber.side_effect = Exception("boom2")

            sync_newsletter_signup_to_sender("x@test.com", "Mario Rossi")


class TestUnsubscribeFromSender:
    """Unit tests for soft unsubscribe sync."""

    def test_calls_update_with_unsubscribed_status(self):
        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value

            unsubscribe_from_sender("X@TEST.COM")

            svc.update_subscriber.assert_called_once_with("x@test.com", {"subscriber_status": "UNSUBSCRIBED"})

    def test_never_raises(self):
        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.update_subscriber.side_effect = Exception("boom")

            unsubscribe_from_sender("x@test.com")


class TestDeleteSubscriberFromSender:
    """Unit tests for hard delete sync."""

    def test_calls_delete_subscriber(self):
        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value

            delete_subscriber_from_sender("X@TEST.COM")

            svc.delete_subscriber.assert_called_once_with("x@test.com")

    def test_never_raises(self):
        with patch("services.sender.sender_sync.SenderService") as MockSvc:
            svc = MockSvc.return_value
            svc.delete_subscriber.side_effect = Exception("boom")

            delete_subscriber_from_sender("x@test.com")


class TestFindOrCreateGroup:
    """Unit tests for _find_or_create_group helper in sync layer."""

    def test_returns_id_of_existing_group(self):
        svc = MagicMock()
        svc.list_groups.return_value = {"data": [{"id": "g1", "title": "Newsletter"}]}

        group_id = _find_or_create_group(svc, "Newsletter")

        assert group_id == "g1"

    def test_creates_new_group_when_not_found(self):
        svc = MagicMock()
        svc.list_groups.return_value = {"data": []}
        svc.create_group.return_value = {"data": {"id": "g-new"}}

        group_id = _find_or_create_group(svc, "Newsletter")

        assert group_id == "g-new"
        svc.create_group.assert_called_once_with("Newsletter")

    def test_returns_none_on_list_failure(self):
        svc = MagicMock()
        svc.list_groups.return_value = None
        svc.create_group.return_value = None

        group_id = _find_or_create_group(svc, "Newsletter")

        assert group_id is None

    def test_returns_none_on_create_failure(self):
        svc = MagicMock()
        svc.list_groups.return_value = {"data": []}
        svc.create_group.return_value = None

        group_id = _find_or_create_group(svc, "Newsletter")

        assert group_id is None
