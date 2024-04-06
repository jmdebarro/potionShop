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
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()
        print(result)
        #(id, num_green_potions, num_green_ml, gold)
        num_green_potion = result[0][1]

    return [
            {
                "sku": "GREEN_FANTASY_POTIONS",
                "name": "green potion",
                "quantity": num_green_potion,
                "price": 52,
                "potion_type": [0, 100, 0, 0],
            }
        ]

