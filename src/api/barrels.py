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
    if len(barrels_delivered) == 0:
        print("No barrels delivered")  
    else:
        # Executes sql UPDATE
        buyBarrels(barrels_delivered)
        print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

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
        sql_to_execute = f"""UPDATE global_inventory SET green_ml = green_ml + {green}, 
        gold = gold + {gold}, red_ml = red_ml + {red}, 
        blue_ml = blue_ml + {blue}, dark_ml = dark_ml + {dark}""".replace("\n", "")
        update = connection.execute(sqlalchemy.text(sql_to_execute))


# Gets called every other tick
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ Send request for what you want """
    print(wholesale_catalog)
    colors_needed = checkStorage()

    return barrelsWanted(wholesale_catalog, colors_needed)

    
def checkStorage():
    '''Checks what barrels we need'''
    sql_to_execute = "SELECT red, green, blue, dark FROM potions_table WHERE quantity < 10"
    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()
        colors = [0, 0, 0, 0]      
        for potion in potions:
            colors[0] += potion.red
            colors[1] += potion.green
            colors[2] += potion.blue
            colors[3] += potion.dark
    return colors


def barrelsWanted(catalog, types):
    '''Code to check for barrels and if there are sufficient funds'''
    reqBarrels = []
    if sum(types) == 0:
        return reqBarrels
    
    sql_to_execute = "SELECT gold FROM global_inventory"
    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0].gold

    # Finds colors I need and then checks if barrel is of needed color
    indexes = [i for i in range(4) if types[i] != 0]
    for barrel in catalog:
        for index in indexes:
            if barrel.potion_type[index] != 0:
                if gold >= barrel.price:
                    reqBarrels.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    gold -= barrel.price
                break
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