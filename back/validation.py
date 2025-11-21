"""
Input Validation and Password Policy
אימות קלט ומדיניות סיסמאות
"""
import re
from marshmallow import Schema, fields, validate, ValidationError, validates, validates_schema

class PasswordPolicy:
    """מדיניות סיסמאות חזקה"""

    MIN_LENGTH = 8
    MAX_LENGTH = 128

    @staticmethod
    def validate(password):
        """
        בודק שסיסמה עומדת במדיניות האבטחה

        דרישות:
        - לפחות 8 תווים
        - לפחות אות גדולה אחת
        - לפחות אות קטנה אחת
        - לפחות ספרה אחת
        """
        errors = []

        if len(password) < PasswordPolicy.MIN_LENGTH:
            errors.append(f'הסיסמה חייבת להיות לפחות {PasswordPolicy.MIN_LENGTH} תווים')

        if len(password) > PasswordPolicy.MAX_LENGTH:
            errors.append(f'הסיסמה חייבת להיות עד {PasswordPolicy.MAX_LENGTH} תווים')

        if not re.search(r'[A-Z]', password):
            errors.append('הסיסמה חייבת להכיל לפחות אות גדולה אחת באנגלית')

        if not re.search(r'[a-z]', password):
            errors.append('הסיסמה חייבת להכיל לפחות אות קטנה אחת באנגלית')

        if not re.search(r'[0-9]', password):
            errors.append('הסיסמה חייבת להכיל לפחות ספרה אחת')

        # רשימת סיסמאות נפוצות (רק דוגמאות - בפרודקשן צריך רשימה מלאה יותר)
        common_passwords = ['Password1', 'Aa123456', 'Qwerty123', 'Admin123']
        if password in common_passwords:
            errors.append('הסיסמה נפוצה מדי. אנא בחר סיסמה אחרת')

        if errors:
            raise ValidationError(errors)

        return True


class UserRegistrationSchema(Schema):
    """סכמת אימות לרישום משתמש"""

    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=50, error='שם המשתמש חייב להיות בין 3-50 תווים'),
            validate.Regexp(
                r'^[a-zA-Z0-9_\u0590-\u05FF]+$',
                error='שם משתמש יכול להכיל רק אותיות, מספרים וקו תחתון'
            )
        ]
    )

    password = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=128)
    )

    full_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100, error='שם מלא חייב להיות בין 2-100 תווים')
    )

    pluga_id = fields.Int(required=False, allow_none=True)
    pluga_name = fields.Str(required=False, allow_none=True)
    gdud = fields.Str(required=False, allow_none=True)
    role = fields.Str(required=False, allow_none=True)

    @validates('password')
    def validate_password(self, value):
        """בדיקת מדיניות סיסמאות"""
        PasswordPolicy.validate(value)


class UserLoginSchema(Schema):
    """סכמת אימות להתחברות"""

    username = fields.Str(required=True)
    password = fields.Str(required=True)


class SoldierSchema(Schema):
    """סכמת אימות לחייל"""

    name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100, error='שם חייל חייב להיות בין 2-100 תווים')
    )

    idf_id = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Regexp(
            r'^\d{7}$',
            error='מספר אישי חייב להכיל בדיוק 7 ספרות'
        )
    )

    role = fields.Str(
        required=True,
        validate=validate.OneOf(
            ['מכ', 'ממ', 'סמל', 'רב סמל', 'קצין', 'חייל'],
            error='תפקיד לא תקין'
        )
    )

    mahlaka_id = fields.Int(required=True)
    phone = fields.Str(required=False, allow_none=True)
    is_krav = fields.Bool(required=False)
    is_ram = fields.Bool(required=False)
    hatash_2_days = fields.Bool(required=False)


class AssignmentTemplateSchema(Schema):
    """סכמת אימות לתבנית משימה"""

    name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100, error='שם משימה חייב להיות בין 2-100 תווים')
    )

    assignment_type = fields.Str(
        required=True,
        validate=validate.OneOf(
            ['שמירה', 'סיור', 'כוננות', 'תפקיד', 'אחר'],
            error='סוג משימה לא תקין'
        )
    )

    commanders_needed = fields.Int(
        required=True,
        validate=validate.Range(min=0, max=100, error='מספר מפקדים חייב להיות בין 0-100')
    )

    soldiers_needed = fields.Int(
        required=True,
        validate=validate.Range(min=0, max=100, error='מספר חיילים חייב להיות בין 0-100')
    )

    length_in_hours = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=24, error='אורך משימה חייב להיות בין 1-24 שעות')
    )

    start_hour = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0, max=23, error='שעת התחלה חייבת להיות בין 0-23')
    )

    times_per_day = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=10, error='מספר פעמים ביום חייב להיות בין 1-10')
    )

    pluga_id = fields.Int(required=True)
    mahalkot_ids = fields.List(fields.Int(), required=False)


def validate_data(schema_class, data):
    """
    פונקציית עזר לאימות נתונים

    Args:
        schema_class: מחלקת הסכמה (Schema)
        data: נתונים לאימות

    Returns:
        tuple: (validated_data, errors)

    Usage:
        validated_data, errors = validate_data(UserRegistrationSchema, request.json)
        if errors:
            return jsonify({'errors': errors}), 400
    """
    schema = schema_class()
    try:
        validated_data = schema.load(data)
        return validated_data, None
    except ValidationError as err:
        return None, err.messages
