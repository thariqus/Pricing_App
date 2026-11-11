from flask import Flask
from repository.price.fetch_price import fetch_all_prices
from unittest.mock import patch
from api import app

def test_fetch_prices_invalid_page():
    with app.test_request_context("/prices?page=0"):
        body, status_code = fetch_all_prices()

        assert status_code == 400
        assert body.json["status"] == "error"
        assert body.json["message"] == "Page must be greater than 0"


def test_fetch_prices_invalid_limit():
    with app.test_request_context("/prices?limit=101"):
        body, status_code = fetch_all_prices()

        assert status_code == 400
        assert body.json["status"] == "error"
        assert body.json["message"] == "Limit must be between 1 and 100"


def test_fetch_prices_success():
    with app.test_request_context("/prices?page=1&limit=10"):
        response = fetch_all_prices()

        assert response["status"] == "success"
        assert response["page"] == 1
        assert response["limit"] == 10
        assert isinstance(response["data"], list)
        assert response["total"] >= 0


def test_fetch_prices_connection_error():
    with app.test_request_context("/prices?page=1&limit=10"):
        with patch(
            "repository.price.fetch_price.get_db_connection",
            side_effect=ConnectionError("Database unavailable")
        ):
            body, status_code = fetch_all_prices()

            assert status_code == 503
            assert body.json["status"] == "error"
            assert body.json["message"] == "Unable to connect to database"
            assert body.json["error"] == "Database unavailable"
