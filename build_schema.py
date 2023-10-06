import config
import pyTigerGraph as tg
from spellchecker import SpellChecker
import uuid, json, datetime
import pandas as pd

host = config.tg_host
graphname = config.tg_graph_name
username = config.tg_username
password = config.tg_password
secret = config.tg_secret

conn = tg.TigerGraphConnection(host=host, graphname=graphname, username=username, password=password)
conn.apiToken = conn.getToken(secret)

# Enter username and password

def build_schema():
    results = conn.gsql('''
        USE GLOBAL
        CREATE VERTEX Patient (PRIMARY_ID id STRING, first_name STRING, last_name STRING, username STRING, email STRING, password STRING, DOB STRING, gender BOOL) WITH primary_id_as_attribute="true"
        CREATE VERTEX Care_Provider (PRIMARY_ID id STRING, name STRING, email STRING, password STRING, specialty STRING) WITH primary_id_as_attribute="true"
        CREATE VERTEX Symptom (PRIMARY_ID id STRING, name STRING) WITH primary_id_as_attribute="true"
        CREATE VERTEX Disease (PRIMARY_ID id STRING, name STRING) WITH primary_id_as_attribute="true"
        CREATE VERTEX Risk_Factors (PRIMARY_ID id STRING, name STRING) WITH primary_id_as_attribute="true"
        CREATE VERTEX Event (PRIMARY_ID id STRING, date_time DATETIME, sensor LIST, actuator LIST, action STRING) WITH primary_id_as_attribute="true"
        CREATE DIRECTED EDGE is_experiencing (From Patient, To Symptom) WITH REVERSE_EDGE="reverse_is_experiencing"
        CREATE DIRECTED EDGE indicates (From Symptom, To Disease) WITH REVERSE_EDGE="reverse_indicates"
        CREATE DIRECTED EDGE diagnosed_by (From Disease, To Care_Provider) WITH REVERSE_EDGE="reverse_diagnosed_by"
        CREATE DIRECTED EDGE diagnosed_with (From Patient, To Disease) WITH REVERSE_EDGE="reverse_diagnosed_with"
        CREATE DIRECTED EDGE treating (From Care_Provider, To Patient) WITH REVERSE_EDGE="reverse_treating"
        CREATE DIRECTED EDGE exhibits (From Patient, To Risk_Factors) WITH REVERSE_EDGE="reverse_exhibits"
        CREATE DIRECTED EDGE reinforces (From Risk_Factors, To Disease) WITH REVERSE_EDGE="reverse_reinforces"
        CREATE DIRECTED EDGE event_patient (From Event, To Patient) WITH REVERSE_EDGE="reverse_event_patient"
        CREATE DIRECTED EDGE event_risk (From Event, To Risk_Factors) WITH REVERSE_EDGE="reverse_event_risk"
        CREATE DIRECTED EDGE event_symptom (From Event, To Symptom) WITH REVERSE_EDGE="reverse_event_symptom"
        CREATE DIRECTED EDGE event_disease (From Event, To Disease) WITH REVERSE_EDGE="reverse_event_disease"
        CREATE DIRECTED EDGE event_care_provider (From Event, To Care_Provider) WITH REVERSE_EDGE="reverse_event_care_provider"
    ''')
    return(results)

def test():
    print("test")

build_schema()
# test()
