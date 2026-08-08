from app.models.database import Base, engine
from app.models.user import User
from app.models.payment import Payment
from app.models.discount import DiscountCode
from app.models.performance import MonthlyPerformance


def init_database():
    Base.metadata.create_all(
        bind=engine
    )

    print(
        "ALIFT database initialized successfully."
    )


if __name__ == "__main__":
    init_database()