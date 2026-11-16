
import sqlite3

DB_NAME = "robotics.db"


def connect_db():
    return sqlite3.connect(DB_NAME)


def create_tables():
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Basic information
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            manufacturer TEXT,
            model TEXT,
            role TEXT,

            -- Electrical specifications
            voltage TEXT,
            rated_voltage REAL,
            voltage_min REAL,
            voltage_max REAL,
            current_min REAL,
            current_max REAL,

            -- Performance specifications
            rpm REAL,
            torque REAL,
            motor_type TEXT,

            -- Physical specifications
            dimensions TEXT,
            weight REAL,
            interface TEXT,

            -- Commercial information
            price REAL,
            currency TEXT DEFAULT 'JOD',
            stock INTEGER DEFAULT 0,
            source_type TEXT DEFAULT 'local_database',
            source_name TEXT,
            product_url TEXT,
            datasheet_url TEXT,
            last_updated TEXT,

            -- Robot compatibility
            quantity_per_robot INTEGER DEFAULT 1,
            supported_robot TEXT,
            specifications TEXT,
            notes TEXT
        )
    """)

    # Add new columns safely to existing databases
    new_columns = {
        "manufacturer": "TEXT",
        "model": "TEXT",
        "current_min": "REAL",
        "current_max": "REAL",
        "rpm": "REAL",
        "torque": "REAL",
        "motor_type": "TEXT",
        "dimensions": "TEXT",
        "weight": "REAL",
        "interface": "TEXT",
        "currency": "TEXT DEFAULT 'JOD'",
        "source_type": "TEXT DEFAULT 'local_database'",
        "source_name": "TEXT",
        "product_url": "TEXT",
        "datasheet_url": "TEXT",
        "last_updated": "TEXT"
    }

    existing_columns = {
        row[1] for row in
        cursor.execute("PRAGMA table_info(components)").fetchall()
    }

    for column, data_type in new_columns.items():
        if column not in existing_columns:
            cursor.execute(
                f"ALTER TABLE components ADD COLUMN "
                f"{column} {data_type}"
            )

    # Database indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_component_category
        ON components(category)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_component_role
        ON components(role)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_component_manufacturer
        ON components(manufacturer)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_component_source
        ON components(source_type)
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_tables()
    print("Robotics database updated successfully!")
