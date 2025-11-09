import mahlaka
import sys
import sqlite3

class pluga():
    
    def __init__(self, name: str, gdud: str = "", color: str = "#FFFFFF",
                 number_of_mahalkha: int = 0, mahalkot: list = None):
        self.name = name.strip()
        self.gdud = gdud.strip()
        self.color = color
        self.number_of_mahalkha = number_of_mahalkha
        self.mahalkot = mahalkot if mahalkot is not None else []

        for i in range(number_of_mahalkha):
            print("adding mahlaka number ", i+1)
            mahlaka_color = input("what color do your mahalkha is ? ")
            print("הדבק את הרשימה ולחץ Ctrl+D (Linux/Mac) או Ctrl+Z ואז Enter (Windows):")
            list_of_soldiers = sys.stdin.read().splitlines()[1:]
            self.add_mahalaka(list_of_soldiers=list_of_soldiers, number=i+1, color=mahlaka_color)

    def add_mahalaka(self, list_of_soldiers: str = "", number: int = 0, color: str = "#FFFFFF"):
        mahlaka_to_add = mahlaka.mahlaka(list_of_soldiers=list_of_soldiers,
                                          number=number, color=color)
        self.mahalkot.append(mahlaka_to_add)

    def check_available_soldiers(self, on_date=None):
        drivers = []
        staff = [] 
        soldiers = []

        for mahlaka_obj in self.mahalkot:
            soldiers.append(mahlaka_obj.check_available_soldiers(on_date=on_date))
            drivers += mahlaka_obj.check_available_drivers(on_date=on_date)
            staff.append(mahlaka_obj.check_available_staff(on_date=on_date))

        for i in range(len(soldiers)):
            print(f"מחלקה מספר {i+1}:")
            print("חיילים זמינים:")
            print(soldiers[i])
            
            print("צוות זמינים:")
            print(staff[i])

        print("נהגים זמינים:")
        print(drivers)