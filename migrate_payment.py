import sqlite3


DB = "data/trading_assistant.db"


columns = {
    "payment_method": "TEXT",
    "plan_days": "INTEGER",
    "plan_price": "REAL",
    "destination": "TEXT",
    "details": "TEXT",
    "reviewed_by": "INTEGER",
    "reviewed_at": "DATETIME",
}


connection = sqlite3.connect(
    DB
)

cursor = connection.cursor()


existing = {
    row[1]
    for row in cursor.execute(
        "PRAGMA table_info(payments)"
    ).fetchall()
}


print(
    "BEFORE:",
    sorted(existing),
)


for name, column_type in columns.items():

    if name not in existing:

        cursor.execute(
            f"ALTER TABLE payments "
            f"ADD COLUMN {name} {column_type}"
        )

        print(
            "ADDED:",
            name,
        )


connection.commit()


after = [
    row[1]
    for row in cursor.execute(
        "PRAGMA table_info(payments)"
    ).fetchall()
]


print(
    "AFTER:",
    after,
)


connection.close()


print(
    "PAYMENT MIGRATION OK"
)