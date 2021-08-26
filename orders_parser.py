import queue
from typing import List
from collections import deque


class OrdersParser:
    def __init__(self, new_order_handler: callable):
        super().__init__()
        # Deque with all current orders (order will be removed from
        # queue as soon as it will be handled)
        self.orders_queue = deque()
        # Last order id for determining new orders
        self.last_order_id = None
        # Handler that will be called if new order is found
        self.new_order_handler = new_order_handler

    def check_for_new_orders(self) -> None:
        self.update_orders()
        while len(self.orders_queue) != 0:
            self.new_order_handler(self.orders_queue.pop())

    def update_orders(self) -> None:
        self.orders_queue.append("1")
