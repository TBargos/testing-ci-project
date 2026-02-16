from datetime import datetime, timezone

import pytest

from parking_pay import create_app
from parking_pay import db as _db
from parking_pay.models import Client, ClientParking, Parking


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
    )

    with app.app_context():
        _db.create_all()

        # Клиент
        client = Client(
            name="Test", surname="User", credit_card="1111", car_number="A123BC"
        )

        # Парковка №1 (будет иметь завершённый лог)
        parking1 = Parking(
            address="Parking 1", opened=True, count_places=10, count_available_places=10
        )

        # Парковка №2 (для теста заезда)
        parking2 = Parking(
            address="Parking 2", opened=True, count_places=5, count_available_places=5
        )

        _db.session.add_all([client, parking1, parking2])
        _db.session.commit()

        # Завершённый лог для (client=1, parking=1)
        record = ClientParking(
            client_id=client.id,
            parking_id=parking1.id,
            time_in=datetime.now(timezone.utc),
            time_out=datetime.now(timezone.utc),
        )

        _db.session.add(record)
        _db.session.commit()

    yield app

    with app.app_context():
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db
