from sqlalchemy import Table, Column, Integer, String, MetaData, func, text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base, str_256
import enum
from sqlalchemy import ForeignKey
import datetime
from typing import Annotated

intpk = Annotated[int, mapped_column(primary_key=True)]


class OrganizationsOrm(Base):
    __tablename__ = "organization"

    id: Mapped[intpk]
    name: Mapped[str]
    inn: Mapped[int]
    license: Mapped[str]
    activity_type: Mapped[str]
    curators: Mapped[list["EmployeesOrm"]] = relationship(back_populates="organization", secondary="orgemployee")


class EmployeesOrm(Base):
    __tablename__ = "employee"

    id: Mapped[intpk]
    name: Mapped[str]
    department: Mapped[str]
    organization: Mapped[list["OrganizationsOrm"]] = relationship(back_populates="curators",
                                                                  secondary="orgemployee")


class OrgEmpOrm(Base):
    __tablename__ = "orgemployee"

    employee_id: Mapped[int] = mapped_column(ForeignKey("employee.id", ondelete="CASCADE"), primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"), primary_key=True)
    authority_type: Mapped[str] = mapped_column()
    employee_type: Mapped[str] = mapped_column()
    period_from: Mapped[datetime.date]
    period_to: Mapped[datetime.date]
    __table_args__ = (
        CheckConstraint(authority_type.in_(["основной", "продление"]), name='check_authority_type_values'),
        CheckConstraint(employee_type.in_(["куратор", "замещающий куратор", "ответственное лицо"]),
                        name='check_employee_type_values'))
