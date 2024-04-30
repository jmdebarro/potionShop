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

    sql_to_execute = "DELETE FROM ml_ledger"
    with db.engine.begin() as connection:
        update = connection.execute(sqlalchemy.text(sql_to_execute))
        sql_to_execute = "DELETE FROM gold_ledger"
        update = connection.execute(sqlalchemy.text(sql_to_execute))
        sql_to_execute = "DELETE FROM potion_ledger"
        update = connection.execute(sqlalchemy.text(sql_to_execute))
        sql_to_execute = "INSERT INTO gold_ledger (gold, ml_cap, potion_cap) VALUES (100, 1, 1)"
        update = connection.execute(sqlalchemy.text(sql_to_execute))
    return "OK"

