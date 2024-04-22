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
    """ Create new row in cart table with customer"""

    with db.engine.begin() as connection:
        try:
            sql_to_execute = "SELECT id FROM customer WHERE name = :name AND class = :class AND level = :level"
            result = connection.execute(sqlalchemy.text(sql_to_execute), [{"name": new_cart.customer_name, 
                                                                           "class": new_cart.character_class,
                                                                           "level": new_cart.level}]).fetchall()[0]
            print(f"Result {result} When customer exists")
        except:
            sql_to_execute = "INSERT INTO customer (name, class, level) VALUES (:name, :class, :level) RETURNING id"
            result = connection.execute(sqlalchemy.text(sql_to_execute), [{"name": new_cart.customer_name, 
                                                                           "class": new_cart.character_class,
                                                                           "level": new_cart.level}]).fetchall()[0]
            print(f"Result {result} if customer doesn't exist")
            
        customer_id = result.id
        sql_to_execute = "INSERT INTO cart (customer_id) VALUES (:id) RETURNING cart_id"
        cart_id = connection.execute(sqlalchemy.text(sql_to_execute), [{"id": customer_id}]).fetchall()[0].cart_id
        print(f"Final id returned after cart insert: {cart_id}")

    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ Post items to cart_items """

    print(f"Cart: {cart_id} | SKU: {item_sku} | {cart_item.quantity}")
    sql_to_execute = "SELECT potion_id FROM potions_table WHERE sku = :sku"
    with db.engine.begin() as connection:
        potion_id = connection.execute(sqlalchemy.text(sql_to_execute), [{"sku": item_sku}]).fetchall()[0][0]
        sql_to_execute = "INSERT INTO cart_items (cart_id, quantity, potion_id) VALUES (:cart_id, :quantity, :potion_id)"
        result = connection.execute(sqlalchemy.text(sql_to_execute), [{"cart_id": cart_id,
                                                                       "quantity": cart_item.quantity, 
                                                                       "potion_id": potion_id}])
    
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ Retrieve all items with cart_id and sum """
    
    gold = 0
    potions_bought = 0
    with db.engine.begin() as connection:
        sql_to_execute = "SELECT potion_id, quantity FROM cart_items WHERE cart_id = :cart_id"
        carts = connection.execute(sqlalchemy.text(sql_to_execute), [{"cart_id": cart_id}]).fetchall()

        # Get potion price and quantity denoted by sku
        sql_to_execute = f"UPDATE potions_table SET quantity = quantity - :quantity WHERE potion_id = :potion_id RETURNING price"
        for purchase in carts:
            potion_price = connection.execute(sqlalchemy.text(sql_to_execute), 
                                              [{"quantity": purchase.quantity, "potion_id": purchase.potion_id}]).fetchall()[0][0] * purchase.quantity
            print(potion_price)
            gold += potion_price
            potions_bought += purchase.quantity

        # Update SQL database with new gold and poion amount
        sql_to_execute = f"UPDATE global_inventory SET gold = gold - :gold"
        update = connection.execute(sqlalchemy.text(sql_to_execute), [{"gold": gold}])
    
    return {"total_potions_bought": potions_bought, "total_gold_paid": gold}


