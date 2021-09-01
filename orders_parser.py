import asyncio
import re
from collections import deque
from typing import Union, Any

from config import ORDER_LAST_TITLES_STARTUP, HANDLE_ORDER_TIMEOUT

import aiohttp
from bs4 import BeautifulSoup, Tag


# Container with all order data
class OrderContainer:
    def __init__(self, title: str, description: str, url: str, min_price: str, max_price: str):
        self.title: str = title
        self.description: str = description
        self.format_description()  # for avoiding multiple blank lines
        self.url: str = url
        self.min_price: str = min_price
        self.max_price: str = max_price

    def format_description(self):
        self.description = re.sub("\n{2,}", '\n', self.description)

    def __str__(self):
        if self.max_price:
            return f"{self.title}\n{self.description}\n\n{self.url}\nMin: {self.min_price}\nMax: {self.max_price}"
        return f"{self.title}\n{self.description}\n\n{self.url}\nMin: {self.min_price}\n"


# TODO: add support for multiple web sites with orders (but for now this works fine)
class OrdersParser:
    BASE_URL = "http://kwork.ru/projects?{0}&page={1}"
    # Taking all keys from config.py var for easier changes in the future
    KWORK_CATEGORIES_URL_ARG = dict(zip(ORDER_LAST_TITLES_STARTUP.keys(), ("c=41", "c=80",)))

    def __init__(self, new_order_handler: callable):
        super().__init__()
        # Deque with all current orders (order will be removed from
        # deque as soon as it will be handled)
        self.orders_deque = deque()
        # Handler that will be called if new order is found
        self.new_order_handler = new_order_handler
        # Categories from KWORK_CATEGORIES_URL_ARG that will be checking every time
        self.needed_categories = tuple(self.KWORK_CATEGORIES_URL_ARG.keys())
        # Last orders titles for determining new orders
        self.last_order_titles: dict = ORDER_LAST_TITLES_STARTUP.copy()

    async def check_for_new_orders(self) -> None:
        await self.update_orders()
        while len(self.orders_deque) != 0:
            # In case if there are a lot of messages vk api will freeze for a moment
            # (So if it happens it's better to give control back to event loop)
            # This can be not important with small amount of orders, but if
            # there will be more and more it will slow down bot a lot!
            # Note(Nik4ant): There might be better way to solve this, but i don't know it
            try:
                await asyncio.wait_for(asyncio.get_running_loop().run_in_executor(None, self.new_order_handler, self.orders_deque.pop()), timeout=HANDLE_ORDER_TIMEOUT)
            except asyncio.exceptions.TimeoutError:
                # Giving control back to event loop, while vk api is freezing
                # because of big amount of requests
                await asyncio.sleep(0)

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
                    # Description can be small (fully visible) and big (not fully visible).
                    # These creates 2 different html hierarchy. This one is for big description
                    description_tag = order_tag.select_one("div.mb15 div.d-flex.relative div.wants-card__left div.wants-card__description-text.br-with-lh div.breakwords.first-letter.js-want-block-toggle.js-want-block-toggle-full")
                    # If tag is None then order has small description that parsing differently
                    if description_tag is None:
                        description_tag = order_tag.select_one("div.mb15 div.d-flex.relative div.wants-card__left div.wants-card__description-text.br-with-lh div")
                    description = description_tag.text.rstrip(" Скрыть")
                    # Note: This tag doesn't appear every time
                    max_price_tag = order_tag.select_one("div.mb15 div.d-flex.relative div.wants-card__right.m-hidden div.wants-card__description-higher-price span.nowrap")
                    if max_price_tag is None:
                        max_price = ""
                    else:
                        # Extracting max price from string with price info
                        max_price = self._format_price_string(max_price_tag.text)
                    # Extracting min price from string with price info
                    min_price = self._format_price_string(order_tag.select_one("div.mb15 div.d-flex.relative div.wants-card__right.m-hidden div div div").text)
                    self.orders_deque.append(OrderContainer(title, description, order_url, min_price, max_price))
                # Parsing how many pages we have if parser don't know it yet
                if max_pages_count is None:
                    # Note(Nik4ant): I think this isn't best way for selecting last page num, but it works
                    pages_tag = soup.select_one("div[class='p1']").findChild()
                    max_pages_count = int(pages_tag.select("li")[-2].findChild().text)
                # Incrementing page num
                current_page_num += 1
                if current_page_num > max_pages_count:
                    break
            # Updating last title for current category
            self.last_order_titles[current_category] = new_title

    @staticmethod
    def _format_price_string(line: str) -> str:
        """
        Method that takes only digits from line with price info. Useful, because
        there are a lot of different prefixes for line with price info.
        :param line: Text line with price info
        :return: Price (nums only)
        """
        return ''.join([char for char in line if char.isdigit()])

    @staticmethod
    async def get_html_page(url: str) -> Union[Any, bytes]:
        async with aiohttp.client.ClientSession() as session:
            async with session.get(url) as response:
                return await response.read()
