import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum

# global cart id and dictionary
cart_ids = 0
cart = {}

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    global cart_ids
    cart_ids = cart_ids + 1
    return {"cart_id": cart_ids}


class CartItem(BaseModel):
    quantity: int

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    global cart
    cart[cart_id] = (item_sku, cart_item.quantity)
    
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    global cart
    """ """
    # carts[key] = (sku, quantity)
    potions_bought = cart[cart_id][1]
    potion_sku = cart[cart_id][0]

    print("Potion sku:", potion_sku, "\nQuantity:", potions_bought)
    sql_to_execute = "SELECT gold FROM global_inventory"
    with db.engine.begin() as connection:
        # Get gold
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0]
        current_gold = result.gold
        print(current_gold)
        
        # Get potion price and quantity denoted by sku
        sql_to_execute = f"SELECT quantity, price FROM potions_table WHERE sku = '{potion_sku}'"
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0]
        potion_quantity = result.quantity
        potion_price = result.price

        # Get new total gold and reduce potion in inventory
        new_gold = current_gold + potions_bought * potion_price
        new_inventory = potion_quantity - potions_bought

        # Update SQL database with new gold and poion amount
        sql_to_execute = f"UPDATE global_inventory SET gold = {new_gold}"
        update = connection.execute(sqlalchemy.text(sql_to_execute))
        sql_to_execute = f"UPDATE potions_table SET quantity = {new_inventory} WHERE sku = '{potion_sku}'"
        update = connection.execute(sqlalchemy.text(sql_to_execute))
    print("New gold", new_gold)
    # Hardcoding potions bought at the moment
    return {"total_potions_bought": potions_bought, "total_gold_paid": potions_bought * potion_price}


