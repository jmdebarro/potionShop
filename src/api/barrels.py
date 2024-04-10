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
    """ See """
    if len(barrels_delivered) == 0:
        print("No barrels delivered")
        
    else:
        sql_to_execute = "SELECT * FROM global_inventory"
        barrels_bought = []
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0]
            current_gold = result.gold
            green_current_ml = result.num_green_ml
            # Iterates through barrels you want to purchase from "/plan"
            for barrel in barrels_delivered:
                barrels_bought.append(barrel)
                current_gold -= barrel.price
                green_current_ml += barrel.ml_per_barrel
                sql_to_execute = f"UPDATE global_inventory SET num_green_ml = {green_current_ml}, gold = {current_gold}"
                update = connection.execute(sqlalchemy.text(sql_to_execute))

        print(f"barrels delievered: {barrels_bought} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ Send request for what you want """
    print(wholesale_catalog)

    check_green = False
    # Check if green barrel exists
    for barrel in wholesale_catalog:
        if barrel.sku == 'SMALL_GREEN_BARREL':
            check_green = True
    num_green_potion = 0
    sql_to_execute = "SELECT * FROM global_inventory"
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0]
        #(id, num_green_potions, num_green_ml, gold)
        num_green_potion = result.num_green_potions
        gold = result.gold
    # Write SQL code to check how many barrels you want to buy
    if num_green_potion < 10 and gold >= 100 and check_green:
        return [
            {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
            }
        ]
    else:
        return []

