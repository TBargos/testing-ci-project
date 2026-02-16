from datetime import datetime, timezone

import pytest

from parking_pay.models import Client, ClientParking, Parking
from tests.factories import ClientFactory, ParkingFactory

# --- Проверка всех GET-методов ---


@pytest.mark.parametrize("url", ["/", "/clients", "/clients/1"])
def test_get_endpoints(client, url):
    response = client.get(url)
    assert response.status_code == 200


# --- Создание клиента (оригинальный тест) ---


def test_create_client(client):
    response = client.post(
        "/clients",
        json={
            "name": "New",
            "surname": "Client",
            "credit_card": "9999",
            "car_number": "B456CD",
        },
    )

    assert response.status_code == 201


# --- Создание клиента (через Factory Boy) ---


def test_create_client_with_factory(client, app, db):
    fake_client = ClientFactory()

    with app.app_context():
        before_count = db.session.query(Client).count()

    response = client.post(
        "/clients",
        json={
            "name": fake_client.name,
            "surname": fake_client.surname,
            "credit_card": fake_client.credit_card,
            "car_number": fake_client.car_number,
        },
    )

    assert response.status_code == 201

    with app.app_context():
        after_count = db.session.query(Client).count()
        assert after_count == before_count + 1


# --- Создание парковки (оригинальный тест) ---


def test_create_parking(client):
    response = client.post(
        "/parkings", json={"address": "New parking", "opened": True, "count_places": 7}
    )

    assert response.status_code == 201


# --- Создание парковки (через Factory Boy) ---


def test_create_parking_with_factory(client, app, db):
    fake_parking = ParkingFactory()

    with app.app_context():
        before_count = db.session.query(Parking).count()

    response = client.post(
        "/parkings",
        json={
            "address": fake_parking.address,
            "opened": fake_parking.opened,
            "count_places": fake_parking.count_places,
        },
    )

    assert response.status_code == 201

    with app.app_context():
        after_count = db.session.query(Parking).count()
        assert after_count == before_count + 1


# --- Заезд на парковку ---


@pytest.mark.parking
def test_enter_parking(client, app, db):
    response = client.post("/client_parkings", json={"client_id": 1, "parking_id": 2})

    assert response.status_code == 201

    with app.app_context():
        parking = db.session.get(Parking, 2)
        assert parking.count_available_places == 4


# --- Выезд с парковки ---


@pytest.mark.parking
def test_exit_parking(client, app, db):
    with app.app_context():
        active_record = ClientParking(
            client_id=1, parking_id=2, time_in=datetime.now(timezone.utc)
        )
        db.session.add(active_record)
        db.session.commit()

        parking_before = db.session.get(Parking, 2)
        places_before = parking_before.count_available_places

    response = client.delete("/client_parkings", json={"client_id": 1, "parking_id": 2})

    assert response.status_code == 200

    with app.app_context():
        parking_after = db.session.get(Parking, 2)
        assert parking_after.count_available_places == places_before + 1

        record = (
            db.session.query(ClientParking).filter_by(client_id=1, parking_id=2).first()
        )

        assert record.time_out is not None
        assert record.time_out >= record.time_in
