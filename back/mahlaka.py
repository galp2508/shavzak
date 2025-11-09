import soldier
from datetime import datetime 
import gdatetime

class mahlaka:
    def __init__(self, list_of_soldiers=None, number: int = 0, color: str = "#FFFFFF"):
        self.number = number
        self.color = color
        self.staff = []
        self.drivers = [] 
        self.soldiers = []
        if list_of_soldiers is not None and list_of_soldiers != "":
            self.import_soldiers(list_of_soldiers)

    def add_staff(self, soldier):
        self.staff.append(soldier)

    def remove_staff(self, soldier):
        self.staff.remove(soldier)

    def add_driver(self, soldier):
        self.drivers.append(soldier)

    def remove_driver(self, soldier):
        self.drivers.remove(soldier)

    def add_soldier(self, soldier):
        self.soldiers.append(soldier)

    def remove_soldier(self, soldier):
        self.soldiers.remove(soldier)
    
    def import_soldiers(self, soldiers_list=[]):
        role = ""
        name = ""
        home_round = ""
        kita = ""
        for line in soldiers_list:
            if 'מ"מ' in line or 'מ"כ' in line or 'סמל' in line:
                role, name, home_round_date = line.split('-')
                self.add_staff(soldier.soldier(name=name, 
                                                 role=role,
                                                 home_round=gdatetime.str_to_gdate(home_round_date.strip())))
            elif "כיתה" in line:
                kita, home_round = line.split('-')
                home_round = gdatetime.str_to_gdate(home_round.strip())
                kita = kita.replace("כיתה", "").strip()
            else:
                if '-' in line:
                    name, role = line.split('-')
                    self.add_driver(soldier.soldier(name=name,
                                                    role="נהג",
                                                    kita=kita.strip(), 
                                                    home_round=home_round))
                else:
                    self.add_soldier(soldier.soldier(name=line,
                                                    role="לוחם",
                                                    kita=kita.strip(), 
                                                    home_round=home_round))
                    
    def check_available_soldiers(self, on_date: datetime = None, strict: bool = True):
        available_soldiers = []
        for s in self.soldiers:
            if s.is_available(on_date, strict=strict):
                available_soldiers.append(s)
        return available_soldiers
    
    def check_available_drivers(self, on_date: datetime = None, strict: bool = True):
        available_drivers = []
        for driver in self.drivers:
            if driver.is_available(on_date, strict=strict):
                available_drivers.append(driver)
        return available_drivers
    
    def check_available_staff(self, on_date: datetime = None, strict: bool = True):
        available_staff = []
        for staff in self.staff:
            if staff.is_available(on_date, strict=strict):
                available_staff.append(staff)
        return available_staff
    
    def get_unavailable_soldiers_with_reasons(self, on_date: datetime = None):
        unavailable = []
        for s in self.soldiers:
            if not s.is_available(on_date):
                unavailable.append({
                    'soldier': s,
                    'reason': s.get_unavailability_reason(on_date)
                })
        return unavailable

    def list_soldiers(self):
        return [s.name for s in self.soldiers]
    
    def print_soldiers(self, soldiers_list=None):
        if soldiers_list is None:
            soldiers_list = self.soldiers
        for s in soldiers_list:
            print(f"{s.name} - {s.role} - {s.kita}")