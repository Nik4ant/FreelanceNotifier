import queue
from collections import deque
from typing import Union, Any

from config import ORDER_LAST_TITLES_STARTUP

import aiohttp
from bs4 import BeautifulSoup, Tag


# TODO: enter all needed data here for easily usage earlier
class WebDataForParsing:
    def __init__(self):
        pass


# Container representing order on freelance
# TODO: docs and stuff
class OrderContainer:
    # TODO: maybe make price int (but for now this is doesn't matter)
    def __init__(self, title: str, description: str, url: str, min_price: str, max_price: str):
        self.title = title
        self.description = description
        self.url = url
        self.min_price = min_price
        self.max_price = max_price

    def __str__(self):
        return f"{self.title}\n{self.description}\n\n{self.url}\nMin: {self.min_price}\nMax: {self.max_price}"


class OrdersParser:
    # Note(Nik4ant): THIS IS ONLY FOR TESTING!!!! I will change it later
    # TODO: change later
    BASE_URL = "http://kwork.ru/projects?{0}&page={1}"
    KWORK_CATEGORIES_URL_ARG = {
        "scripts": "c=41",
        "desktop": "c=80",
    }

    def __init__(self, new_order_handler: callable):
        super().__init__()
        # Deque with all current orders (order will be removed from
        # deque as soon as it will be handled)
        self.orders_queue = deque()
        # Handler that will be called if new order is found
        self.new_order_handler = new_order_handler
        # Categories from KWORK_CATEGORIES_URL_ARG that will be checking every time
        self.needed_categories = ["scripts", "desktop"]
        # Last orders titles for determining new orders
        self.last_order_titles: dict = ORDER_LAST_TITLES_STARTUP.copy()

    async def check_for_new_orders(self) -> None:
        await self.update_orders()
        while len(self.orders_queue) != 0:
            self.new_order_handler(self.orders_queue.pop())

    async def update_orders(self) -> None:
        for current_category in self.needed_categories:
            # Flag for end and current page num
            is_end_of_new_orders = False
            # Will be updated on first iteration. New title for each category
            # this is first parsed title if it doesn't match with the old one
            new_title = None
            # Current page num and max pages count (will be parsed)
            current_page_num = 1
            max_pages_count = None
            # Parsing all orders on all pages until we find already parsed order
            while not is_end_of_new_orders:
                formatted_url = self.BASE_URL.format(self.KWORK_CATEGORIES_URL_ARG[current_category],
                                                     str(current_page_num))
                soup = BeautifulSoup(await self.get_html_page(formatted_url), "lxml")
                # Select all orders tags and extracting data from them
                for order_tag in soup.find_all("div", {"class": "card__content pb5"}):
                    order_tag: Tag
                    # Title tag with link on order and title itself
                    title_tag = order_tag.findChild().findChild().findChild().findChild().findChild()
                    # Order title
                    title = title_tag.text
                    # If this order was parsed already parser stops
                    # (Also updating last title)
                    if new_title is None:
                        new_title = title
                    if title == self.last_order_titles[current_category]:
                        is_end_of_new_orders = True
                        break
                    # Other order data
                    order_url = title_tag.attrs.get("href") + "/view"
                    description = order_tag.select_one("div.mb15 div.d-flex.relative div.wants-card__left div.wants-card__description-text.br-with-lh div.breakwords.first-letter.js-want-block-toggle.js-want-block-toggle-full").text.rstrip(" Скрыть")
                    min_price = ''.join(soup.select_one("div.mb15 div.d-flex.relative div.wants-card__right.m-hidden div div div").text.split()[3:5])
                    # TODO: check if price parsing correctly
                    # This tag doesn't appear every time so need to check for it
                    max_price = ''.join(soup.select_one("div.mb15 div.d-flex.relative div.wants-card__right.m-hidden div.wants-card__description-higher-price span.nowrap").text.split()[1:3])
                    self.orders_queue.append(OrderContainer(title, description, order_url, min_price, max_price))
                # Parsing how many pages we have if parser don't know it yet
                if max_pages_count is None:
                    # Note(Nik4ant): This isn't best way for selecting last page num, but works
                    pages_tag = soup.select_one("div[class='p1']").findChild()
                    max_pages_count = int(pages_tag.select("li")[-2].findChild().text)
                # Incrementing page num
                current_page_num += 1
                if current_page_num > max_pages_count:
                    break
            # Updating last title for current category
            self.last_order_titles[current_category] = new_title

    @staticmethod
    async def get_html_page(url: str) -> Union[Any, bytes]:
        async with aiohttp.client.ClientSession() as session:
            async with session.get(url) as response:
                return await response.read()
