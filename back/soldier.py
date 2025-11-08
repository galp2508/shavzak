from datetime import datetime

class soldier:
    """
    Soldier record with convenience helpers.
    """
    def __init__(self, name: str, idf_id: int = 0, kita : str = "", id: str = "",
                 role: str = "", sex: str = "", phone_number: str = "",
                 address: str = "", emergency_contact_name: str = "", 
                 emergency_contact_number: str = "", pakal: str = "",
                 birth_date: datetime = None, recruit_date: datetime = None,
                 home_round: datetime = None):
        # normalize simple fields
        self.name = name.strip()
        self.idf_id = idf_id
        self.kita = kita.strip()
        self.id = id.strip()
        self.role = role.strip()
        self.sex = sex.strip()
        self.phone_number = phone_number.strip()
        self.address = address.strip()
        self.emergency_contact_name = emergency_contact_name.strip()
        self.emergency_contact_number = emergency_contact_number.strip()
        self.pakal = pakal.strip()
        self.birth_date = birth_date
        self.recruit_date = recruit_date
        self.home_round = home_round
  
    def is_home_round_due(self, on_date: datetime = None) -> bool:
        """
        Check if the soldier's home round is due on the given date.
        If no date is provided, use today's date.
        Returns True if the given date is a home round date (occurs every 21 days from initial home round).
        """
        if on_date is None:
            on_date = datetime.now()
            print("on date is none set to today", on_date, type(on_date))
        
        # Calculate days since initial home round
        days_difference = (on_date - self.home_round).days
        # Check if the days difference is divisible by 21 (complete cycles)
        is_home_round = days_difference % 21 == 0  or days_difference % 22 == 0 or days_difference % 23 == 0 or days_difference % 24 == 0
        
        return is_home_round

  
    def __repr__(self) -> str:
        return f"solider(name={self.name!r}, idf_id={self.idf_id!r}, role={self.role!r})"
