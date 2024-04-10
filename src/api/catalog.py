import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    num_green_potion = 0
    sql_to_execute = "SELECT * FROM global_inventory"
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()[0]
        num_green_potion = result.num_green_potions

    # Hardcoding potion amount right now
    if num_green_potion > 0:
        return [
                {
                    "sku": "GREEN_POTION",
                    "name": "green potion",
                    "quantity": 1,
                    "price": 30,
                    "potion_type": [0, 100, 0, 0]
                }
            ]
    return []

