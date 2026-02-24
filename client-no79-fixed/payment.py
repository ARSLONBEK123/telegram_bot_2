import aiohttp
import asyncio

CREATE_URL = "https://alpha-smm.com/order/create"
STATUS_URL = "https://alpha-smm.com/order/status/{}"

async def create_payment(amount: float, payment_type: str):
    payload = {
        "product_name": "SMMCHI Balance",   
        "amount": amount,
        "payment_type": payment_type
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(CREATE_URL, json=payload) as r:
            return await r.json()

async def check_payment(order_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(STATUS_URL.format(order_id)) as r:
            return await r.json()
            

