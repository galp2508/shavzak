#!/usr/bin/env python3
"""בדיקת חמליסטים במערכת"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from models import init_db, get_session, Soldier, Certification

DB_PATH = os.path.join(os.path.dirname(__file__), 'shavzak.db')
engine = init_db(DB_PATH)
session = get_session(engine)

# מצא חמליסטים
soldiers_with_cert = session.query(Soldier).join(Certification).filter(
    Certification.certification_name == 'חמליסט'
).all()

print(f'🏥 חמליסטים במערכת: {len(soldiers_with_cert)}')
for s in soldiers_with_cert:
    certs = session.query(Certification).filter_by(soldier_id=s.id).all()
    print(f'  • {s.name} (ID: {s.id}, תפקיד: {s.role}) - הסמכות: {[c.certification_name for c in certs]}')

# בדוק גם איך מקודדת ההסמכה
print(f'\n📋 כל ההסמכות במערכת:')
all_certs = session.query(Certification).all()
for cert in all_certs:
    soldier = session.query(Soldier).get(cert.soldier_id)
    print(f'  • {soldier.name}: {cert.certification_name}')

session.close()
