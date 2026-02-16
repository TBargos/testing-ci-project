from datetime import datetime, timezone

from flask import abort, jsonify, request
from sqlalchemy import select

from . import db
from .models import Client, ClientParking, Parking


def register_routes(app):

    @app.get("/")
    def index():
        return {"service": "Parking API", "version": "1.0"}

    @app.get("/clients")
    def get_clients():
        stmt = select(Client)
        clients = db.session.execute(stmt).scalars().all()

        return jsonify(
            [
                {
                    "id": c.id,
                    "name": c.name,
                    "surname": c.surname,
                    "car_number": c.car_number,
                }
                for c in clients
            ]
        )

    @app.get("/clients/<int:client_id>")
    def get_client(client_id):
        client = db.session.get(Client, client_id)
        if not client:
            abort(404)

        return jsonify(
            {
                "id": client.id,
                "name": client.name,
                "surname": client.surname,
                "car_number": client.car_number,
            }
        )

    @app.post("/clients")
    def create_client():
        data = request.json

        client = Client(
            name=data["name"],
            surname=data["surname"],
            credit_card=data.get("credit_card"),
            car_number=data.get("car_number"),
        )

        db.session.add(client)
        db.session.commit()

        return jsonify({"message": "Client created"}), 201

    @app.post("/parkings")
    def create_parking():
        data = request.json

        parking = Parking(
            address=data["address"],
            opened=data.get("opened", True),
            count_places=data["count_places"],
            count_available_places=data["count_places"],
        )

        db.session.add(parking)
        db.session.commit()

        return jsonify({"message": "Parking created"}), 201

    @app.post("/client_parkings")
    def enter_parking():
        data = request.json

        client = db.session.get(Client, data["client_id"])
        if not client:
            abort(404)

        parking = db.session.get(Parking, data["parking_id"])
        if not parking:
            abort(404)

        if not parking.opened:
            return jsonify({"error": "Parking closed"}), 400

        if parking.count_available_places <= 0:
            return jsonify({"error": "No available places"}), 400

        parking.count_available_places -= 1

        record = ClientParking(
            client_id=client.id,
            parking_id=parking.id,
            time_in=datetime.now(timezone.utc),
        )

        db.session.add(record)
        db.session.commit()

        return jsonify({"message": "Entered parking"}), 201

    @app.delete("/client_parkings")
    def exit_parking():
        data = request.json

        client = db.session.get(Client, data["client_id"])
        if not client:
            abort(404)

        parking = db.session.get(Parking, data["parking_id"])
        if not parking:
            abort(404)

        stmt = select(ClientParking).filter_by(
            client_id=client.id, parking_id=parking.id, time_out=None
        )

        record = db.session.execute(stmt).scalar_one_or_none()

        if not record:
            return jsonify({"error": "Record not found"}), 404

        if not client.credit_card:
            return jsonify({"error": "No credit card linked"}), 400

        parking.count_available_places += 1
        record.time_out = datetime.now(timezone.utc)

        db.session.commit()

        return jsonify({"message": "Exited parking"})
