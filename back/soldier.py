from datetime import datetime, timedelta

class soldier:
    """
    Soldier record with advanced availability management.
    """
    def __init__(self, name: str, idf_id: int = 0, kita: str = "", id: str = "",
                 role: str = "", sex: str = "", phone_number: str = "",
                 address: str = "", emergency_contact_name: str = "", 
                 emergency_contact_number: str = "", pakal: str = "",
                 birth_date: datetime = None, recruit_date: datetime = None,
                 home_round: datetime = None, certifications: list = None,
                 is_platoon_commander: bool = False, has_hatashab: bool = False):
        
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
        
        self.certifications = certifications if certifications else []
        self.is_platoon_commander = is_platoon_commander
        self.has_hatashab = has_hatashab
        
        self.exit_requests = []
        self.medical_referrals = []
        self.unavailable_dates = []
    
    def add_certification(self, cert_name: str):
        if cert_name not in self.certifications:
            self.certifications.append(cert_name)
    
    def has_certification(self, cert_name: str) -> bool:
        return cert_name in self.certifications
    
    def add_exit_request(self, date: datetime, reason: str = ""):
        self.exit_requests.append({
            'date': date,
            'reason': reason,
            'status': 'pending'
        })
    
    def approve_exit_request(self, date: datetime):
        for request in self.exit_requests:
            if request['date'].date() == date.date():
                request['status'] = 'approved'
                if date not in self.unavailable_dates:
                    self.unavailable_dates.append(date)
                return True
        return False
    
    def add_medical_referral(self, date: datetime, referral_type: str, duration_hours: int = 4):
        self.medical_referrals.append({
            'date': date,
            'type': referral_type,
            'duration_hours': duration_hours
        })
    
    def add_unavailable_date(self, date: datetime, reason: str = ""):
        self.unavailable_dates.append({
            'date': date,
            'reason': reason
        })
    
    def is_home_round_due(self, on_date: datetime = None) -> bool:
        if on_date is None:
            on_date = datetime.now()
        
        if self.home_round is None:
            return False
        
        days_difference = (on_date - self.home_round).days
        is_home_round = (days_difference % 21 == 0 or days_difference % 22 == 0 or 
                        days_difference % 23 == 0 or days_difference % 24 == 0)
        
        return is_home_round
    
    def is_hatashab_day(self, on_date: datetime = None) -> bool:
        if not self.has_hatashab:
            return False
        
        if on_date is None:
            on_date = datetime.now()
        
        weekday = on_date.weekday()
        return weekday in [3, 4, 5]
    
    def has_exit_request_on(self, on_date: datetime) -> bool:
        for request in self.exit_requests:
            if request['status'] == 'approved' and request['date'].date() == on_date.date():
                return True
        return False
    
    def has_medical_referral_on(self, on_date: datetime) -> bool:
        for referral in self.medical_referrals:
            if referral['date'].date() == on_date.date():
                return True
        return False
    
    def is_unavailable_on(self, on_date: datetime) -> bool:
        for unavailable in self.unavailable_dates:
            if isinstance(unavailable, dict):
                if unavailable['date'].date() == on_date.date():
                    return True
            elif isinstance(unavailable, datetime):
                if unavailable.date() == on_date.date():
                    return True
        return False
    
    def is_available(self, on_date: datetime = None, strict: bool = True) -> bool:
        if on_date is None:
            on_date = datetime.now()
        
        if self.is_home_round_due(on_date):
            return False
        
        if self.is_hatashab_day(on_date):
            return False
        
        if strict:
            if self.has_exit_request_on(on_date):
                return False
            
            if self.has_medical_referral_on(on_date):
                return False
            
            if self.is_unavailable_on(on_date):
                return False
        
        return True
    
    def get_unavailability_reason(self, on_date: datetime) -> str:
        if self.is_home_round_due(on_date):
            return "סבב בית"
        if self.is_hatashab_day(on_date):
            return "התש 2"
        if self.has_exit_request_on(on_date):
            for req in self.exit_requests:
                if req['status'] == 'approved' and req['date'].date() == on_date.date():
                    return f"בקשת יציאה: {req.get('reason', 'לא צוין')}"
        if self.has_medical_referral_on(on_date):
            for ref in self.medical_referrals:
                if ref['date'].date() == on_date.date():
                    return f"הפניה: {ref['type']}"
        if self.is_unavailable_on(on_date):
            for unavail in self.unavailable_dates:
                if isinstance(unavail, dict):
                    if unavail['date'].date() == on_date.date():
                        return f"לא זמין: {unavail.get('reason', 'לא צוין')}"
        return "זמין"
  
    def __repr__(self) -> str:
        return f"soldier(name={self.name!r}, role={self.role!r}, hatashab={self.has_hatashab})"