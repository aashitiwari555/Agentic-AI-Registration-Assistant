import re
from datetime import datetime


# EMAIL VALIDATION
def validate_email(email):

    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    if re.match(pattern, email):
        return True

    return False


# PHONE VALIDATION
def validate_phone(phone):

    if phone.isdigit() and len(phone) == 10:
        return True

    return False


# DOB VALIDATION
def validate_dob(dob):

    try:
        datetime.strptime(dob, "%Y-%m-%d")
        return True

    except:
        return False