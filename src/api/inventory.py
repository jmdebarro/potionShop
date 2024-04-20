from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """

    with db.engine.begin() as connection:
        sql_to_execute = "SELECT green_ml, blue_ml, red_ml, dark_ml, gold FROM global_inventory"
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0]
        total_ml = result.green_ml + result.blue_ml + result.red_ml + result.dark_ml
        total_gold = result.gold

        sql_to_execute = "SELECT SUM(quantity) FROM potions_table"
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0]
        total_potions = result[0]

    print(f"number_of_potions: {total_potions}\nml_in_barrels: {total_ml}\ngold: {total_gold}")
    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": total_gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    with db.engine.begin() as connection:
        sql_to_execute = "SELECT potion_cap, ml_cap, gold FROM global_inventory"
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        gold = result.gold
        ml_cap = result.ml_cap
        potion_cap = result.potion_cap
        
    return {
        "potion_capacity": 0,
        "ml_capacity": 0
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return "OK"
