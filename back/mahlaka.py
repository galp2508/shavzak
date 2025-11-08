import soldier
from datetime import datetime 
import gdatetime

class mahlaka:
    def __init__(self, list_of_soldiers : list = "", number: int = 0, color: str = "#FFFFFF"):
        self.number = number
        self.color = color
        self.staff = []
        self.drivers = [] 
        self.soldiers = []
        if list_of_soldiers is not "":
            self.import_soldiers(list_of_soldiers)

    def add_staff(self, soldier):
        self.staff.append(soldier)

    def remove_staff(self, soldier):
        self.soldiers.remove(soldier)

    def add_driver(self, soldier):
        self.drivers.append(soldier)

    def remove_driver(self, soldier):
        self.drivers.append(soldier)

    def add_soldier(self, soldier):
        self.soldiers.append(soldier)

    def remove_soldier(self, soldier):
        self.soldiers.remove(soldier)
    
    def import_soldiers(self, soliders_list=[]):
        role = ""
        name = ""
        home_round = ""
        kita = ""
        for line in soliders_list:
            if 'מ"מ' in line or 'מ"כ' in line or 'סמל' in line:
                role, name, home_round_date = line.split('-')
                self.add_staff(soldier.soldier(name=name, 
                                                 role=role,
                                                 home_round=gdatetime.str_to_gdate(home_round_date.strip())))
            elif "כיתה" in line:
                kita, home_round = line.split('-')
                home_round  = gdatetime.str_to_gdate(home_round.strip())
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
                    
    
    def check_available_soldiers(self, on_date: datetime = None):
        available_soldiers = []

        for soldier in self.soldiers:
            if not soldier.is_home_round_due(on_date):
                available_soldiers.append(soldier)
        
        return available_soldiers
    
    def check_available_drivers(self, on_date: datetime = None):
        available_drivers = []

        for driver in self.drivers:
            if not driver.is_home_round_due(on_date):
                available_drivers.append(driver)
        
        return available_drivers
    
    def check_available_staff(self, on_date: datetime = None):
        available_staff = []

        for staff in self.staff:
            if not staff.is_home_round_due(on_date):
                available_staff.append(staff)
        
        return available_staff

    def list_soldiers(self):
        return [soldier.name for soldier in self.soldiers]
    
    def print_soldiers(self, soliders_list=None):
        if soliders_list is None:
            soliders_list = self.soldiers

        for soldier in soliders_list:
            print(f"{soldier.name} - {soldier.role} - {soldier.kita}")