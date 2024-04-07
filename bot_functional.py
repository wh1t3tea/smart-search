import aiogram
import asyncio
from os import getenv
from aiogram import Bot, Dispatcher, types, F, Router, html
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from core import get_employee, get_organization, supervised_insert
import datetime
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


class Form(StatesGroup):
    MainMenu = State()
    GetQuery = State()
    SetQuery = State()
    GetEmployee = State()
    GetOrg = State()
    UpdateData = State()
    Start = State()


TOKEN = "7176999211:AAE_ZFTWTUII192R25uakA8i-GaTfEfqsOQ"

form_router = Router()

@form_router.message(Command("cancel"))
@form_router.message(F.text.casefold() == "Главное меню")
@form_router.message(Form.Start)
@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(Form.MainMenu)
    await message.answer(
        "Выберите функцию",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Поиск"),
                    KeyboardButton(text="Обновление данных"),
                ]
            ],
            resize_keyboard=True,
        )
    )


@form_router.message(Command("cancel"))
@form_router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await state.set_state(Form.Start)


@form_router.message(Form.MainMenu)
async def process_query(message: Message, state: FSMContext) -> None:
    if message.text == "Поиск":
        await state.set_state(Form.GetQuery)
        await message.answer("Выберите, что вы хотите искать",
                             reply_markup=ReplyKeyboardMarkup(
                                 keyboard=[
                                     [
                                         KeyboardButton(text="Сотрудника"),
                                         KeyboardButton(text="Организацию"),
                                     ]
                                 ],
                                 resize_keyboard=True,
                             ),
                             )
    elif message.text == "Обновление данных":
        await state.set_state(Form.SetQuery)
        await message.answer("Выберите, тип обновления данных",
                             reply_markup=ReplyKeyboardMarkup(
                                 keyboard=[[
                                     KeyboardButton(text="Добавить строчку из Excel таблицы.")
                                 ]],
                                 resize_keyboard=True,
                             ),
                             )


@form_router.message(Form.GetQuery)
async def employee_seach(message: Message, state: FSMContext) -> None:
    if message.text == "Сотрудника":
        await state.set_state(Form.GetEmployee)
        await message.answer(
            "Напишите фамилию сотрудника используя любой регистр или используйте полную форму запроса:\n'Фамилия И.О.'",
            reply_markup=ReplyKeyboardRemove())
    elif message.text == "Организацию":
        await state.set_state(Form.GetOrg)
        await message.answer(
            "Напишите название компании не используя аббревиатуры.\nНапример для поиска компании 'ОА Ромашка' необходимо написать 'ромашка' в любом регистре.",
            reply_markup=ReplyKeyboardRemove())


@form_router.message(Form.GetEmployee)
async def request_employee(message: Message, state: FSMContext) -> None:
    if message.text == "Главное меню":
        await state.set_state(Form.Start)
        await message.answer("Главное меню:", reply_markup=ReplyKeyboardRemove())
    else:
        result = await get_employee(message.text.lower())
        await message.answer(f"Вот что удалось найти по запросу: {message.text}\n```{result}```",
                             parse_mode="MarkdownV2",
                             reply_markup=ReplyKeyboardMarkup(
                                 keyboard=[[
                                     KeyboardButton(text="Главное меню")
                                 ]],
                                 resize_keyboard=True,
                             ),)


@form_router.message(Form.GetOrg)
async def request_organization(message: Message, state: FSMContext) -> None:
    if message.text == "Главное меню":
        await state.set_state(Form.Start)
        await message.answer("Главное меню", reply_markup=ReplyKeyboardRemove())
    else:
        result = await get_organization(message.text.lower())
        await message.answer(f"Вот что удалось найти по запросу: {message.text}\n```{result}```",
                             parse_mode="MarkdownV2",
                             reply_markup=ReplyKeyboardMarkup(
                                     keyboard=[[
                                         KeyboardButton(text="Главное меню")
                                     ]],
                                     resize_keyboard=True,
                                 ),)


@form_router.message(Form.SetQuery)
async def organization_search(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.UpdateData)
    await message.answer(f"Введите данные в следующем формате:\nКраткое наименование организации, ИНН, Лицензия, Вид деятельности, Надзорное управление, Ф.И.О сотрудника, Тип полномочий, Тип сотрудника, Назначен с, Назначен по",
            reply_markup=ReplyKeyboardRemove())


@form_router.message(Form.UpdateData)
async def update_excel_format(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.Start)
    try:
        prepocessed_data = preprocess_excel_data(message)
        print(prepocessed_data)
        await supervised_insert(prepocessed_data)
    except Exception as e:
        print(e)
        await message.answer(f"Ошибка. Перепроверьте ввод данных.",
                         reply_markup=ReplyKeyboardRemove())
    await message.answer(f"Данные были успешно сохранены",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[
                                 KeyboardButton(text="Главное меню")
                             ]],
                             resize_keyboard=True,
                         ),)


def preprocess_excel_data(message: Message) -> list[dict]:
    table_keys = ["organization_name",
                  "inn",
                  "license",
                  "activity_type",
                  "department",
                  "employee_name",
                  "authority_type",
                  "employee_type",
                  "period_from",
                  "period_to"]
    data = message.text.split("\n")
    rows = []
    for idx, row in enumerate(data):
        row2table = {}
        preprocessed_row = row.split(", ")
        for i in range(len(table_keys)):
            row2table[table_keys[i]] = preprocessed_row[i]
            if table_keys[i] == "inn":
                row2table[table_keys[i]] = int(preprocessed_row[i])
            if table_keys[i] in ["period_from", "period_to"]:
                row2table[table_keys[i]] = datetime.datetime.strptime(preprocessed_row[i], "%Y.%m.%d").date()
        rows.append(row2table)
    return rows


async def main():
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())