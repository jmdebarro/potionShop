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
    """ """
    sql_to_execute = "SELECT * FROM global_inventory"
    barrels_bought = []
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()
        current_gold = result[0][3]
        current_ml = result[0][2]
        # Iterates through barrels you want to purchase from "/plan"
        for barrel in barrels_delivered:
            # If barrel price is below gold available, buy barrel
            if (barrel.price) < current_gold:
                barrels_bought.append(barrel)
                current_gold -= barrel.price
                current_ml += barrel.ml_per_barrel
                sql_to_execute = f"UPDATE global_inventory SET num_green_ml = {current_ml}, gold = {current_gold}"
                update = connection.execute(sqlalchemy.text(sql_to_execute))

    print(f"barrels delievered: {barrels_bought} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    num_green_potion = 0
    sql_to_execute = "SELECT * FROM global_inventory"
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        #(id, num_green_potions, num_green_ml, gold)
        num_green_potion = result.fetchall()[0][1]
    # Write SQL code to check how many barrels you want to buy
    if num_green_potion < 10:
        return [
            {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
            }
        ]
    else:
        return []

