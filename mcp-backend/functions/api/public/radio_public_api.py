from flask import jsonify

from api.decorators import public_endpoint
from services.radio import RadioEpisodeService, RadioSeasonService
from utils.http_responses import handle_service_error

episode_service = RadioEpisodeService()
season_service = RadioSeasonService()


@public_endpoint(methods=("GET",))
def get_published_radio_episodes(req):
    try:
        payload = episode_service.get_all(published_only=True)
        return jsonify([e.to_payload() for e in payload]), 200
    except Exception as err:
        return handle_service_error(err)


@public_endpoint(methods=("GET",))
def get_latest_radio_episode(req):
    try:
        episode = episode_service.get_latest_published()
        if episode is None:
            return jsonify({"error": "No published episodes found"}), 404
        return jsonify(episode.to_payload()), 200
    except Exception as err:
        return handle_service_error(err)


@public_endpoint(methods=("GET",))
def get_radio_episode(req):
    try:
        args = req.args or {}
        slug = args.get("slug", "").strip()
        episode_id = args.get("id", "").strip()

        if not slug and not episode_id:
            return jsonify({"error": "Missing required query param: slug or id"}), 400

        if slug:
            episode = episode_service.get_by_slug(slug)
            if episode is None:
                return jsonify({"error": "Episode not found"}), 404
        else:
            episode = episode_service.get_by_id(episode_id)

        if not episode.is_published:
            return jsonify({"error": "Episode not found"}), 404
        return jsonify(episode.to_payload()), 200
    except Exception as err:
        return handle_service_error(err)


@public_endpoint(methods=("GET",))
def get_radio_seasons(req):
    try:
        payload = season_service.get_all()
        return jsonify([s.to_payload() for s in payload]), 200
    except Exception as err:
        return handle_service_error(err)
