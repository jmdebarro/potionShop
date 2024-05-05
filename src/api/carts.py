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


    if search_page == "":
        search_page = 0
    else:
        search_page = int(search_page)


    sort_cl = db.orders.c.time
    if sort_col == search_sort_options.customer_name:
        sort_cl = db.orders.c.name
    elif sort_col == search_sort_options.item_sku:
        sort_cl = db.orders.c.item
    elif sort_col == search_sort_options.line_item_total:
        sort_cl = db.orders.c.gold


    order_by = sqlalchemy.desc(sort_cl)
    if sort_order == search_sort_order.asc:
        order_by = sqlalchemy.asc(sort_cl)
    
    total_stmt = (
        sqlalchemy.select(
            db.orders.c.name,
            db.orders.c.item,
            db.orders.c.gold,
            db.orders.c.time
        )
    )

    stmt = (
        sqlalchemy.select(
            db.orders.c.name,
            db.orders.c.item,
            db.orders.c.gold,
            db.orders.c.time
        )
        .limit(5)
        .offset(search_page * 5)
        .order_by(order_by, sort_cl)
    )

    if customer_name != "":
        stmt = stmt.where(db.orders.c.name.ilike(f"%{customer_name}%"))
        total_stmt = total_stmt.where(db.orders.c.name.ilike(f"%{customer_name}%"))
    if potion_sku != "":
        stmt = stmt.where(db.orders.c.item.ilike(f"%{potion_sku}%"))
        total_stmt = total_stmt.where(db.orders.c.name.ilike(f"%{potion_sku}%"))


    with db.engine.connect() as conn:
        length = len(conn.execute(total_stmt).fetchall())
        result = conn.execute(stmt)
        fields = []
        for row in result:
            fields.append(
                {
                    "line_item_id": 1,
                    "item_sku": row.item,
                    "customer_name": row.name,
                    "line_item_total": row.gold,
                    "timestamp": row[3],
                }
            )

    
    if search_page < 5 and ((search_page + 1) * 5) > length:
        next_pg = str(search_page + 1)
    else:
        next_pg = ""

    if search_page > 0:
        prev_pg = str(search_page - 1)
    else:
        prev_pg = ""

    print(f"Search page {search_page} | Next page {next_pg} | Prev page {prev_pg} | Total length {length}")

    return {
        "previous": prev_pg,
        "next": next_pg,
        "results": fields,
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
        sql_to_execute = "INSERT INTO potion_ledger (potion_id, change) VALUES (:potion_id, :change)"
        for purchase in carts:
            insert = connection.execute(sqlalchemy.text(sql_to_execute), 
                                              [{"change": -1 * purchase.quantity, "potion_id": purchase.potion_id}])
            
            sql_to_execute = "SELECT price from potions_table WHERE potion_id = :potion_id"
            amount = connection.execute(sqlalchemy.text(sql_to_execute), [{"potion_id" : purchase.potion_id}]).fetchone()
            gold += amount.price * purchase.quantity
            potions_bought += purchase.quantity

        # Update SQL database with new gold and poion amount
        sql_to_execute = "INSERT INTO gold_ledger (gold) VALUES (:gold)"
        update = connection.execute(sqlalchemy.text(sql_to_execute), [{"gold": gold}])
    
    return {"total_potions_bought": potions_bought, "total_gold_paid": gold}


