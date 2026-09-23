import logging
import sys
from aiohttp import web

from asgiref.sync import sync_to_async

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from environs import Env

from utilities import ai_handler

env = Env()
env.read_env()
TOKEN = env.str("TOKEN")
BASE_WEBHOOK_URL = "https://nononerous-philomena-cluelessly.ngrok-free.dev"
WEBHOOK_PATH = f"/webhook/bot/{TOKEN}"
WEBHOOK_URL = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"

SECRET_TOKEN = "SuperSecretToken123"

WEB_SERVER_HOST = "127.0.0.1"
WEB_SERVER_PORT = 8080

router = Router()
dp = Dispatcher()
dp.include_router(router)
bot = Bot(token=TOKEN)

class BotState(StatesGroup):
    image = State()
    checking = State()
    add_to_database = State()

def text_build(response):
    answer = ""
    for q in response:
        answer += (f"{q['name']} - {q['qty']}\n")

    return answer

def list_btn_builder(response):
    response_btn = InlineKeyboardBuilder()
    for i in (response):
        if i["status"] == "matched":
            response_btn.button(text=f"{i['id']}", callback_data=f"item:{i['id']}")
        else:
            response_btn.button(text=f"❌{i['id']}", callback_data=f"item:{i['id']}")
    response_btn.adjust(2)
    response_btn.row(InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approved"))

    return response_btn

@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await message.answer(f"Salom. Mahsulotlar ro'yhatini yuboring.")
    await state.set_state(BotState.image)

@router.message(F.photo)
async def handler(message: Message, state: FSMContext):
    photo = message.photo[-1]
    await bot.download(file=photo.file_id, destination="saved_image.jpg")
    await message.answer("Iltimos kuting ...")
    response = await sync_to_async(ai_handler)()

    await state.update_data(response=response)
   
    await message.answer(text_build(response), reply_markup=list_btn_builder(response).as_markup())

@router.callback_query(F.data.startswith("item:"))
async def check(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    response = data.get("response", [])
    index = call.data.split(":")[1]

    answer = ""
    for q in response:
        if q['id'] == int(index) and q['status'] == "matched":
            answer += (f"❌{q['name']} - {q['qty']}\n")
            q['status'] = "removed"
            q['name'] = "❌" + q['name']
        else:
            if q['id'] == int(index) and q['status'] == "removed":
                answer += (f"{q['name']} - {q['qty']}\n")
                await call.answer("❌ Bu mahsulot allaqachon o'chirilgan.")

            else:
                answer += (f"{q['name']} - {q['qty']}\n")

    await call.message.edit_text(answer, reply_markup=list_btn_builder(response).as_markup())


@router.callback_query(F.data==("approved"))
async def add_data(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer("✅ Mahsulotlar qo'shildi.")

async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=SECRET_TOKEN,
        drop_pending_updates=True
    )
    logging.info(f"Webhook set to: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook()
    await bot.session.close()
    logging.info("Webhook deleted and bot session closed.")


def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=SECRET_TOKEN,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()