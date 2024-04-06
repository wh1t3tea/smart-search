import datetime
from core import create_tables, get_organization, get_employee, supervised_insert
import asyncio
import argparse


async def main(arg):
    #await create_tables()
    #await get_organization(arg.name)
    #await get_employee(arg.name)
    #data = [{"employee_name": "Антонов К.В",
            #  "department": "ДЕП №3",
            #  "organization_name": "Тинькофф банк",
            #  "inn": 7319392,
            #  "license": "1213-23213-2",
            #  "activity_type": "ДЕЯТ 3",
            #  "period_from": datetime.date(2024, 1, 10),
            #  "period_to": datetime.date(2024, 3, 10),
            #  "authority_type": "продление",
            #  "employee_type": "замещающий куратор"},
            # {"employee_name": "Сидоров А.В",
            #  "department": "ДЕП №2",
            #  "organization_name": "АО Ромашка",
            #  "inn": 77101396,
            #  "employee_type": "ответственное лицо",
            #  "license": "079-13893-010000...",
            #  "activity_type": "ПУРЦБ и ИС",
            #  "period_from": datetime.date(2024, 1, 10),
            #  "period_to": datetime.date(2024, 3, 10),
            #  "authority_type": "основной"}
            # ]
    await supervised_insert(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    asyncio.run(main(parser.parse_args()))

