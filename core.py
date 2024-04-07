from sqlalchemy import text, insert, delete, select
from database import async_engine, session_factory
from models import Base, OrganizationsOrm, EmployeesOrm, OrgEmpOrm
from tabulate import tabulate
import prettytable as pt


async def to_table(rows):
    headers = ["Краткое наименование орг.",
               "ИНН",
               "Лицензия орг.",
               "Вид деятельности орг.",
               "Ф.И.О",
               "Надзорное управление",
               "Тип полномочий",
               "Тип сотрудника",
               "Назначен с",
               "Назначен до"]
    table = pt.PrettyTable(headers)
    for row in rows:
        table.add_row(row)
    return table


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def get_organization(org_name):
    query = (
        select(
            OrganizationsOrm.name.label("org_name"),
            OrganizationsOrm.inn,
            OrganizationsOrm.license,
            OrganizationsOrm.activity_type,
            EmployeesOrm.name,
            EmployeesOrm.department,
            OrgEmpOrm.authority_type,
            OrgEmpOrm.employee_type,
            OrgEmpOrm.period_from,
            OrgEmpOrm.period_to
        )
        .select_from(OrganizationsOrm)
        .join(OrgEmpOrm, OrgEmpOrm.organization_id == OrganizationsOrm.id)
        .join(EmployeesOrm, EmployeesOrm.id == OrgEmpOrm.employee_id)
        .where(OrganizationsOrm.name.ilike(f'%{org_name}%'))
    )
    async with session_factory() as session:
        result = await session.execute(query)
        result = result.all()
        return await to_table(result)


async def get_employee(employee):
    query = (
        select(
            OrganizationsOrm.name.label("org_name"),
            OrganizationsOrm.inn,
            OrganizationsOrm.license,
            OrganizationsOrm.activity_type,
            EmployeesOrm.name,
            EmployeesOrm.department,
            OrgEmpOrm.authority_type,
            OrgEmpOrm.employee_type,
            OrgEmpOrm.period_from,
            OrgEmpOrm.period_to
        )
        .select_from(EmployeesOrm)
        .join(OrgEmpOrm, OrgEmpOrm.employee_id == EmployeesOrm.id)
        .join(OrganizationsOrm, OrganizationsOrm.id == OrgEmpOrm.organization_id)
        .where(EmployeesOrm.name.ilike(f'%{employee}%'))
    )
    async with session_factory() as session:
        result = await session.execute(query)
        result = result.all()
        return await to_table(result)


async def supervised_insert(data):
    employee_keys = ["employee_name",
                     "department"]

    organization_keys = ["organization_name",
                         "inn",
                         "license",
                         "activity_type"]

    junction_keys = ["authority_type",
                     "employee_type",
                     "period_from",
                     "period_to"]

    employee_data = []
    organization_data = []
    junction_data = []
    employee_names = []
    organization_names = []
    async with session_factory() as session:

        for row in data:
            print(row)

            employee_row = {key: value for key, value in row.items() if key in employee_keys}
            employee_row["name"] = employee_row["employee_name"]
            del employee_row["employee_name"]

            organization_row = {key: value for key, value in row.items() if key in organization_keys}
            organization_row["name"] = organization_row["organization_name"]
            del organization_row["organization_name"]

            junction_row = {key: value for key, value in row.items() if key in junction_keys}
            junction_data.append(junction_row)

            organization_names.append(organization_row["name"])
            employee_names.append(employee_row["name"])

            employee_result = await session.execute(
                select(EmployeesOrm).where(EmployeesOrm.name == employee_row["name"]))
            employee_exists = (employee_result.fetchone() is not None)

            organization_result = await session.execute(
                select(OrganizationsOrm).where(OrganizationsOrm.name == organization_row["name"]))
            organization_exists = (organization_result.fetchone() is not None)

            if not employee_exists:
                employee_data.append(EmployeesOrm(**employee_row))

            if not organization_exists:
                organization_data.append(OrganizationsOrm(**organization_row))

        for idx in range(len(employee_data)):
            await session.merge(employee_data[idx])
        for idx in range(len(organization_data)):
            await session.merge(organization_data[idx])

        await session.flush()
        await session.commit()

        query_employee = select(EmployeesOrm.id, EmployeesOrm.name).where(
            EmployeesOrm.name.in_(employee_names))
        query_organization = select(OrganizationsOrm.id, OrganizationsOrm.name).where(
            OrganizationsOrm.name.in_(organization_names))

        employee_idx = await session.execute(query_employee)
        organization_idx = await session.execute(query_organization)

        emp2idx = {row.name: row.id for row in employee_idx}
        org2idx = {row.name: row.id for row in organization_idx}

        junction = []
        for idx, row in enumerate(junction_data):
            junction_data[idx]["employee_id"] = emp2idx[employee_names[idx]]
            junction_data[idx]["organization_id"] = org2idx[organization_names[idx]]
            junction.append(OrgEmpOrm(**row))
        for idx in range(len(junction)):
            await session.merge(junction[idx])

        await session.flush()
        await session.commit()
