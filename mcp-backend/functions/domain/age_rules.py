"""Completed calendar years; February 29 advances on March 1 in non-leap years."""
from datetime import date
from typing import Optional


def calendar_age(birth_date: date, as_of: date) -> Optional[int]:
    if not isinstance(birth_date, date) or not isinstance(as_of, date):
        return None
    age = as_of.year - birth_date.year - ((as_of.month, as_of.day) < (birth_date.month, birth_date.day))
    return age if age >= 0 else None
