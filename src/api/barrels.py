import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int


@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """Sets barrel ml and gold in db"""
    try:
        sql_to_execute = "INSERT INTO process (id, type) VALUES (:id, 'barrel')"
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text(sql_to_execute), [{"id": order_id}])
        if len(barrels_delivered) == 0:
            print("No barrels delivered")  
        else:
            # Executes sql UPDATE
            buyBarrels(barrels_delivered)
            print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

        return "OK"
    
    except:
        print(f"Order: {order_id} already processed")
        return "OK"


def buyBarrels(barrel_list):
    '''Handles updating db ml and gold'''
    gold = 0
    red = 0
    green = 0
    blue = 0
    dark = 0

    with db.engine.begin() as connection:
        for barrel in barrel_list:
            gold -= barrel.price
            if barrel.potion_type[0] != 0:
                red += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type[1] != 0:
                green += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type[2] != 0:
                blue += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type[3] != 0:
                dark += barrel.ml_per_barrel * barrel.quantity
            else:
                raise Exception("Invalid error type")
        print(f"Green {green} | Red : {red} | Blue: {blue} | Dark: {dark}")
        sql_to_execute = "INSERT INTO ml_ledger (green, red, blue, dark) VALUES (:green, :red, :blue, :dark)"
        update = connection.execute(sqlalchemy.text(sql_to_execute), [{"green": green, "red": red, "blue": blue, "dark": dark}])
        sql_to_execute = "INSERT INTO gold_ledger (gold) VALUES (:gold)"
        update = connection.execute(sqlalchemy.text(sql_to_execute), [{"gold": gold}])


# Gets called every other tick
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ Send request for what you want """
    print(wholesale_catalog)

    return barrelsWanted(wholesale_catalog)


def barrelsWanted(catalog):
    '''Code to check for barrels and if there are sufficient funds'''
    reqBarrels = []
    #sql_to_execute = "SELECT gold, ml_cap, red_ml, green_ml, blue_ml, dark_ml FROM global_inventory"
    sql_to_execute = "SELECT COALESCE(SUM(red), 0), COALESCE(SUM(green), 0), COALESCE(SUM(blue), 0), COALESCE(SUM(dark), 0) FROM ml_ledger"
    with db.engine.begin() as connection:
        ml = connection.execute(sqlalchemy.text(sql_to_execute)).fetchone()
        #(red, green, blue, dark)
        red = ml[0]
        green = ml[1]
        blue = ml[2]
        dark = ml[3]

        sql_to_execute = "SELECT SUM(gold), SUM(ml_cap) FROM gold_ledger"
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchone()
        #(gold, ml_cap, potion_cap)
        gold = result[0]
        threshold = result[1] * 10000 / 4
        current_cap = result[1] * 10000 - red - green - blue - dark
        print(f"Gold: {gold} | Red: {red} | Blue: {blue} | Green: {green} | Dark: {dark}")
        print(f"Threshold: {threshold} | Current_Cap: {current_cap}")


    new_cat = [barrel for barrel in catalog if barrel.ml_per_barrel <= threshold and barrel.price <= gold]
    for barrel in new_cat:
        quantity = 0
        if current_cap - barrel.ml_per_barrel < 0 or gold < barrel.price:
            # Don't have capacity or gold for current barrel
            continue
        # Iterates through barrel listing, adding barrels to order based on ml availability and gold
        elif barrel.potion_type[0] == 1:
            while red + barrel.ml_per_barrel <= threshold and gold >= barrel.price and quantity < barrel.quantity and red + barrel.ml_per_barrel < current_cap:
                quantity += 1
                gold -= barrel.price
                red += barrel.ml_per_barrel
                current_cap -= barrel.ml_per_barrel
        elif barrel.potion_type[1] == 1:
            while green + barrel.ml_per_barrel <= threshold and gold >= barrel.price and quantity < barrel.quantity and red + barrel.ml_per_barrel < current_cap:
                quantity += 1
                gold -= barrel.price
                green += barrel.ml_per_barrel
                current_cap -= barrel.ml_per_barrel
        elif barrel.potion_type[2] == 1:
            while blue + barrel.ml_per_barrel <= threshold and gold >= barrel.price and quantity < barrel.quantity and red + barrel.ml_per_barrel < current_cap:
                quantity += 1
                gold -= barrel.price
                blue += barrel.ml_per_barrel
                current_cap -= barrel.ml_per_barrel
        elif barrel.potion_type[3] == 1:
            while dark + barrel.ml_per_barrel <= threshold and gold >= barrel.price and quantity < barrel.quantity and red + barrel.ml_per_barrel < current_cap:
                quantity += 1
                gold -= barrel.price
                dark += barrel.ml_per_barrel
                current_cap -= barrel.ml_per_barrel
        if quantity > 0:
            reqBarrels.append({
                "sku" : barrel.sku,
                "quantity" : quantity
            })
    print(f"\nCurrent_cap at end: {current_cap} | Total ml: {red + green + blue + dark}")
    return reqBarrels


''' For Testing
[
  {
    "sku": "SMALL_RED_BARREL",
    "ml_per_barrel": 500,
    "potion_type": [
      1,
      0,
      0,
      0
    ],
    "price": 100,
    "quantity": 10
  },
  {
    "sku": "SMALL_GREEN_BARREL",
    "ml_per_barrel": 500,
    "potion_type": [
      0,
      1,
      0,
      0
    ],
    "price": 100,
    "quantity": 10
  },
  {
    "sku": "SMALL_BLUE_BARREL",
    "ml_per_barrel": 500,
    "potion_type": [
      0,
      0,
      1,
      0
    ],
    "price": 120,
    "quantity": 10
  },
  {
    "sku": "MINI_RED_BARREL",
    "ml_per_barrel": 200,
    "potion_type": [
      1,
      0,
      0,
      0
    ],
    "price": 60,
    "quantity": 1
  },
  {
    "sku": "MINI_GREEN_BARREL",
    "ml_per_barrel": 200,
    "potion_type": [
      0,
      1,
      0,
      0
    ],
    "price": 60,
    "quantity": 1
  },
  {
    "sku": "MINI_BLUE_BARREL",
    "ml_per_barrel": 200,
    "potion_type": [
      0,
      0,
      1,
      0
    ],
    "price": 60,
    "quantity": 1
  }
]
'''