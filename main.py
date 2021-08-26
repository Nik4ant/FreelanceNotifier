from orders_parser import OrdersParser
from bot_server import BotServer
from config import API_TOKEN, GROUP_ID, ORDERS_UPDATE_DELAY_SECONDS

import asyncio


async def order_parser_scheduler():
    # TODO: make custom scheduler as i did before
    parser.check_for_new_orders()
    await asyncio.sleep(ORDERS_UPDATE_DELAY_SECONDS)


async def main():
    await order_parser_scheduler()
    await bot_server.process()
    asyncio.ensure_future(main())
    print("Repeat")


loop = asyncio.get_event_loop()
# Bot and parser
bot_server = BotServer(API_TOKEN, GROUP_ID)
parser = OrdersParser(new_order_handler=bot_server.new_order_handler)
try:
    # Running loop
    asyncio.ensure_future(main())
    loop.run_forever()
finally:
    loop.close()
