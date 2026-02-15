import random
import factory
from faker import Faker

from parking_pay.models import Client, Parking

fake = Faker()


class ClientFactory(factory.Factory):
    class Meta:
        model = Client

    name = factory.Faker("first_name")
    surname = factory.Faker("last_name")

    # либо есть карта, либо None
    credit_card = factory.LazyFunction(
        lambda: fake.credit_card_number() if random.choice([True, False]) else None
    )

    car_number = factory.Faker("bothify", text="??###??")


class ParkingFactory(factory.Factory):
    class Meta:
        model = Parking

    address = factory.Faker("address")
    opened = factory.Faker("boolean")

    count_places = factory.Faker("random_int", min=1, max=200)

    # доступных мест изначально столько же
    count_available_places = factory.LazyAttribute(
        lambda obj: obj.count_places
    )
