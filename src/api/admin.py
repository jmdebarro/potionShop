from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """

    sql_to_execute = "UPDATE global_inventory SET green_ml = 0, red_ml = 0, blue_ml = 0, dark_ml = 0, gold = 100"
    with db.engine.begin() as connection:
        update = connection.execute(sqlalchemy.text(sql_to_execute))
        sql_to_execute = "UPDATE potions_table SET quantity = 0"
        update = connection.execute(sqlalchemy.text(sql_to_execute))
    return "OK"

