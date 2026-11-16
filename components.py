
from database import connect_db, create_tables


# ==========================================
# SAMPLE ROBOTICS COMPONENTS
# ==========================================

SAMPLE_COMPONENTS = [

    {
        "name": "ESP32 DevKit",
        "category": "Microcontroller",
        "voltage": "3.3V",
        "specifications": "WiFi, Bluetooth, GPIO",
        "price": 8.0,
        "stock": 10,
        "role": "controller",
        "rated_voltage": None,
        "voltage_min": None,
        "voltage_max": None,
        "quantity_per_robot": 1,
        "supported_robot": "Line Follower",
        "notes": "3.3V logic. Check the exact board power input."
    },

    {
        "name": "Arduino Uno",
        "category": "Microcontroller",
        "voltage": "5V",
        "specifications": "ATmega328P, 14 Digital Pins",
        "price": 12.0,
        "stock": 10,
        "role": "controller",
        "rated_voltage": None,
        "voltage_min": None,
        "voltage_max": None,
        "quantity_per_robot": 1,
        "supported_robot": "Line Follower",
        "notes": "5V logic board."
    },

    {
        "name": "5 Channel IR Sensor",
        "category": "Sensor",
        "voltage": "3.3V-5V",
        "specifications": "5 infrared channels",
        "price": 4.0,
        "stock": 15,
        "role": "line_sensor",
        "rated_voltage": None,
        "voltage_min": 3.3,
        "voltage_max": 5.0,
        "quantity_per_robot": 1,
        "supported_robot": "Line Follower",
        "notes": "One sensor board with five sensing channels."
    },

    {
        "name": "TB6612FNG",
        "category": "Motor Driver",
        "voltage": "2.5V-13.5V",
        "specifications": "Dual DC motor driver",
        "price": 5.0,
        "stock": 8,
        "role": "motor_driver",
        "rated_voltage": None,
        "voltage_min": 2.5,
        "voltage_max": 13.5,
        "quantity_per_robot": 1,
        "supported_robot": "Line Follower",
        "notes": "Motor supply range. Logic supply must also be checked."
    },

    {
        "name": "N20 DC Motor",
        "category": "Motor",
        "voltage": "6V",
        "specifications": "Metal gearbox DC motor",
        "price": 6.0,
        "stock": 12,
        "role": "drive_motor",
        "rated_voltage": 6.0,
        "voltage_min": None,
        "voltage_max": None,
        "quantity_per_robot": 2,
        "supported_robot": "Line Follower",
        "notes": "One motor per wheel. Confirm motor speed and current."
    },

    {
        "name": "2S LiPo Battery",
        "category": "Battery",
        "voltage": "7.4V",
        "specifications": "Two-cell lithium polymer battery",
        "price": 15.0,
        "stock": 5,
        "role": "battery",
        "rated_voltage": 7.4,
        "voltage_min": None,
        "voltage_max": None,
        "quantity_per_robot": 1,
        "supported_robot": "Line Follower",
        "notes": "Nominal voltage 7.4V. Check motor voltage requirements."
    }
]


# ==========================================
# ADD OR UPDATE SAMPLE DATA
# ==========================================

def add_sample_components():

    create_tables()

    connection = connect_db()
    cursor = connection.cursor()

    for item in SAMPLE_COMPONENTS:

        cursor.execute("""
            SELECT id FROM components
            WHERE name = ?
        """, (item["name"],))

        existing = cursor.fetchone()

        if existing is None:

            cursor.execute("""
                INSERT INTO components (
                    name, category, voltage, specifications,
                    price, stock, role, rated_voltage,
                    voltage_min, voltage_max,
                    quantity_per_robot, supported_robot, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["name"],
                item["category"],
                item["voltage"],
                item["specifications"],
                item["price"],
                item["stock"],
                item["role"],
                item["rated_voltage"],
                item["voltage_min"],
                item["voltage_max"],
                item["quantity_per_robot"],
                item["supported_robot"],
                item["notes"]
            ))

        else:

            # Update technical metadata without overwriting
            # the existing price or stock values.
            cursor.execute("""
                UPDATE components
                SET role = ?,
                    rated_voltage = ?,
                    voltage_min = ?,
                    voltage_max = ?,
                    quantity_per_robot = ?,
                    supported_robot = ?,
                    notes = ?
                WHERE name = ?
            """, (
                item["role"],
                item["rated_voltage"],
                item["voltage_min"],
                item["voltage_max"],
                item["quantity_per_robot"],
                item["supported_robot"],
                item["notes"],
                item["name"]
            ))

    connection.commit()
    connection.close()

    print("Component database updated successfully!")


# ==========================================
# DISPLAY COMPONENTS
# ==========================================

def show_components():

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name, category, role, voltage,
               price, stock, quantity_per_robot
        FROM components
        ORDER BY category
    """)

    results = cursor.fetchall()

    connection.close()

    print("\n========== ROBOTICS COMPONENT DATABASE ==========")

    for item in results:

        print(
            f"\nName: {item[0]}"
            f"\nCategory: {item[1]}"
            f"\nRole: {item[2]}"
            f"\nVoltage: {item[3]}"
            f"\nPrice: {item[4]} JD"
            f"\nStock: {item[5]}"
            f"\nRequired Quantity: {item[6]}"
        )

    print("\n==================================================")


if __name__ == "__main__":

    add_sample_components()
    show_components()
