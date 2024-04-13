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
    red, green, blue = getMl()
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            red -= potion.potion_type[0] * potion.quantity
            green -= potion.potion_type[1] * potion.quantity
            blue -= potion.potion_type[2] * potion.quantity

            sql_to_execute = f"SELECT * FROM potions_table WHERE red = {potion.potion_type[0]} AND green = {potion.potion_type[1]} AND blue = {potion.potion_type[2]}"
            result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0]
            print(result)
            #Check if row exists
            if result:
                cur_quantity = result.quantity + potion.quantity
                sql_to_execute = f"UPDATE potions_table SET quantity = {cur_quantity} WHERE sku = '{result.sku}'"
                update = connection.execute(sqlalchemy.text(sql_to_execute))
            else:
                # Not relevant until we do unique potions
                continue
    # Subtract ml used for potions
    sql_to_execute = f"UPDATE global_inventory SET num_green_ml = {green}, num_red_ml = {red}, num_blue_ml = {blue}"
    result = connection.execute(sqlalchemy.text(sql_to_execute))



@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    red_ml, green_ml, blue_ml = getMl()
    # Break ml into potion and leftover
    green_potions = green_ml // 100
    red_potions = red_ml // 100
    blue_potions = blue_ml // 100

    return potionsToBottle(red_potions, green_potions, blue_potions)


def potionsToBottle(red, green, blue):
    potionList = []
    if red > 0:
        potionList.append({
                    "potion_type": [100, 0, 0, 0],
                    "quantity": red,
                })
    if green > 0:
        potionList.append({
                    "potion_type": [0, 100, 0, 0],
                    "quantity": green,
                })
    if blue > 0:
        potionList.append({
                "potion_type": [0, 0, 100, 0],
                "quantity": blue,
            })
    return potionList


def getMl():
    '''Returns current ml for every color and gold'''
    sql_to_execute = "SELECT * FROM global_inventory"
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0]
        green_current_ml = result.num_green_ml
        red_current_ml = result.num_red_ml
        blue_current_ml = result.num_blue_ml
    return red_current_ml, green_current_ml, blue_current_ml


if __name__ == "__main__":
    print(get_bottle_plan())