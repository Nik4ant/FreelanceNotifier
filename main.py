from orders_parser import OrdersParser
from bot_server import BotServer
from config import API_TOKEN, GROUP_ID, ORDERS_UPDATE_DELAY_SECONDS

import time
import asyncio


async def order_parser_scheduler() -> None:
    global global_time_since_orders_update
    # Using this scheduler, because asyncio.sleep isn't good solution for big delay
    if (global_time_since_orders_update is None or
            time.time() - global_time_since_orders_update >= ORDERS_UPDATE_DELAY_SECONDS):
        global_time_since_orders_update = time.time()
        await parser.check_for_new_orders()


async def main():
    await order_parser_scheduler()
    await bot_server.process()
    asyncio.ensure_future(main())


loop = asyncio.get_event_loop()
# Will be used for scheduling time between parser updates
global_time_since_orders_update: float = None
# Bot and parser
bot_server = BotServer(API_TOKEN, GROUP_ID)
parser = OrdersParser(new_order_handler=bot_server.new_order_handler)
try:
    # Running loop
    asyncio.ensure_future(main())
    loop.run_forever()
finally:
    loop.close()
