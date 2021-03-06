from config import EVENT_CHECK_TIMEOUT, GROUP_ID
from orders_parser import OrderContainer

import asyncio
from datetime import datetime

import ujson
import vk_api
# last two for type hints
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from vk_api.vk_api import VkApiMethod  # for type hint


class BotServer:
    def __init__(self, token: str, group_id: int):
        self.vk_session = vk_api.VkApi(token=token)
        self.longpoll = VkBotLongPoll(self.vk_session, group_id)
        self.vk: VkApiMethod = self.vk_session.get_api()
        # Last contacted user
        self.last_user_id = self.vk.messages.getConversations()["items"][0]["conversation"]["peer"]["id"]

    async def process(self):
        # Note(Nik4ant): Without this code would be 25 seconds delay because vk_api method blocks event loop
        try:
            current_loop = asyncio.get_running_loop()
            # Note(Nik4ant): Executor param is None, because asyncio will use default executor
            events = await asyncio.wait_for(current_loop.run_in_executor(None, self.longpoll.check),
                                            timeout=EVENT_CHECK_TIMEOUT)
            # Handling events
            for event in events:
                # Check for button press
                if event.type == VkBotEventType.MESSAGE_EVENT:
                    # If payload type contains in VK api send request to API
                    # else handle it manually
                    payload_type = event.object.payload.get("type")
                    # Handling payloads
                    if payload_type == "open_link":
                        self.vk.messages.sendMessageEventAnswer(
                                    event_id=event.object.event_id,
                                    user_id=event.object.user_id,
                                    peer_id=event.object.peer_id,
                                    event_data=ujson.dumps(event.object.payload))
                    elif payload_type == "delete_message":
                        self.vk.messages.delete(peer_id=event.object.peer_id,
                                                delete_for_all=True,
                                                conversation_message_ids=event.object.conversation_message_id)
        # Note(Nik4ant): Timeout exception will be raised only if there is no events (tested)
        except asyncio.exceptions.TimeoutError:
            pass

    def new_order_handler(self, order):
        self.show_order_info(order, self.last_user_id)

    def show_order_info(self, order: OrderContainer, user_id: int):
        # Configuring keyboard
        order_keyboard = VkKeyboard(inline=True)
        # This button directs to order by url
        order_keyboard.add_callback_button(label="??????????????", color=VkKeyboardColor.POSITIVE,
                                           payload={
                                               "type": "open_link",
                                               "link": order.url
                                           })
        # Note(Nik4ant): This payload isn't mention in docs, it need for detection event in self.process
        order_keyboard.add_callback_button(label="??????????????????????????????", color=VkKeyboardColor.NEGATIVE,
                                           payload={
                                               "type": "delete_message"
                                           })
        self.send_message(f"???????????? ?????????? ({datetime.now().strftime('%H:%M %d.%m')}):\n{order}",
                          user_id, order_keyboard)

    def send_message(self, message_text: str, user_id: int, keyboard: VkKeyboard = None):
        self.vk.messages.send(user_id=user_id,
                              keyboard=keyboard.get_keyboard(),
                              message=message_text,
                              random_id=get_random_id())
