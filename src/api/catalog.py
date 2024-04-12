import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    sql_to_execute = "SELECT * FROM potions_table WHERE quantity > 0"
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute)).fetchall()
        
    return offerPotions(result)


def offerPotions(potions):
    """Iterates through available potions and addes to catalog"""
    offers, i = 0, 0
    catalogList = []
    length = len(potions)

    while offers < 6 and i < length:
        name = " ".join(potions[i].sku.split("_")).lower()
        catalogList.append({
                    "sku": potions[i].sku,
                    "name": name,
                    "quantity": potions[i].quantity,
                    "price": potions[i].price,
                    "potion_type": [potions[i].red, potions[i].green, potions[i].blue, potions[i].dark]
                })
        i += 1
        offers += 1
    return catalogList