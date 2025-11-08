from datetime import datetime

def str_to_gdate(date_str: str) -> datetime:
    """
    Convert a string in the format 'DD.MM.YYYY' to a datetime object.
    """
    return datetime.strptime(date_str, "%d.%m.%Y")

