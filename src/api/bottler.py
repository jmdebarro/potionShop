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
    """ """
    if len(potions_delivered) == 0:
        print("No potions delivered")

    else:
        green_potions = potions_delivered[0].quantity
        sql_to_execute = f"UPDATE global_inventory SET num_green_potions = {green_potions}"
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text(sql_to_execute))

            # get green ml
            sql_to_execute = "SELECT num_green_ml FROM global_inventory"
            result = connection.execute(sqlalchemy.text(sql_to_execute))
            green_ml = result.fetchall()[0][0]
            leftover_green = green_ml - potions_delivered[0].quantity * 100
            sql_to_execute = f"UPDATE global_inventory SET num_green_ml = {leftover_green}"
            result = connection.execute(sqlalchemy.text(sql_to_execute))
            
        print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    sql_to_execute = "SELECT num_green_ml, num_red_ml, num_blue_ml FROM global_inventory"
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0]
        green_ml = result.num_green_ml
        red_ml = result.num_red_ml
        blue_ml = result.num_blue_ml
        print(green_ml)

    # Break green ml into potion and leftover
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

if __name__ == "__main__":
    print(get_bottle_plan())