from fastmcp import FastMCP
import httpx

API_BASE = "http://localhost:8000/api"

# Initialize MCP
mcp = FastMCP(
    name="RestaurantMCPServer",
    instructions="""
    This server provides tools for managing a restaurant's operations including menu management, customer management, and billing.

    MENU OPERATIONS:
    - Use get_categories() when the user asks "what do you serve" or wants to know about the types of food and drinks available (like Starters, Burgers, Pizza, Beverages).
    - Use get_menu_items() to show the dishes or drinks in a particular group, including their names, descriptions, and whether they’re available.
    - Use get_sizes() to provide portion and price options for a specific dish or drink (for example, regular or large).
    - Use get_full_menu() ONLY if the user asks to see everything on the menu, with all groups, dishes, and prices together.
    
    CUSTOMER MANAGEMENT:
    - Use get_customers() to list all registered customers
    - Use create_customer(first_name, last_name, phone, address) to register new customers

    BILLING WORKFLOW:
    1. First, create a bill using create_bill(customer_id, order_type, payment_method)
    - order_type options: typically "dine-in", "takeout", "delivery"
    - payment_method options: typically "cash", "card", "digital"
    2. Add items to the bill using add_bill_item(bill_id, item_id, size_id, quantity)
    - quantity defaults to 1 if not specified
    - You must specify both item_id and size_id for each item
    3. Use get_bills() to view all bills and their current status
    4. Use cancel_bill(bill_id) if a bill needs to be cancelled
    """
)

# ----------- Menu Tools -----------

@mcp.tool
async def get_full_menu():
    """Get the complete menu structure with categories, subcategories, items, and sizes"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/menu/")
        resp.raise_for_status()
        return resp.json()

@mcp.tool
async def get_categories():
    """Get all types of food and drinks offered"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/categories/")
        resp.raise_for_status()
        return resp.json()

@mcp.tool
async def get_menu_items(category_id: int = 0 , subcategory_id: int = 0):
    """
    Get all menu items, optionally filter by category id or subcategory id.
    Shows name, description, availability
    """
    params = {}
    # tolerate None, empty strings, and 0 from callers
    if category_id != 0:
        try:
            params['subcategory__category'] = int(category_id)
        except Exception:
            params['subcategory__category'] = category_id
    if subcategory_id != 0:
        try:
            params['subcategory'] = int(subcategory_id)
        except Exception:
            params['subcategory'] = subcategory_id
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/items/", params=params)
        resp.raise_for_status()
        return resp.json()

@mcp.tool
async def get_sizes(category_id: int = 0, subcategory_id: int = 0):
    """
    Get all sizes, optionally filter by category id or subcategory id.
    Shows type, group, size names, and prices.
    """
    params = {}
    if category_id != 0:
        try:
            params['subcategory__category'] = int(category_id)
        except Exception:
            params['subcategory__category'] = category_id
    if subcategory_id != 0:
        try:
            params['subcategory'] = int(subcategory_id)
        except Exception:
            params['subcategory'] = subcategory_id
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/sizes/", params=params)
        resp.raise_for_status()
        return resp.json()

# ----------- Customer Tools (unchanged) -----------

@mcp.tool
async def get_customers():
    """List all customers"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/customers/")
        resp.raise_for_status()
        return resp.json()


@mcp.tool
async def check_customer_by_phone(phone: str):
    """Check if a customer exists by phone. Returns {'exists': bool, 'customer': {...}} when found."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/customers/by-phone/", params={'phone': phone})
        resp.raise_for_status()
        return resp.json()

@mcp.tool
async def create_customer(first_name: str, last_name: str, phone: str, address: str):
    """Create a new customer"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE}/customers/", json={
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "address": address
        })
        resp.raise_for_status()
        return resp.json()

# ----------- Bill Tools (unchanged) -----------

@mcp.tool
async def get_bills():
    """Get all bills"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/bills/")
        resp.raise_for_status()
        return resp.json()

@mcp.tool
async def create_bill(customer_id: int, order_type: str, payment_method: str):
    """Create a new bill"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE}/bills/", json={
            "customer": customer_id,
            "order_type": order_type,
            "payment_method": payment_method
        })
        resp.raise_for_status()
        return resp.json()

@mcp.tool
async def cancel_bill(bill_id: int):
    """Cancel an existing bill"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE}/bills/{bill_id}/cancel/")
        resp.raise_for_status()
        return resp.json()

@mcp.tool
async def add_bill_item(bill_id: int, item_id: int, size_id: int, quantity: int = 1):
    """Add item to bill"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE}/bill-items/", json={
            "bill": bill_id,
            "item": item_id,
            "size": size_id,
            "quantity": quantity
        })
        resp.raise_for_status()
        return resp.json()

if __name__ == "__main__":
    #mcp.run()
    mcp.run(transport="http", host="localhost", port=5005)