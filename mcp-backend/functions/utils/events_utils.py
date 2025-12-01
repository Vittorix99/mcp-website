import datetime
import logging
from datetime import datetime as dt
import re
EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def is_minor(birthdate_str):
    """Restituisce True se la persona è minorenne. Accetta formato 'gg-mm-aaaa'."""
    try:
        birthdate = datetime.datetime.strptime(birthdate_str, "%d-%m-%Y").date()
        print("Birthday is:", birthdate)
        today = datetime.date.today()
        return (today - birthdate).days // 365 < 18
    except Exception:
        return True  # In caso di parsing fallito, consideriamo minorenne per sicurezza

def is_Under_21(birthdate_str):
    """Restituisce True se la persona è minorenne. Accetta formato 'gg-mm-aaaa'."""
    try:
        birthdate = datetime.datetime.strptime(birthdate_str, "%d-%m-%Y").date()
        print("Birthday is:", birthdate)
        today = datetime.date.today()
        return (today - birthdate).days // 365 < 21
    except Exception:
        return True  # In caso di parsing fallito, consideriamo minorenne per sicurezza




def calculate_end_of_year(date_input):
    """
    Riceve una data come stringa ISO o datetime.
    Restituisce la fine dell'anno nel formato "gg-mm-aaaa" oppure None se errore.
    """
    try:
        if isinstance(date_input, datetime):
            dt = date_input
        elif isinstance(date_input, str):
            dt = datetime.fromisoformat(date_input.replace("Z", ""))
        else:
            raise ValueError("Unsupported date input type")

        return f"31-12-{dt.year}"
    except Exception:
        logging.exception("Failed to calculate end of year")
        return None

def calculate_end_of_year_membership(date_input):
    """
    Calcola la fine dell’anno dato un datetime o stringa ISO. Output: '31-12-YYYY'.
    """
    try:
        if isinstance(date_input, str):
            date_input = dt.fromisoformat(date_input.replace("Z", ""))
        elif not isinstance(date_input, dt):
            raise TypeError("Expected a datetime or ISO string.")

        return f"31-12-{date_input.year}"
    except Exception as e:
        import logging
        logging.exception("Failed to calculate end of year")
        return None
    except Exception as e:
        import logging
        logging.exception("Failed to calculate end of year")
        return None
def sanitize_event(event: dict) -> dict:
    """Rimuove i campi admin-only da un dizionario evento"""
    hidden_fields = ['participantsCount', 'maxParticipants', 'createdBy', 'updatedBy']
    return {k: v for k, v in event.items() if k not in hidden_fields}

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email.strip().lower()))