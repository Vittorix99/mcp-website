# API Contract Inventory — 2026-10-24

> Status: observed current state; proposed as discovery evidence, not an approved target contract.

## Scope and method

- 134 decorated HTTP/callable functions found under `mcp-backend/functions/api`.
- 128 are imported by `mcp-backend/functions/main.py`; 6 are defined but not exported.
- 130 unique frontend route slugs found in `mcp-website/config/endpoints.js`.
- Method, access wrapper, DTO validation, export status, frontend mapping, coarse consumer counts, test references, and notable dependencies were derived statically.
- Consumer and test counts are search-based signals, not proof of runtime coverage. Complete response schemas, error sets, datastore calls, and latency require executable contract instrumentation.

## Contract gaps requiring resolution

- Frontend-only slugs (no decorated backend function): admin_upload_event_photo, get_all_questions, newsletter_participants, signup_request.
- Backend functions absent from the frontend route map: create_admin, delete_admin, entrance_validate, get_admin_by_id, get_all_admins, sender_webhook, update_admin, verify_admin.
- Defined but not exported by `main.py`: create_admin, get_all_admins, get_admin_by_id, update_admin, delete_admin, verify_admin.
- No OpenAPI document, JSON Schema contract, generated client, or contract-test gate was found.
- The proxy accepts a backend function path dynamically, so the route map is a convention rather than an enforced allowlist.

## Endpoint inventory

| Endpoint | Method | Access | Exported | Frontend key | Consumer files | Validation | Test refs | Notable deps | Source |
|---|---|---|---:|---|---:|---|---:|---|---|
| `admin_create_discount_code` | POST | admin claim | yes | createDiscountCode | 14 | AdminCreateDiscountCodeRequestDTO | 0 | internal | `mcp-backend/functions/api/admin/discount_code_api.py:22` |
| `admin_create_event` | POST | admin claim | yes | createEvent | 23 | CreateEventRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/events_api.py:28` |
| `admin_create_radio_episode` | POST | admin claim | yes | createEpisode | 11 | CreateRadioEpisodeRequestDTO | 3 | internal | `mcp-backend/functions/api/admin/radio_episodes_api.py:31` |
| `admin_create_radio_season` | POST | admin claim | yes | createSeason | 11 | CreateRadioSeasonRequestDTO | 3 | internal | `mcp-backend/functions/api/admin/radio_seasons_api.py:30` |
| `admin_delete_event` | DELETE | admin claim | yes | deleteEvent | 20 | EventDeleteRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/events_api.py:62` |
| `admin_delete_newsletter_signup` | DELETE | admin claim | yes | delete | 49 | NewsletterDeleteQueryDTO | 1 | internal | `mcp-backend/functions/api/admin/newsletter_api.py:52` |
| `admin_delete_radio_episode` | DELETE | admin claim | yes | deleteEpisode | 11 | inline/none | 3 | internal | `mcp-backend/functions/api/admin/radio_episodes_api.py:70` |
| `admin_delete_radio_season` | DELETE | admin claim | yes | deleteSeason | 11 | inline/none | 3 | internal | `mcp-backend/functions/api/admin/radio_seasons_api.py:69` |
| `admin_disable_discount_code` | DELETE | admin claim | yes | disableDiscountCode | 15 | DiscountCodeIdRequestDTO | 0 | internal | `mcp-backend/functions/api/admin/discount_code_api.py:76` |
| `admin_get_age_distribution` | GET | admin claim | yes | getAgeDistribution | 13 | EventAnalyticsQueryDTO | 0 | internal | `mcp-backend/functions/api/admin/stats_api.py:158` |
| `admin_get_all_events` | GET | admin claim | yes | getAllEvents | 22 | inline/none | 2 | internal | `mcp-backend/functions/api/admin/events_api.py:79` |
| `admin_get_analytics_event_snapshot` | GET | admin claim | yes | getAnalyticsEventSnapshot | 10 | EventSnapshotQueryDTO | 1 | internal | `mcp-backend/functions/api/admin/stats_api.py:42` |
| `admin_get_analytics_events_index` | GET | admin claim | yes | getAnalyticsEventsIndex | 10 | inline/none | 1 | internal | `mcp-backend/functions/api/admin/stats_api.py:65` |
| `admin_get_analytics_global_snapshot` | GET | admin claim | yes | getAnalyticsGlobalSnapshot | 13 | inline/none | 1 | internal | `mcp-backend/functions/api/admin/stats_api.py:55` |
| `admin_get_audience_retention` | GET | admin claim | yes | getAudienceRetention | 13 | EventAnalyticsQueryDTO | 0 | internal | `mcp-backend/functions/api/admin/stats_api.py:106` |
| `admin_get_dashboard_kpis` | GET | admin claim | yes | getDashboardKpis | 10 | inline/none | 0 | internal | `mcp-backend/functions/api/admin/stats_api.py:184` |
| `admin_get_dashboard_snapshot` | GET | admin claim | yes | getDashboardSnapshot | 13 | inline/none | 1 | internal | `mcp-backend/functions/api/admin/stats_api.py:32` |
| `admin_get_discount_code` | GET | admin claim | yes | getDiscountCode | 14 | DiscountCodeIdRequestDTO | 0 | internal | `mcp-backend/functions/api/admin/discount_code_api.py:49` |
| `admin_get_entrance_flow` | GET | admin claim | yes | getEntranceFlow | 13 | EventAnalyticsQueryDTO | 2 | internal | `mcp-backend/functions/api/admin/stats_api.py:75` |
| `admin_get_event_by_id` | GET | admin claim | yes | getEventById | 23 | EventLookupQueryDTO | 2 | internal | `mcp-backend/functions/api/admin/events_api.py:92` |
| `admin_get_event_funnel` | GET | admin claim | yes | getEventFunnel | 13 | EventAnalyticsQueryDTO | 0 | internal | `mcp-backend/functions/api/admin/stats_api.py:132` |
| `admin_get_event_guide` | GET | admin claim | yes | getGuide | 11 | EventGuideQueryDTO | 0 | internal | `mcp-backend/functions/api/admin/events_api.py:108` |
| `admin_get_event_location` | GET | admin claim | yes | getLocation | 11 | GetEventLocationQueryDTO | 1 | internal | `mcp-backend/functions/api/admin/location_api.py:22` |
| `admin_get_gender_distribution` | GET | admin claim | yes | getGenderDistribution | 13 | EventAnalyticsQueryDTO | 0 | internal | `mcp-backend/functions/api/admin/stats_api.py:145` |
| `admin_get_general_stats` | GET | admin claim | yes | getGeneralStats | 10 | inline/none | 2 | internal | `mcp-backend/functions/api/admin/stats_api.py:22` |
| `admin_get_membership_trend` | GET | admin claim | yes | getMembershipTrend | 13 | MembershipTrendQueryDTO | 0 | internal | `mcp-backend/functions/api/admin/stats_api.py:171` |
| `admin_get_newsletter_consents` | GET | admin claim | yes | getConsents | 11 | inline/none | 1 | internal | `mcp-backend/functions/api/admin/newsletter_api.py:66` |
| `admin_get_newsletter_signups` | GET | admin claim | yes | getSignups | 11 | NewsletterLookupQueryDTO | 1 | internal | `mcp-backend/functions/api/admin/newsletter_api.py:21` |
| `admin_get_radio_episode` | GET | admin claim | yes | getEpisode | 12 | inline/none | 2 | internal | `mcp-backend/functions/api/admin/radio_episodes_api.py:44` |
| `admin_get_radio_episodes` | GET | admin claim | yes | getEpisodes | 11 | inline/none | 2 | internal | `mcp-backend/functions/api/admin/radio_episodes_api.py:21` |
| `admin_get_radio_season` | GET | admin claim | yes | getSeason | 11 | inline/none | 2 | internal | `mcp-backend/functions/api/admin/radio_seasons_api.py:43` |
| `admin_get_radio_seasons` | GET | admin claim | yes | getSeasons | 15 | inline/none | 2 | internal | `mcp-backend/functions/api/admin/radio_seasons_api.py:20` |
| `admin_get_revenue_breakdown` | GET | admin claim | yes | getRevenueBreakdown | 13 | EventAnalyticsQueryDTO | 0 | internal | `mcp-backend/functions/api/admin/stats_api.py:119` |
| `admin_get_sales_over_time` | GET | admin claim | yes | getSalesOverTime | 13 | EventAnalyticsQueryDTO | 0 | internal | `mcp-backend/functions/api/admin/stats_api.py:93` |
| `admin_list_discount_codes` | GET | admin claim | yes | listDiscountCodes | 15 | DiscountCodeEventRequestDTO | 0 | internal | `mcp-backend/functions/api/admin/discount_code_api.py:36` |
| `admin_publish_radio_episode` | PATCH | admin claim | yes | publishEpisode | 11 | RadioEpisodeIdRequestDTO | 3 | internal | `mcp-backend/functions/api/admin/radio_episodes_api.py:84` |
| `admin_rebuild_analytics` | POST | admin claim | yes | rebuildAnalytics | 13 | RebuildAnalyticsRequestDTO | 3 | internal | `mcp-backend/functions/api/admin/stats_api.py:194` |
| `admin_sender_campaign_copy` | POST | admin claim | yes | campaignCopy | 17 | CampaignIdRequestDTO | 1 | Sender.net | `mcp-backend/functions/api/admin/sender/campaigns_api.py:128` |
| `admin_sender_campaign_schedule` | POST/DELETE | admin claim | yes | campaignSchedule | 17 | CampaignIdRequestDTO, ScheduleCampaignRequestDTO | 2 | Sender.net | `mcp-backend/functions/api/admin/sender/campaigns_api.py:101` |
| `admin_sender_campaign_send` | POST | admin claim | yes | campaignSend | 17 | CampaignIdRequestDTO | 2 | Sender.net | `mcp-backend/functions/api/admin/sender/campaigns_api.py:86` |
| `admin_sender_campaign_stats` | GET | admin claim | yes | campaignStats | 17 | CampaignStatsQueryDTO | 2 | Sender.net | `mcp-backend/functions/api/admin/sender/campaigns_api.py:140` |
| `admin_sender_campaigns` | GET/POST/PUT/DELETE | admin claim | yes | campaigns | 43 | CampaignIdRequestDTO, CampaignQueryDTO, CreateCampaignRequestDTO, UpdateCampaignRequestDTO | 2 | Sender.net | `mcp-backend/functions/api/admin/sender/campaigns_api.py:22` |
| `admin_sender_fields` | GET/POST/DELETE | admin claim | yes | fields | 42 | CreateFieldRequestDTO, FieldDeleteRequestDTO | 1 | Sender.net | `mcp-backend/functions/api/admin/sender/fields_api.py:15` |
| `admin_sender_group_subscribers` | GET | admin claim | yes | groupSubscribers | 17 | GroupSubscribersQueryDTO | 1 | Sender.net | `mcp-backend/functions/api/admin/sender/groups_api.py:59` |
| `admin_sender_groups` | GET/POST/PUT/DELETE | admin claim | yes | groups | 45 | CreateGroupRequestDTO, GroupDeleteRequestDTO, UpdateGroupRequestDTO | 1 | Sender.net | `mcp-backend/functions/api/admin/sender/groups_api.py:20` |
| `admin_sender_segment_subscribers` | GET | admin claim | yes | segmentSubscribers | 17 | SegmentSubscribersQueryDTO | 1 | Sender.net | `mcp-backend/functions/api/admin/sender/segments_api.py:43` |
| `admin_sender_segments` | GET/DELETE | admin claim | yes | segments | 38 | SegmentDeleteRequestDTO, SegmentQueryDTO | 1 | Sender.net | `mcp-backend/functions/api/admin/sender/segments_api.py:15` |
| `admin_sender_subscriber_events` | GET | admin claim | yes | subscriberEvents | 17 | SubscriberEventQueryDTO | 1 | Sender.net | `mcp-backend/functions/api/admin/sender/subscribers_api.py:108` |
| `admin_sender_subscriber_groups` | POST/DELETE | admin claim | yes | subscriberGroups | 17 | SubscriberGroupRequestDTO | 1 | Sender.net | `mcp-backend/functions/api/admin/sender/subscribers_api.py:85` |
| `admin_sender_subscribers` | GET/POST/PUT/DELETE | admin claim | yes | subscribers | 42 | DeleteSubscriberRequestDTO, SubscriberQueryDTO, UpdateSubscriberRequestDTO, UpsertSubscriberRequestDTO | 1 | Sender.net | `mcp-backend/functions/api/admin/sender/subscribers_api.py:23` |
| `admin_sender_transactional` | GET/POST/DELETE | admin claim | yes | transactional | 33 | CampaignIdRequestDTO, CreateTransactionalCampaignRequestDTO | 1 | Sender.net | `mcp-backend/functions/api/admin/sender/transactional_api.py:20` |
| `admin_sender_transactional_send` | POST | admin claim | yes | transactionalSend | 17 | SendTransactionalCampaignRequestDTO | 1 | Sender.net | `mcp-backend/functions/api/admin/sender/transactional_api.py:63` |
| `admin_toggle_guide_published` | PATCH | admin claim | yes | toggleGuidePublished | 11 | ToggleGuidePublishedRequestDTO | 0 | internal | `mcp-backend/functions/api/admin/events_api.py:138` |
| `admin_toggle_location_published` | PATCH | admin claim | yes | toggleLocationPublished | 11 | ToggleLocationPublishedRequestDTO | 1 | internal | `mcp-backend/functions/api/admin/location_api.py:52` |
| `admin_unpublish_radio_episode` | PATCH | admin claim | yes | unpublishEpisode | 11 | RadioEpisodeIdRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/radio_episodes_api.py:97` |
| `admin_update_discount_code` | PATCH | admin claim | yes | updateDiscountCode | 15 | AdminUpdateDiscountCodeRequestDTO | 0 | internal | `mcp-backend/functions/api/admin/discount_code_api.py:62` |
| `admin_update_event` | PUT | admin claim | yes | updateEvent | 21 | UpdateEventRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/events_api.py:45` |
| `admin_update_event_guide` | PUT | admin claim | yes | updateGuide | 11 | UpdateEventGuideRequestDTO | 0 | internal | `mcp-backend/functions/api/admin/events_api.py:123` |
| `admin_update_event_location` | PUT | admin claim | yes | updateLocation | 11 | UpdateEventLocationRequestDTO | 1 | internal | `mcp-backend/functions/api/admin/location_api.py:37` |
| `admin_update_newsletter_signup` | PUT | admin claim | yes | update | 37 | NewsletterUpdateRequestDTO | 1 | internal | `mcp-backend/functions/api/admin/newsletter_api.py:38` |
| `admin_update_radio_episode` | PUT | admin claim | yes | updateEpisode | 11 | UpdateRadioEpisodeRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/radio_episodes_api.py:57` |
| `admin_update_radio_season` | PUT | admin claim | yes | updateSeason | 11 | UpdateRadioSeasonRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/radio_seasons_api.py:56` |
| `capture_order_event` | POST | public | yes | captureEventOrder | 10 | OrderCaptureDTO | 6 | internal | `mcp-backend/functions/api/public/event_payment_api.py:34` |
| `check_participants` | POST | public | yes | checkParticipants | 12 | CheckParticipantsRequestDTO | 4 | internal | `mcp-backend/functions/api/public/events_tickets_api.py:12` |
| `contact_us` | POST | public | yes | contactUs | 10 | ContactFormRequestDTO | 1 | internal | `mcp-backend/functions/api/public/contact_api.py:14` |
| `create_admin` | POST | admin claim | NO | — | 0 | CreateAdminRequestDTO | 0 | internal | `mcp-backend/functions/api/admin/admin.py:17` |
| `create_membership` | POST | admin claim | yes | createMembership | 13 | CreateMembershipRequestDTO | 6 | internal | `mcp-backend/functions/api/admin/members_api.py:53` |
| `create_order_event` | POST | public | yes | createEventOrder | 10 | PreOrderDTO | 7 | Firestore | `mcp-backend/functions/api/public/event_payment_api.py:16` |
| `create_participant` | POST | admin claim | yes | createParticipant | 14 | ParticipantCreateRequestDTO | 7 | internal | `mcp-backend/functions/api/admin/participants_api.py:50` |
| `create_purchase` | POST | admin claim | yes | createPurchase | 15 | CreatePurchaseRequestDTO | 4 | internal | `mcp-backend/functions/api/admin/purchases_api.py:41` |
| `create_wallet_pass` | POST | admin claim | yes | createWalletPass | 15 | MembershipIdRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/members_api.py:179` |
| `delete_admin` | DELETE | admin claim | NO | — | 0 | AdminIdQueryDTO | 0 | internal | `mcp-backend/functions/api/admin/admin.py:78` |
| `delete_membership` | DELETE | admin claim | yes | deleteMembership | 13 | MembershipIdRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/members_api.py:89` |
| `delete_message` | DELETE | admin claim | yes | deleteMessage | 13 | MessageIdRequestDTO | 1 | internal | `mcp-backend/functions/api/admin/messages_api.py:22` |
| `delete_participant` | DELETE | admin claim | yes | deleteParticipant | 14 | ParticipantLookupRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/participants_api.py:76` |
| `delete_purchase` | DELETE | admin claim | yes | deletePurchase | 15 | PurchaseIdRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/purchases_api.py:65` |
| `entrance_deactivate_scan_token` | POST | admin claim | yes | deactivateScanToken | 12 | DeactivateScanTokenRequestDTO | 1 | internal | `mcp-backend/functions/api/entrance/entrance_api.py:52` |
| `entrance_generate_scan_token` | POST | admin claim | yes | generateScanToken | 12 | GenerateScanTokenRequestDTO | 1 | internal | `mcp-backend/functions/api/entrance/entrance_api.py:23` |
| `entrance_manual_entry` | POST | admin claim | yes | manualEntry | 12 | ManualEntryRequestDTO | 1 | internal | `mcp-backend/functions/api/entrance/entrance_api.py:66` |
| `entrance_validate` | POST | public | yes | — | 1 | ValidateEntryRequestDTO | 1 | internal | `mcp-backend/functions/api/entrance/entrance_api.py:81` |
| `entrance_verify_scan_token` | GET | public | yes | verifyScanToken | 13 | VerifyScanTokenQueryDTO | 1 | internal | `mcp-backend/functions/api/entrance/entrance_api.py:38` |
| `get_admin_by_id` | GET | admin claim | NO | — | 0 | AdminIdQueryDTO | 0 | internal | `mcp-backend/functions/api/admin/admin.py:46` |
| `get_all_admins` | GET | admin claim | NO | — | 0 | inline/none | 0 | internal | `mcp-backend/functions/api/admin/admin.py:33` |
| `get_all_events` | GET | public | yes | getAllEvents | 22 | EventViewQueryDTO | 4 | internal | `mcp-backend/functions/api/public/events_api.py:20` |
| `get_all_purchases` | GET | admin claim | yes | getAllPurchases | 17 | inline/none | 2 | internal | `mcp-backend/functions/api/admin/purchases_api.py:19` |
| `get_event_by_id` | GET | public | yes | getEventById | 23 | EventLookupQueryDTO | 5 | internal | `mcp-backend/functions/api/public/events_api.py:43` |
| `get_event_guide` | GET | public | yes | getEventGuide | 10 | EventLookupQueryDTO | 0 | internal | `mcp-backend/functions/api/public/events_api.py:56` |
| `get_latest_radio_episode` | GET | public | yes | getLatestEpisode | 10 | inline/none | 1 | internal | `mcp-backend/functions/api/public/radio_public_api.py:21` |
| `get_membership` | GET | admin claim | yes | getMembershipById | 13 | MembershipLookupQueryDTO | 2 | internal | `mcp-backend/functions/api/admin/members_api.py:41` |
| `get_membership_events` | GET | admin claim | yes | getMembershipEvents | 13 | MembershipLookupQueryDTO | 2 | internal | `mcp-backend/functions/api/admin/members_api.py:140` |
| `get_membership_price` | GET | admin claim | yes | getMembershipPrice | 15 | MembershipPriceQueryDTO | 3 | internal | `mcp-backend/functions/api/admin/members_api.py:167` |
| `get_membership_price_public` | GET | public | yes | getMembershipPrice | 15 | inline/none | 0 | internal | `mcp-backend/functions/api/public/settings_api.py:37` |
| `get_membership_purchases` | GET | admin claim | yes | getMembershipPurchases | 13 | MembershipLookupQueryDTO | 2 | internal | `mcp-backend/functions/api/admin/members_api.py:125` |
| `get_memberships` | GET | admin claim | yes | getMemberships | 14 | MembershipListQueryDTO | 2 | internal | `mcp-backend/functions/api/admin/members_api.py:29` |
| `get_memberships_report` | GET | admin claim | yes | getMembershipsReport | 13 | MembershipReportQueryDTO | 2 | internal | `mcp-backend/functions/api/admin/members_api.py:224` |
| `get_messages` | GET | admin claim | yes | getAllMessages | 12 | inline/none | 1 | internal | `mcp-backend/functions/api/admin/messages_api.py:12` |
| `get_next_event` | GET | public | yes | getNextEvent | 12 | inline/none | 2 | internal | `mcp-backend/functions/api/public/events_api.py:33` |
| `get_participant` | POST | admin claim | yes | getParticipantById | 14 | ParticipantLookupRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/participants_api.py:37` |
| `get_participants_by_event` | POST | admin claim | yes | getParticipantsByEvent | 16 | ParticipantEventRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/participants_api.py:24` |
| `get_published_radio_episodes` | GET | public | yes | getPublishedEpisodes | 17 | inline/none | 1 | internal | `mcp-backend/functions/api/public/radio_public_api.py:12` |
| `get_purchase` | GET | admin claim | yes | getPurchase | 14 | PurchaseLookupQueryDTO | 2 | internal | `mcp-backend/functions/api/admin/purchases_api.py:28` |
| `get_radio_episode` | GET | public | yes | getEpisode | 12 | inline/none | 1 | internal | `mcp-backend/functions/api/public/radio_public_api.py:32` |
| `get_radio_seasons` | GET | public | yes | getSeasons | 15 | inline/none | 1 | internal | `mcp-backend/functions/api/public/radio_public_api.py:56` |
| `get_setting` | GET | public | yes | getSetting | 11 | GetSettingQueryDTO | 3 | internal | `mcp-backend/functions/api/public/settings_api.py:19` |
| `get_settings` | GET | public | yes | getSettings | 13 | GetSettingQueryDTO | 2 | internal | `mcp-backend/functions/api/admin/setting_api.py:17` |
| `get_wallet_model` | GET | admin claim | yes | getWalletModel | 13 | inline/none | 2 | internal | `mcp-backend/functions/api/admin/members_api.py:203` |
| `invalidate_wallet_pass` | POST | admin claim | yes | invalidateWalletPass | 13 | MembershipIdRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/members_api.py:191` |
| `member_get_event_location` | GET | Firebase member | yes | getEventLocation | 11 | MemberEventQueryDTO | 1 | internal | `mcp-backend/functions/api/member/location_api.py:14` |
| `member_get_events` | GET | Firebase member | yes | events | 123 | inline/none | 1 | internal | `mcp-backend/functions/api/member/member_api.py:34` |
| `member_get_me` | GET | Firebase member | yes | me | 12 | inline/none | 1 | internal | `mcp-backend/functions/api/member/member_api.py:21` |
| `member_get_purchases` | GET | Firebase member | yes | purchases | 45 | inline/none | 1 | internal | `mcp-backend/functions/api/member/member_api.py:47` |
| `member_get_ticket` | GET | Firebase member | yes | ticket | 20 | MemberEventQueryDTO | 1 | internal | `mcp-backend/functions/api/member/member_api.py:60` |
| `member_patch_preferences` | PATCH | Firebase member | yes | preferences | 10 | MemberPreferencesPatchDTO | 1 | internal | `mcp-backend/functions/api/member/member_api.py:76` |
| `merge_memberships` | POST | admin claim | yes | mergeMemberships | 13 | MergeMembershipsRequestDTO | 1 | internal | `mcp-backend/functions/api/admin/members_api.py:77` |
| `newsletter_signup` | POST | public | yes | newsletterSignup | 11 | NewsletterSignupRequestDTO | 1 | Sender.net | `mcp-backend/functions/api/public/newsletter_api.py:18` |
| `provision_member_accounts` | POST | admin claim | yes | provisionAll | 11 | inline/none | 0 | Firebase | `mcp-backend/functions/api/admin/members_auth_api.py:24` |
| `provision_single_member_account` | POST | admin claim | yes | provisionSingle | 11 | inline/none | 0 | Firebase | `mcp-backend/functions/api/admin/members_auth_api.py:86` |
| `renew_membership` | POST | admin claim | yes | renewMembership | 13 | RenewMembershipRequestDTO | 0 | internal | `mcp-backend/functions/api/admin/members_api.py:101` |
| `reply_to_message` | POST | admin claim | yes | replyToMessage | 13 | ReplyMessageRequestDTO | 1 | internal | `mcp-backend/functions/api/admin/messages_api.py:33` |
| `send_location` | POST | admin claim | yes | sendLocation | 15 | SendLocationRequestDTO | 5 | internal | `mcp-backend/functions/api/admin/participants_api.py:107` |
| `send_location_to_all` | POST | admin claim | yes | sendLocationToAll | 15 | SendLocationToAllRequestDTO | 1 | internal | `mcp-backend/functions/api/admin/participants_api.py:118` |
| `send_membership_card` | POST | admin claim | yes | sendMembershipCard | 13 | MembershipIdRequestDTO | 1 | internal | `mcp-backend/functions/api/admin/members_api.py:113` |
| `send_omaggio_emails` | POST | admin claim | yes | sendOmaggioEmails | 15 | SendOmaggioEmailsRequestDTO | 1 | internal | `mcp-backend/functions/api/admin/participants_api.py:130` |
| `send_ticket` | POST | admin claim | yes | sendTicket | 15 | SendTicketRequestDTO | 3 | internal | `mcp-backend/functions/api/admin/participants_api.py:92` |
| `sender_webhook` | POST | public | yes | — | 0 | inline/none | 2 | Sender.net | `mcp-backend/functions/api/public/sender_webhook_api.py:21` |
| `set_membership_price` | POST | admin claim | yes | setMembershipPrice | 14 | MembershipPriceSetRequestDTO | 3 | internal | `mcp-backend/functions/api/admin/members_api.py:155` |
| `set_settings` | POST | admin claim | yes | setSetting | 11 | SetSettingRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/setting_api.py:32` |
| `set_wallet_model` | POST | admin claim | yes | setWalletModel | 13 | WalletModelSetRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/members_api.py:212` |
| `update_admin` | PUT | admin claim | NO | — | 0 | UpdateAdminRequestDTO | 0 | internal | `mcp-backend/functions/api/admin/admin.py:62` |
| `update_membership` | PUT | admin claim | yes | updateMembership | 13 | UpdateMembershipRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/members_api.py:65` |
| `update_participant` | PUT | admin claim | yes | updateParticipant | 14 | ParticipantUpdateRequestDTO | 2 | internal | `mcp-backend/functions/api/admin/participants_api.py:63` |
| `update_purchase_status` | POST | admin claim | yes | updatePurchaseStatus | 16 | UpdatePurchaseStatusRequestDTO | 1 | internal | `mcp-backend/functions/api/admin/purchases_api.py:53` |
| `validate_discount_code` | POST | public | yes | validateDiscountCode | 11 | ValidateDiscountCodeRequestDTO | 2 | internal | `mcp-backend/functions/api/public/discount_code_public_api.py:20` |
| `verify_admin` | CALLABLE | callable auth check | NO | — | 0 | inline/none | 0 | internal | `mcp-backend/functions/api/admin/admin.py:93` |

## Required contract fields not yet formalized

| Required field | Current evidence | Gap to close |
|---|---|---|
| Consumer | The table records static frontend-reference counts and route-map keys. | Resolve ambiguous keys, external callers, deployed versions, and owners with runtime telemetry and owner review. |
| Authentication / authorization | Access decorators and wrappers are recorded per endpoint. | Add negative contract tests and document claim/role semantics, token sources, and exceptions. |
| Request schema | Pydantic DTOs are recorded where statically visible; `inline/none` marks legacy parsing or no payload. | Capture query, path, body, headers, constraints, and examples in an executable specification. |
| Response schema | Handlers return Flask JSON, dictionaries, lists, or DTO payloads; no shared response specification exists. | Record every success envelope and field, including nullability and compatibility guarantees. |
| Errors | Status/error returns vary across handlers and shared exception adapters. | Enumerate status codes and machine-readable error envelopes for each endpoint. |
| Data sources | Data access is usually indirect through services/repositories and is not declared at the endpoint boundary. | Trace endpoint-to-collection/query/write paths and operation counts in the benchmark harness. |
| External dependencies | The table contains conservative endpoint-body keyword signals only. | Trace indirect provider calls, retries, timeouts, idempotency, and failure behavior through service call graphs. |
| Performance | Three public endpoints have only exploratory warm samples; no endpoint has a statistically valid baseline. | Measure p50/p95/p99, cold starts, payload bytes, Firestore reads/writes, provider timings, and error rate per tier-1 endpoint. |
| Test coverage | The table records files that mention the endpoint name, not branch or behavioral coverage. | Link each contract behavior to deterministic unit, integration, contract, and E2E cases. |

## Minimum executable-contract target

1. Versioned OpenAPI for every exported HTTP endpoint, including auth, request, response, and error schemas.
2. A generated or schema-checked frontend client with no duplicate handwritten route catalog.
3. Contract tests for happy path, validation, authentication, authorization, not found, conflict/idempotency, and provider failures where applicable.
4. A deployment check that fails on unexported handlers, mapped-but-missing routes, undocumented exports, or schema drift.
5. An explicit decision for external-only routes such as webhooks and literal proxy paths.

## Evidence limitations

- Static repository evidence does not prove which functions are deployed.
- Arbitrary Flask return paths prevent reliable automatic derivation of complete response/error schemas.
- Provider labels are conservative keyword signals; performance fields require measured baselines in WS3.
