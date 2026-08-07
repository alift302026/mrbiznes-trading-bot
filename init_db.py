from app.models.database import Base, engine
from app.models.user import User


def init_database():
    Base.metadata.create_all(bind=engine)
    print("Database created successfully.")


if __name__ == "__main__":
    init_database()