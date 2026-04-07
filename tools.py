from langchain_core.tools import tool
from pydantic import BaseModel, Field
from data import FLIGHTS_DB, HOTELS_DB
from typing import Dict, Literal, List


def format_price(price: int) -> str:
    """Format số tiền thành dạng 1.450.000₫"""
    return f"{price:,.0f}".replace(",", ".") + "₫"


# =========================
# TOOL 1: SEARCH FLIGHTS
# =========================
class FlightInput(BaseModel):
    """Input for flight queries."""
    origin: Literal["Hà Nội", "Hồ Chí Minh", 'Đà Nẵng', 'Phú Quốc'] = Field(
        description="Departure city or airport code"
    )
    destination: Literal['Đà Nẵng', 'Phú Quốc', 'Hồ Chí Minh', "Hà Nội"] = Field(
        description="Arrival city or airport code"
    )

@tool(args_schema=FlightInput)
def search_flights(origin: str, destination: str) -> str:
    """Get a list of flights with the airline, flight times, and ticket prices."""
    key = (origin, destination)
    reverse_key = (destination, origin)

    flights = None
    reverse = False

    if key in FLIGHTS_DB:
        flights = FLIGHTS_DB[key]
    elif reverse_key in FLIGHTS_DB:
        flights = FLIGHTS_DB[reverse_key]
        reverse = True
    else:
        return f"Không tìm thấy chuyến bay từ {origin} đến {destination}."

    result = []

    if reverse:
        title = f"Không có chuyến bay từ {origin} đến {destination}. Chuyến bay từ {destination} đến {origin}:" 
    else:
        title = f"Chuyến bay từ {origin} đến {destination}:"

    result.append(title)

    for f in flights:
        result.append(
            f"Airline: {f['airline']}, "
            f"Departure: {f['departure']}, "
            f"Arrival: {f['arrival']}, "
            f"Price: {format_price(f['price'])}, "
            f"Class: {f['class']}"
        )

    return "\n".join(result)


# =========================
# TOOL 2: SEARCH HOTELS
# =========================
   
class HotelInput(BaseModel):
    city: Literal['Đà Nẵng', 'Phú Quốc', 'Hồ Chí Minh'] = Field(
        description="City to search hotels in"
    )
    max_price_per_night: int | None = Field(
        default=None,
        description="Maximum price per night (optional)"
    )

@tool(args_schema=HotelInput)
def search_hotels(city: str, max_price_per_night: int = None) -> str:
    """Search hotels by city and optionally filter by max price per night."""
    if city not in HOTELS_DB:
        return f"Không tìm thấy dữ liệu khách sạn tại {city}."

    hotels = HOTELS_DB[city]

    if max_price_per_night:
        filtered = [
            h for h in hotels
            if h["price_per_night"] <= max_price_per_night
        ]
    else:
        filtered = hotels

    if not filtered:
        return f"Không tìm thấy khách sạn tại {city} với giá dưới {format_price(max_price_per_night)}/đêm. Hãy thử tăng ngân sách."


    # sort theo rating giảm dần
    filtered.sort(key=lambda x: x["rating"], reverse=True)

    result = [f"Khách sạn tại {city}:"]

    for h in filtered:
        result.append(
            f"- Name: {h['name']}\n"
            f"  Stars: {h['stars']}\n"
            f"  Price per night: {format_price(h['price_per_night'])}\n"
            f"  Area: {h['area']}\n"
            f"  Rating: {h['rating']}"
        )

    return "\n".join(result)


# =========================
# TOOL 3: CALCULATE BUDGET
# =========================
class Expense(BaseModel):
    name: str = Field(description="Expense item name, for example: airline ticket")
    amount: int = Field(description="Amount (VND)")

class BudgetInput(BaseModel):
    total_budget: int = Field(description="Total budget (VND)")
    expenses: List[Expense]

@tool(args_schema=BudgetInput)
def calculate_budget(total_budget: int, expenses: List[Expense]) -> str:
    """Calculate the remaining budget after deducting expenses."""
    total_expense = sum(e.amount for e in expenses)
    remaining = total_budget - total_expense

    lines = ["Bảng chi phí:"]

    for e in expenses:
        name = e.name.capitalize()
        lines.append(f"{name}: {format_price(e.amount)}")

    lines.append("-------------------")
    lines.append(f"Tổng chi: {format_price(total_expense)}")
    lines.append(f"Ngân sách: {format_price(total_budget)}")

    if remaining >= 0:
        lines.append(f"Còn lại: {format_price(remaining)}")
    else:
        lines.append(f"Vượt ngân sách {format_price(abs(remaining))}! Cần điều chỉnh.")

    return "\n".join(lines)