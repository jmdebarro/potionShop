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
    if len(potions_delivered) == 0:
        print("No potions delivered")
    else:
        deliverPotions(potions_delivered)    
        print(f"potions delievered: {potions_delivered} order_id: {order_id}")

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

            sql_to_execute = f"SELECT * FROM potions_table WHERE red = {potion.potion_type[0]} AND green = {potion.potion_type[1]} AND blue = {potion.potion_type[2]} AND dark = {potion.potion_type[3]}"
            result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0]
            print(result)

            
            sql_to_execute = f"UPDATE potions_table SET quantity = quantity + {potion.quantity} WHERE sku = '{result.sku}'"
            update = connection.execute(sqlalchemy.text(sql_to_execute))
        # Subtract ml used for potions
        sql_to_execute = f"UPDATE global_inventory SET green_ml = {green},red_ml = {red}, blue_ml = {blue}"
        result = connection.execute(sqlalchemy.text(sql_to_execute))



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
        sql_to_execute = f"SELECT id, quantity, red, green, blue, dark FROM potions_table"
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()
        for potion in result:
            potion_type = [potion.red, potion.green, potion.blue, potion.dark]
            quantity = 0
            while min(red - potion.red, green - potion.green, blue - potion.blue, dark - potion.dark) >= 0 and quantity < 4:
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
    sql_to_execute = "SELECT * FROM global_inventory"
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0]
        green_current_ml = result.green_ml
        red_current_ml = result.red_ml
        blue_current_ml = result.blue_ml
        dark_current_ml = result.dark_ml
    return red_current_ml, green_current_ml, blue_current_ml, dark_current_ml


if __name__ == "__main__":
    print(get_bottle_plan())