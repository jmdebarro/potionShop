import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int


@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ Potion order leads to updated ml and potion quantity"""
    try:    
        sql_to_execute = "INSERT INTO process (id, type) VALUES (:id, 'potion')"
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text(sql_to_execute), [{"id": order_id}])
        if len(potions_delivered) == 0:
            print("No potions delivered")
        else:
            deliverPotions(potions_delivered)    
            print(f"potions delievered: {potions_delivered} order_id: {order_id}")

        return "OK"
    except:
        print(f"Order {order_id} already delivered")

        return "OK"


def deliverPotions(potions_delivered):
    '''Handles SQL UPDATES for potion delivery'''
    red = green = blue = dark = 0
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            red += potion.potion_type[0] * potion.quantity
            green += potion.potion_type[1] * potion.quantity
            blue += potion.potion_type[2] * potion.quantity
            dark += potion.potion_type[3] * potion.quantity

            sql_to_execute = f"SELECT potion_id FROM potions_table WHERE red = :red AND green = :green AND blue = :blue AND dark = :dark"
            vals = [{"red": potion.potion_type[0], "green": potion.potion_type[1], "blue": potion.potion_type[2], "dark": potion.potion_type[3]}]
            result = connection.execute(sqlalchemy.text(sql_to_execute), vals).fetchall()[0]
            potion_id = result.potion_id

            sql_to_execute = "INSERT INTO potion_ledger (potion_id, change) VALUES (:potion_id, :change)"
            update = connection.execute(sqlalchemy.text(sql_to_execute), [{"potion_id" : potion_id, "change": potion.quantity}])
        # Subtract ml used for potions
        sql_to_execute = "INSERT INTO ml_ledger (red, green, blue, dark) VALUES (:red, :green, :blue, :dark)"
        result = connection.execute(sqlalchemy.text(sql_to_execute), [{"red": -1 * red, "green": -1 * green, "blue": -1 * blue, "dark": -1 * dark}])



@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    red_ml, green_ml, blue_ml, dark_ml = getMl()

    return bottlePotions(red_ml, green_ml, blue_ml, dark_ml)

def bottlePotions(red, green, blue, dark):
    '''Bottle potions'''

    potion_list = []
    with db.engine.begin() as connection:
        sql_to_execute = "SELECT p.potion_id, COALESCE(p.red, 0), COALESCE(p.green, 0), COALESCE(p.blue, 0), (COALESCE(p.dark, 0)), COALESCE(SUM(pl.change), 0) AS quantity\
                            FROM potions_table AS p\
                            LEFT JOIN potion_ledger AS pl ON pl.potion_id = p.potion_id\
                            GROUP BY p.potion_id;"
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()
        print(result)
        for potion in result:
            potion_type = [potion.red, potion.green, potion.blue, potion.dark]
            quantity = 0
            while min(red - potion.red, green - potion.green, blue - potion.blue, dark - potion.dark) >= 0 and quantity < 5:
                quantity += 1
                red -= potion.red
                blue -= potion.blue
                green -= potion.green
                dark -= potion.dark
            if quantity != 0:
                potion_list.append({
                    "potion_type" : potion_type,
                    "quantity": quantity
                })
    print(potion_list)
    return potion_list


def getMl():
    '''Returns current ml for every color and gold'''
    sql_to_execute = "SELECT COALESCE(SUM(red), 0), SELECT COALESCE(SUM(green), 0), SELECT COALESCE(SUM(blue), 0), SELECT COALESCE(SUM(dark), 0) FROM ml_ledger"
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0]
        red_current_ml = result[0]
        green_current_ml = result[1]
        blue_current_ml = result[2]
        dark_current_ml = result[3]
    return red_current_ml, green_current_ml, blue_current_ml, dark_current_ml


if __name__ == "__main__":
    print(get_bottle_plan())