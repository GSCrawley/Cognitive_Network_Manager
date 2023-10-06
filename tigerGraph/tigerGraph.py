import config
import pyTigerGraph as tg
from spellchecker import SpellChecker
import uuid, json, datetime
import pandas as pd
from tigerGraph.eventGraph import event_snapshot

host = config.tg_host
graphname = config.tg_graph_name
username = config.tg_username
password = config.tg_password
secret = config.tg_secret

conn = tg.TigerGraphConnection(host=host, graphname=graphname, username=username, password=password)
conn.apiToken = conn.getToken(secret)

def create_new_patient_vertex(first_name, last_name, username, password, email, DOB):
    unique_id = uuid.uuid4()
    patient_id = f"P{str(unique_id)[:8]}"
    date_of_birth = int(DOB)
    attributes = {
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "password": password,
        "email": email,
        "DOB": DOB,
    }
    print(attributes)
    conn.upsertVertex("Patient", patient_id, attributes)
    return(patient_id)

def create_new_provider_vertex(name, email, password, specialty):
    unique_id = uuid.uuid4()
    care_provider_id = f"CP{str(unique_id)[:8]}"
    # date_of_birth = int(DOB)
    attributes = {
        "name": name,
        "email": email,
        "password": password,
        "specialty": specialty,
    }
    print(attributes)
    conn.upsertVertex("Care_Provider", care_provider_id, attributes)
    return(care_provider_id)

def creat_new_location_vertex(user_id, location):
    unique_id = uuid.uuid4()
    location_id = f"L{str(unique_id)[:8]}"
    attrebutes = {
        "location": location
    }
    conn.upsertVertex("Location", location_id, attrebutes)
    conn.upsertEdge("Patient", f"{user_id}", "patient_location", "Location", f"{location_id}")
    return("test")

def user_login(email, password):
    result = conn.runInstalledQuery("authenticateUser", {"email": email, "password": password})
    # print('RESULT: ', result[0]['User'])
    return result[0]

def care_provider_login(email, password):
    result = conn.runInstalledQuery("authenticateProvider", {"email": email, "password": password})
    return result[0]

def get_user_profile(id_value):
    result = conn.runInstalledQuery("getProfile", {"id_value": id_value})
    # print("RESULT: ", result)
    return result

def get_provider_profile(id_value):
    result = conn.runInstalledQuery("getProviderProfile", {"id_value": id_value})
    print(result)
    return result

def provider_add_patient(patient_id, provider_id):
    properties = {"weight": 5}
    result = conn.upsertEdge("Care_Provider", f"{provider_id}", "treating", "Patient", f"{patient_id}", f"{properties}")
    return result

def get_patient_info(id_value):
    result = conn.runInstalledQuery("getPatientInfo", {"id_value": id_value})
    info = result[0]['User'][0]['attributes']['User.DOB']
    return info

def get_symptom_info(id_value_data):
    id_value_list = json.loads(id_value_data)
    result_list = []
    for id_value in id_value_list:
        print("ID_VALUE:", id_value)
        result = conn.runInstalledQuery("getSymptomInfo", {"id_value": id_value})
        name = result[0]['Symp'][0]['attributes']['Symp.name']
        result_list.append(name)
    return result_list

# def get_diseases_id(diseases_name_list):
#     output_list = []
#     for disease_name in diseases_name_list:
#         data = conn.runInstalledQuery("getDiseaseID", {"diseaseName": disease_name})
#         # disease_id = data['result'][0]['v_id']
#         # disease_id = data[0]['result'][0]['v_id']
#         # output_list.append(data)
#         print("OUTPUT:", data)
#     return(output_list)

def check_existing_symptom(patient_id, symptom_list_data):
    vertex_type = "Symptom"
    attribute = "name"
    result_list = []
    id_list = []
    spell = SpellChecker()
    # SPELL CHECKER
    for symptom in symptom_list_data:
        symptom_check = symptom.split(" ")
        checked_words = []
        for word in symptom_check:
            # print("WORD: ", word)
            checked_word = spell.correction(word)
            checked_words.append(checked_word)
        result = " ".join(checked_words)
        result_list.append(result.lower())
    # result_list = symptom_list_data
    print('RESULT: ', result_list)
    try:
        df = conn.getVertexDataFrame(vertex_type)
        for name in result_list:
            if name[-1] == ".":
                name = name[:-1]
            if name in df['name'].values:
                # print(df['name'].values)
                print("EXSISTING SYMPTOM: ", name)
                result = df.loc[df[attribute] == name]
                v_id = result['v_id'].values
                v_id = str(v_id)[2:-2]
                # print(df.loc[df[attribute]==name])
                # edge.s.append(v_id)
                id_list.append(v_id)
                properties = {"weight": 5}
                print("test", v_id)
                conn.upsertEdge("Patient", f"{patient_id}", "is_experiencing", "Symptom", f"{v_id}", f"{properties}")
            else:
                v_id = create_symptom_vertex(patient_id, name)
                print("v_id: ", v_id)
                id_list.append(v_id)
    except Exception as e:
        print("test")
        for name in result_list:
            v_id = create_symptom_vertex(patient_id, name)
            id_list.append(v_id)
    return(id_list)

def check_existing_disease(disease_list_data, symptom_id_list):
    vertex_type = "Disease"
    attribute = "name"
    symptoms_id_list = json.loads(symptom_id_list)
    stripped_string = symptom_id_list[1:-1]
    symptom_id_list = stripped_string.split(', ')
    disease_id_list = []
    print("TEST: ", disease_list_data, type(symptom_id_list))
    try:
        df = conn.getVertexDataFrame(vertex_type)
        # print("DF: ", df)
        for name in disease_list_data:
            name=name.lower()
            if name[-1] == ".":
                name = name[:-1]
            if name in df['name'].values:
                print("NAME: ", name)
                result = df.loc[df[attribute] == name]
                v_id = result['v_id'].values
                v_id = str(v_id)[2:-2]
                disease_id_list.append(v_id)
                # Make DB query call for weight
                properties = {"weight": 5}
                for symptom_id in symptom_id_list:
                    # symptom_name = name.lower()
                    # print("SYmptom Name: ", symptom_name)
                    # data = conn.runInstalledQuery("getSymptomID", {"symptomName": symptom_name})
                    # print("DATA: ", data)
                    # symptom_id = data[0]['result'][0]['v_id']
                    print("Symptom ID: ", symptom_id)
                    print("Disease ID: ", v_id)
                    conn.upsertEdge("Symptom", f"{symptom_id[1:-1]}", "indicates", "Disease", f"{v_id}", f"{properties}")
                print("Exsisting Disease: ", name)
            else:
                new_disease_id = create_disease_vertex(name, symptom_id_list)
                disease_id_list.append(new_disease_id)
    except Exception as e:
        for name in disease_list_data:
            print("NEW: ", name)
            new_disease_id = create_disease_vertex(name, symptom_id_list)
            disease_id_list.append(new_disease_id)
    return(disease_id_list)
    

def create_symptom_vertex(patient_id, new_symptom):
    unique_id = uuid.uuid4()
    symptom_id = f"S{str(unique_id)[:8]}"
    # edge.s.append(symptom_id)
    properties = {"weight": 5}
    # Lowercase standerdize names
    print("NEW SYMPTOM:", new_symptom)
    attributes = {
        "name": new_symptom.lower()
    }
    conn.upsertVertex("Symptom", f"{symptom_id}", attributes)
    conn.upsertEdge("Patient", f"{patient_id}", "is_experiencing", "Symptom", f"{symptom_id}", f"{properties}")
    # print("HELLO!!!", new_symptom, symptom_id)
    return(symptom_id)

def create_disease_vertex(new_disease, symptom_id_list):
    unique_id = uuid.uuid4()
    disease_id = f"D{str(unique_id)[:8]}"
    # edge.d.append(disease_id)
    # Check new disease string for period.
    if new_disease[-1] == ".":
        new_disease = new_disease[:-1]
    # Lowercase standerdize names
    attributes = {
        "name": new_disease.lower()
    }
    conn.upsertVertex("Disease", f"{disease_id}", attributes)
    # add event
    # print("SYMPTOM: ", symptom_id_list)

    for symptom_id in symptom_id_list:
        properties = {"weight": 5}
        # data = conn.runInstalledQuery("getSymptomID", {"symptomName": symptom_name})
        print("DATA: ", symptom_id[1:-1])
        # symptom_id = data[0]['result'][0]['v_id']
        conn.upsertEdge("Symptom", f"{symptom_id[1:-1]}", "indicates", "Disease", f"{disease_id}", f"{properties}")
        # add event
    return(disease_id)

def confirm_diagnosis(disease_name, patient_id, care_provider_id):
    properties = {"weight": 5}
    disease_name = disease_name.lower()
    print("DISEASE NAME: ", disease_name)
    data = conn.runInstalledQuery("getDiseaseID", {"diseaseName": disease_name})
    disease_id = data[0]['result'][0]['v_id']
    properties = {"weight": 5}
    print(disease_id)
    conn.upsertEdge("Patient", f"{patient_id}", "diagnosed_with", "Disease", f"{disease_id}", f"{properties}")
    conn.upsertEdge("Disease", f"{disease_id}", "diagnosed_by", "Care_Provider", f"{care_provider_id}", f"{properties}")
    # add event


    print("SUCESS?")
    return(disease_id)

def check_existing_risk_factors(risk_factors_list, disease_name, patient_id):
    vertex_type = "Risk_Factors"
    attribute = "name"
    risk_factors_name_list = []
    risk_factors_name_patient_list = []
    disease_name = disease_name.lower()
    data = conn.runInstalledQuery("getDiseaseID", {"diseaseName": disease_name})
    disease_id = data[0]['result'][0]['v_id']
    risk_factors_id_list = []
    try:
        df = conn.getVertexDataFrame(vertex_type)
        for name in risk_factors_list:
            name=name.lower()
            if name not in df['name'].values:
                v_id = create_risk_factor_vertex(name, disease_name)
                risk_factors_id_list.append(v_id)
            elif name in df['name'].values:
                result = df.loc[df[attribute] == name]
                v_id = result['v_id'].values
                v_id = str(v_id)[2:-2]
                risk_factors_id_list.append(v_id)
    except:
        for name in risk_factors_list:
            v_id = create_risk_factor_vertex(name, disease_name)
            risk_factors_id_list.append(v_id)
    # get all risk factors from disease
    data = conn.runInstalledQuery("getAssociatedRiskFactorsDisease", {"name": disease_name.lower()})
    data = data[0]['result']
    for i in range(len(data)):
        risk_factors_name_list.append(data[i]['attributes']['name'])
    print("RF List: ", risk_factors_name_list)
    # get all risk factors from patient
    data = conn.runInstalledQuery("getAssociatedRiskFactorsPatient", {"patient_id": patient_id})
    data = data[0]['result']
    for i in range(len(data)):
        risk_factors_name_patient_list.append(data[i]['attributes']['name'])
    # get matching risk factors
    matching_risk_factors = []
    for item in risk_factors_name_patient_list:
        if item in risk_factors_name_list:
            matching_risk_factors.append(item)
            risk_factors_name_list.remove(item)

    return(risk_factors_name_list, matching_risk_factors, disease_id, risk_factors_id_list)

def check_existing_risk_factors_for_patient(risk_factors_list, patient_id):
    vertex_type = "Risk_Factors"
    attribute = "name"
    risk_factor_id_list = []
    try:
        df = conn.getVertexDataFrame(vertex_type)
        for name in risk_factors_list:
            name=name.lower()
            # if name[0] == "-":
            #     name = name[1:]
            if name in df['name'].values:
                print(name)
                result = df.loc[df[attribute] == name]
                v_id = result['v_id'].values
                risk_factor_id = str(v_id)[2:-2]
                risk_factor_id_list.append(risk_factor_id)
                properties = {"weight": 5}
                conn.upsertEdge("Patient", f"{patient_id}", "exhibits", "Risk_Factors", f"{risk_factor_id}", f"{properties}")
            else:
                risk_id = create_risk_factor_input_vertex(name, patient_id)
                risk_factor_id_list.append(risk_id)
                
    except:
        for name in risk_factors_list:
            new_id = create_risk_factor_input_vertex(name, patient_id)
            risk_factor_id_list.append(new_id)
    return(risk_factor_id_list)

def create_risk_factor_vertex(risk_factor, disease_name):
    unique_id = uuid.uuid4()
    risk_factor_id = f"RF{str(unique_id)[:8]}"
    disease_name = disease_name.lower()
    data = conn.runInstalledQuery("getDiseaseID", {"diseaseName": disease_name})
    disease_id = data[0]['result'][0]['v_id']
    attributes = {
        "name": risk_factor.lower()
    }
    properties = {"weight": 5}
    conn.upsertVertex("Risk_Factors", f"{risk_factor_id}", attributes)
    # conn.upsertEdge("Patient", f"{patient_id}", "exhibits", "Risk_Factors", f"{risk_factor_id}", f"{properties}")
    conn.upsertEdge("Risk_Factors", f"{risk_factor_id}", "reinforces", "Disease", f"{disease_id}", f"{properties}")
    print("This is a test")
    return(risk_factor_id)

def create_risk_factor_input_vertex(risk_factor, patient_id):
    unique_id = uuid.uuid4()
    risk_factor_id = f"RF{str(unique_id)[:8]}"
    attributes = {
        "name": risk_factor.lower()
    }
    properties = {"weight": 5}
    conn.upsertVertex("Risk_Factors", f"{risk_factor_id}", attributes)
    conn.upsertEdge("Patient", f"{patient_id}", "exhibits", "Risk_Factors", f"{risk_factor_id}", f"{properties}")
    print("This is a test")
    return(risk_factor_id)

def create_event(vertex1_id_list, vertex2_id_list, send_vertex, receive_vertex, send_edge_name, receive_edge_name, action):
    unique_id = uuid.uuid4()
    event_id = f"E{str(unique_id)[:8]}"
    timestamp = datetime.datetime.now()
    attributes = {
        "date_time": timestamp.isoformat(),
        "sensor": vertex1_id_list,
        "actuator": vertex2_id_list,
        "action": action
    }
    conn.upsertVertex("Event", f"{event_id}", attributes)

    # Use send/receive vertex to upsert event data
    # Get event data from vertex

    for id in vertex1_id_list:
        if id == "genesis":
            break
        properties = {"weight": 5}
        conn.upsertEdge(f"Event", f"{event_id}", f"{send_edge_name}", f"{send_vertex}", f"{id}", f"{properties}")
        add_event_to_vertex(id, timestamp, event_id, send_vertex)

    
    for id in vertex2_id_list:
        properties = {"weight": 5}
        conn.upsertEdge(f"Event", f"{event_id}", f"{receive_edge_name}", f"{receive_vertex}", f"{id}", f"{properties}")
        add_event_to_vertex(id, timestamp, event_id, receive_vertex)
    
    event_snapshot(event_id, timestamp, action, vertex1_id_list, vertex2_id_list, send_vertex, receive_vertex, send_edge_name, receive_edge_name)

    return("hi")

def add_event_to_vertex(id, timestamp, event_id, vertex):
    data = conn.getVerticesById(vertex, id)

    data = data[0]['attributes']['event']
    # print("QUERY: ", data)
    keylist = []
    valuelist = []
    for key, value in data.items():
        keylist.append(key)
        valuelist.append(value)
    
    keylist.append(timestamp.isoformat())
    valuelist.append(event_id)
    # print("KEYS", keylist)
    # print("VALUES", valuelist)

    # get event history from vertex
    event_attributes = {
        "event": {
            "keylist": keylist,
            "valuelist": valuelist,
        }
    }

    conn.upsertVertex(f"{vertex}", f"{id}", event_attributes)

# ADD REFERALS
# TESTs
# Labs
# Diagnosis
# Treatment