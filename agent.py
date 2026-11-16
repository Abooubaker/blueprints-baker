
import ollama
import json
from database import connect_db


# ==========================================
# 1. DATABASE SEARCH
# ==========================================

def search_components(category=None):

    connection = connect_db()
    connection.row_factory = None
    cursor = connection.cursor()

    query = """
        SELECT id, name, category, voltage,
               specifications, price, stock,
               role, rated_voltage,
               voltage_min, voltage_max,
               quantity_per_robot,
               supported_robot, notes
        FROM components
        WHERE stock > 0
    """

    values = []

    category_mapping = {
        "sensors": "Sensor",
        "sensor": "Sensor",
        "motors": "Motor",
        "motor": "Motor",
        "microcontroller": "Microcontroller",
        "controllers": "Microcontroller",
        "motor driver": "Motor Driver",
        "drivers": "Motor Driver",
        "battery": "Battery",
        "batteries": "Battery"
    }

    if category:
        category = category_mapping.get(
            category.lower().strip(),
            category
        )

        query += " AND category LIKE ?"
        values.append(f"%{category}%")

    cursor.execute(query, values)

    rows = cursor.fetchall()
    connection.close()

    columns = [
        "id", "name", "category", "voltage",
        "specifications", "price", "stock",
        "role", "rated_voltage",
        "voltage_min", "voltage_max",
        "quantity_per_robot",
        "supported_robot", "notes"
    ]

    return [
        dict(zip(columns, row))
        for row in rows
    ]


# ==========================================
# 2. COMPONENT SELECTION ENGINE
# ==========================================

def select_component(role, robot_type):

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, category, voltage,
               specifications, price, stock,
               role, rated_voltage,
               voltage_min, voltage_max,
               quantity_per_robot,
               supported_robot, notes
        FROM components
        WHERE role = ?
          AND stock > 0
        ORDER BY price ASC
    """, (role,))

    rows = cursor.fetchall()
    connection.close()

    columns = [
        "id", "name", "category", "voltage",
        "specifications", "price", "stock",
        "role", "rated_voltage",
        "voltage_min", "voltage_max",
        "quantity_per_robot",
        "supported_robot", "notes"
    ]

    candidates = [
        dict(zip(columns, row))
        for row in rows
    ]

    for component in candidates:

        supported = component["supported_robot"]

        if supported:
            supported_types = [
                item.strip().lower()
                for item in supported.split(",")
            ]

            if (
                robot_type.lower() not in supported_types
                and "all" not in supported_types
            ):
                continue

        quantity = component["quantity_per_robot"] or 1

        if component["stock"] >= quantity:
            return component

    return None


# ==========================================
# 3. BUILD ROBOT PROPOSAL
# ==========================================

def build_robot_proposal(requirements):

    robot_type = requirements["robot_type"]
    budget = requirements["budget_jd"]

    if robot_type.lower() not in [
        "line follower",
        "line follower robot"
    ]:

        return {
            "success": False,
            "message": (
                "This robot type is not supported yet. "
                "Currently supported: Line Follower."
            )
        }

    required_roles = [
        "controller",
        "motor_driver",
        "drive_motor",
        "line_sensor",
        "battery"
    ]

    selected_components = []
    missing_components = []
    total_cost = 0.0

    for role in required_roles:

        component = select_component(
            role,
            "Line Follower"
        )

        if component is None:
            missing_components.append(role)
            continue

        quantity = component["quantity_per_robot"] or 1

        unit_price = float(component["price"] or 0)
        subtotal = unit_price * quantity

        selected_components.append({
            "id": component["id"],
            "name": component["name"],
            "category": component["category"],
            "role": component["role"],
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": round(subtotal, 2),
            "stock": component["stock"],
            "voltage": component["voltage"],
            "rated_voltage": component["rated_voltage"],
            "voltage_min": component["voltage_min"],
            "voltage_max": component["voltage_max"],
            "specifications": component["specifications"],
            "notes": component["notes"]
        })

        total_cost += subtotal

    total_cost = round(total_cost, 2)

    # Check battery and motor voltage
    compatibility_warnings = []

    battery = next(
        (
            item for item in selected_components
            if item["role"] == "battery"
        ),
        None
    )

    motor = next(
        (
            item for item in selected_components
            if item["role"] == "drive_motor"
        ),
        None
    )

    if battery and motor:

        battery_voltage = battery["rated_voltage"]
        motor_voltage = motor["rated_voltage"]

        if (
            battery_voltage is not None
            and motor_voltage is not None
            and battery_voltage > motor_voltage
        ):

            compatibility_warnings.append(
                f"Battery nominal voltage is "
                f"{battery_voltage}V, while the motor "
                f"rated voltage is {motor_voltage}V. "
                "A suitable voltage regulation solution "
                "or a different battery must be verified."
            )

    # Check budget
    within_budget = total_cost <= budget

    proposal = {
        "success": True,
        "robot_type": robot_type,
        "budget_jd": budget,
        "performance": requirements["performance"],
        "components": selected_components,
        "missing_components": missing_components,
        "total_cost": total_cost,
        "remaining_budget": round(budget - total_cost, 2),
        "within_budget": within_budget,
        "compatibility_warnings": compatibility_warnings,
        "additional_parts_not_in_database": [
            "Robot chassis",
            "Wheels",
            "Wiring and connectors",
            "Power switch",
            "Mounting hardware"
        ],
        "approval_required": True
    }

    return proposal


# ==========================================
# 4. DISPLAY PROPOSAL
# ==========================================

def display_proposal(proposal):

    print("\n========================================")
    print("       ROBOT COMPONENT PROPOSAL")
    print("========================================")

    if not proposal["success"]:
        print(proposal["message"])
        return

    print("\nRobot:", proposal["robot_type"])
    print("Budget:", proposal["budget_jd"], "JD")
    print("Performance:", proposal["performance"])

    print("\nSelected Components:")

    for item in proposal["components"]:

        print("\nComponent:", item["name"])
        print("Role:", item["role"])
        print("Quantity:", item["quantity"])
        print("Unit Price:", item["unit_price"], "JD")
        print("Subtotal:", item["subtotal"], "JD")
        print("Stock:", item["stock"])

    print("\n----------------------------------------")
    print("Total Cost:", proposal["total_cost"], "JD")
    print("Budget:", proposal["budget_jd"], "JD")

    if proposal["within_budget"]:
        print("Budget Status: WITHIN BUDGET")
    else:
        print(
            "Budget Status: OVER BUDGET by",
            abs(proposal["remaining_budget"]),
            "JD"
        )

    if proposal["missing_components"]:

        print("\nMissing Components:")

        for role in proposal["missing_components"]:
            print("-", role)

    if proposal["compatibility_warnings"]:

        print("\nCompatibility Warnings:")

        for warning in proposal["compatibility_warnings"]:
            print("-", warning)

    print("\nAdditional parts not included in cost:")

    for part in proposal["additional_parts_not_in_database"]:
        print("-", part)

    print("\n========================================")
    print("User approval is required.")
    print("========================================")


# ==========================================
# 5. TOOL DEFINITION
# ==========================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_components",
            "description": (
                "Search the robotics database for available "
                "components by category."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": (
                            "Sensor, Motor, Microcontroller, "
                            "Motor Driver, or Battery."
                        )
                    }
                },
                "required": ["category"]
            }
        }
    }
]


# ==========================================
# 6. COLLECT REQUIREMENTS
# ==========================================

def collect_requirements():

    print("\n=== Robot Project Requirements ===")

    robot_type = input(
        "\nWhat type of robot do you want to build? "
    ).strip()

    while not robot_type:

        robot_type = input(
            "Please enter the robot type: "
        ).strip()

    while True:

        try:

            budget = float(input(
                "\nWhat is your total budget in JD? "
            ))

            if budget > 0:
                break

            print("Budget must be greater than zero.")

        except ValueError:

            print("Please enter a valid number.")

    while True:

        performance = input(
            "\nPerformance preference (Normal / High Speed): "
        ).strip().lower()

        if performance in ["normal", "high speed"]:
            break

        print("Please enter Normal or High Speed.")

    return {
        "robot_type": robot_type,
        "budget_jd": budget,
        "performance": performance
    }


# ==========================================
# 7. EXECUTE TOOLS
# ==========================================

def execute_tool(tool_call):

    function_name = tool_call["function"]["name"]
    arguments = tool_call["function"]["arguments"]

    if function_name == "search_components":

        result = search_components(**arguments)

        print("\n[Tool Used: Database Search]")
        print("Search Results:", result)

        return result

    return {
        "error": "Unknown tool"
    }


# ==========================================
# 8. START AI AGENT
# ==========================================

def start_agent(requirements):

    proposal = build_robot_proposal(requirements)

    display_proposal(proposal)

    messages = [
        {
            "role": "system",
            "content": f"""
You are an AI Robotics Assistant.

Your job is to help users build robots.

Communicate in English.

The following proposal was generated by the Python
selection engine using the actual database.

PROPOSAL DATA:
{json.dumps(proposal, indent=2)}

IMPORTANT RULES:

1. Treat the proposal data as the source of truth.
2. Never invent components, prices, stock, or specifications.
3. Never change the calculated total cost.
4. Never claim the robot is within budget if within_budget is false.
5. Explain compatibility warnings clearly.
6. Explain missing components.
7. Do not claim that a purchase has been made.
8. Ask for user approval before finalizing the proposal.
9. You may use search_components to answer questions
   about available database components.
10. Do not claim compatibility unless the database
    contains enough information to support it.

If the proposal exceeds the budget, explain that honestly.
Suggest searching for cheaper available alternatives only
if they actually exist in the database.
"""
        },
        {
            "role": "user",
            "content": (
                "Explain the generated robot proposal, "
                "its total cost, and any compatibility issues. "
                "Then ask for my approval."
            )
        }
    ]

    print("\nAI Robotics Agent Started!")
    print("Type 'exit' to stop.")

    while True:

        try:

            response = ollama.chat(
                model="qwen3:4b",
                messages=messages,
                tools=tools
            )

            tool_rounds = 0
            max_tool_rounds = 8

            while True:

                assistant_message = response["message"]
                tool_calls = assistant_message.get(
                    "tool_calls", []
                )

                messages.append(assistant_message)

                if not tool_calls:

                    answer = assistant_message.get(
                        "content", ""
                    )

                    print("\nAI Agent:", answer)
                    break

                tool_rounds += 1

                if tool_rounds > max_tool_rounds:

                    print("\nTool call limit reached.")
                    break

                for tool_call in tool_calls:

                    try:

                        result = execute_tool(tool_call)

                    except Exception as error:

                        result = {
                            "error": str(error)
                        }

                    messages.append({
                        "role": "tool",
                        "content": json.dumps(
                            result,
                            ensure_ascii=False
                        ),
                        "name": tool_call["function"]["name"]
                    })

                response = ollama.chat(
                    model="qwen3:4b",
                    messages=messages,
                    tools=tools
                )

            # Continue the conversation
            user_input = input("\nYou: ").strip()

            if user_input.lower() == "exit":

                print("Goodbye!")
                break

            if not user_input:
                continue

            messages.append({
                "role": "user",
                "content": user_input
            })

        except Exception as error:

            print("\nAn error occurred:", error)

            user_input = input(
                "\nTry again or type exit: "
            ).strip()

            if user_input.lower() == "exit":
                break

            messages.append({
                "role": "user",
                "content": user_input
            })


# ==========================================
# 9. MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    project_requirements = collect_requirements()

    start_agent(project_requirements)
