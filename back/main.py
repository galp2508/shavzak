
import pluga
from datetime import datetime, timedelta
import shavzak_manager

def main():
    my_pluga = pluga.pluga(name="פלוגה ב", gdud="פנתר", color="#BF092F", number_of_mahalkha=1)
    shavzak_manager_instance = shavzak_manager.shavzak_manager(pluga_instance=my_pluga)
    shavzak_manager_instance.get_assignment_template()
    shavzak_manager_instance.create_time_slots()
    shavzak_manager_instance.assign_soldiers_smart()
    shavzak_manager_instance.display_company_schedule()

if __name__ == "__main__":
    main()