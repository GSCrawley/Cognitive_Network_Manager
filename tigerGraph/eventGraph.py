import config
import pyTigerGraph as tg
from spellchecker import SpellChecker
import uuid, json, datetime, threading
import pandas as pd

host = config.tg_host
graphname = config.tg_graph_name
username = config.tg_username
password = config.tg_password
secret = config.tg_secret

conn1 = tg.TigerGraphConnection(host=host, graphname=graphname, username=username, password=password)
conn1.apiToken = conn1.getToken(secret)

host = config.tg_host
graphname = config.tg_graph_event
username = config.tg_event_username
password = config.tg_password
secret = config.tg_event_secret

conn2 = tg.TigerGraphConnection(host=host, graphname=graphname, username=username, password=password)
conn2.apiToken = conn2.getToken(secret)

# Get sesson_id by hashing the token.
# Then for each session share that id between relivent vertecies.

def event_snapshot(event_id, timestamp, action, vertex1_id_list, vertex2_id_list, send_vertex, receive_vertex, send_edge_name, receive_edge_name):
    data = conn2.runInstalledQuery("FindMostRecentEvent", {})
    if data[0] == {'t': []}:
        t = 0
    else:
        t = data[0]['t'][0]['attributes']['t.T']
        t += 1
    attributes = {
        "date_time": timestamp.isoformat(),
        "sensor": vertex1_id_list,
        "actuator": vertex2_id_list,
        "action": action,
        "T": t
    }
    conn2.upsertVertex("Event", f"{event_id}", attributes)

    for id in vertex1_id_list:
        if id == "genesis":
            break
        new_vertex_id = update_attributes(event_id, send_vertex, id, send_edge_name)
        # get list of vertex events, return most recent event.
        history = conn1.runInstalledQuery("getEventHistory", {"vertexType": send_vertex, "vertexId": id})
        history = history[0]['result'][0]['attributes']['result.event']
        connect_history(history, new_vertex_id, send_vertex, event_id)

    for id in vertex2_id_list:
        new_vertex_id = update_attributes(event_id, receive_vertex, id, receive_edge_name)
        if vertex1_id_list[0] == "genesis":
            break
        history = conn1.runInstalledQuery("getEventHistory", {"vertexType": receive_vertex, "vertexId": id})
        history = history[0]['result'][0]['attributes']['result.event']
        connect_history(history, new_vertex_id, receive_vertex, event_id)

    # # GET event edges
    parent_event_thread = threading.Thread(target=connect_parent, args=(event_id,))
    parent_event_thread.start()
    return()

def update_attributes(event_id, vertex, id, edge):
    unique_id = uuid.uuid4()
    if id[0:2] == "CP":
        vertex_id = f"CP{str(unique_id)[:8]}"
    elif id[0:2] == "RF":
        vertex_id = f"RF{str(unique_id)[:8]}"
    elif id[0:1] == "P":
        vertex_id = f"P{str(unique_id)[:8]}"
    elif id[0:1] == "S":
        vertex_id = f"S{str(unique_id)[:8]}"
    elif id[0:1] == "D":
        vertex_id = f"D{str(unique_id)[:8]}"

    data = conn1.getVerticesById(vertex, id)
    attributes = data[0]['attributes']
    attributes["identity"] = str(id)
    
    events = attributes['event']
    times = attributes['time']
    eventlist = []
    timelist = []
    for event in events:
        eventlist.append(event)
    for time in times:
        timelist.append(time)

    attributes['event'] = eventlist
    attributes['time'] = timelist
    conn2.upsertVertex(f"{vertex}", f"{vertex_id}", attributes)

    properties = {"weight": 5}
    conn2.upsertEdge(f"Event", f"{event_id}", f"{edge}", f"{vertex}", f"{vertex_id}", f"{properties}")
    return(vertex_id)

def connect_history(history, new_vertex_id, vertex, event_id):
    # items = [(int(time), value) for time, value in history.items()]
    # Sort the list of tuples by timestamp
    # sorted_items = sorted(items, key=lambda x: x[0])
    sorted_items = history
    if len(sorted_items) > 1:
        # latest_event = sorted_items[-2][1]
        latest_event = sorted_items[0]
        data = conn2.getEdges("Event", latest_event)
        connect_self(data, vertex, new_vertex_id)

    return()
    
def connect_self(data, vertex, new_vertex_id):
    for item in data:
        if vertex == "Care_Provider":
            edge = "care_provider_self"
        elif vertex == "Patient":
            edge = "patient_self"
        elif vertex == "Symptom":
            edge = "symptom_self"
        elif vertex == "Disease":
            edge = "disease_self"
        elif vertex == "Risk_Factors":
            edge = "risk_factors_self"

        if vertex == item["to_type"]:
            prev = conn2.getVerticesById(vertex, item["to_id"])
            prev = prev[0]['attributes']['identity'] 

            curr = conn2.getVerticesById(vertex, new_vertex_id)
            curr = curr[0]['attributes']['identity']
            if prev == curr:
                properties = {"weight": 5}
                conn2.upsertEdge(f"{vertex}", f"{item['to_id']}", f"{edge}", f"{vertex}", f"{new_vertex_id}", f"{properties}")

def connect_parent(event_id):
    # GET event edges
    event_edges = conn2.getEdges("Event", event_id)
    event_data = conn2.getVerticesById("Event", event_id)
    if event_data[0]['attributes']['action'] == "Appointment":
        e_edges = conn2.getEdges("Care_Provider", event_edges[1]['to_id'])
        parent_id = e_edges[1]['to_id']
        child_id = event_edges[0]['to_id']
        properties = {"weight": 5}
        conn2.upsertEdge(f"Care_Provider", f"{parent_id}", f"treating", f"Patient", f"{child_id}", f"{properties}")

    elif event_data[0]['attributes']['action'] == "Symptom Input":
        parent_id = ""
        child_ids = []
        for vertex in event_edges:
            if vertex['to_type'] == "Patient":
                e_edges = conn2.getEdges("Patient", vertex['to_id'])
                parent_id = e_edges[1]['to_id']
            elif vertex['to_type'] == "Symptom":
                child_ids.append(vertex['to_id'])
        for child in child_ids:
            properties = {"weight": 5}
            conn2.upsertEdge("Patient", f"{parent_id}", "is_experiencing", "Symptom", f"{child}", f"{properties}")
    
    elif event_data[0]['attributes']['action'] == "Disease Hypothesis":
        parent_ids = []
        child_ids = []
        for vertex in event_edges:
            if vertex['to_type'] == "Symptom":
                e_edges = conn2.getEdges("Symptom", vertex['to_id'])
                parent_ids.append(e_edges[1]['to_id'])
            elif vertex['to_type'] == "Disease":
                child_ids.append(vertex['to_id'])
        for parent_id in parent_ids:
            for child_id in child_ids:
                properties = {"weight": 5}
                conn2.upsertEdge("Symptom", f"{parent_id}", "indicates", "Disease", f"{child_id}", f"{properties}")

    elif event_data[0]['attributes']['action'] == "Diagnosis Patient":
        e_edges = conn2.getEdges("Disease", event_edges[1]['to_id'])
        parent_id = e_edges[1]['to_id']
        child_id = event_edges[0]['to_id']
        properties = {"weight": 5}
        conn2.upsertEdge("Disease", f"{parent_id}", "diagnosed_with", "Patient", f"{child_id}", f"{properties}")

    elif event_data[0]['attributes']['action'] == "Diagnosis Care Provider":
        e_edges = conn2.getEdges("Disease", event_edges[0]['to_id'])
        parent_id = e_edges[1]['to_id']
        child_id = event_edges[1]['to_id']
        properties = {"weight": 5}
        conn2.upsertEdge("Disease", f"{parent_id}", "diagnosed_by", "Care_Provider", f"{child_id}", f"{properties}")

    elif event_data[0]['attributes']['action'] == "Risk Factors Patient":
        e_edges = conn2.getEdges("Patient", event_edges[0]['to_id'])
        parent_id = e_edges[1]['to_id']
        child_ids = []
        for vertex in event_edges:
            if vertex['to_type'] == "Risk_Factors":
                child_ids.append(vertex['to_id'])
        properties = {"weight": 5}
        for child_id in child_ids:
            conn2.upsertEdge("Patient", f"{parent_id}", "exhibits", "Risk_Factors", f"{child_id}", f"{properties}")

    elif event_data[0]['attributes']['action'] == "Risk Factors Disease":
        parent_id = ""
        child_ids = []
        for vertex in event_edges:
            if vertex['to_type'] == "Disease":
                e_edges = conn2.getEdges("Disease", vertex['to_id'])
                parent_id = e_edges[1]['to_id']
            elif vertex['to_type'] == "Risk_Factors":
                child_ids.append(vertex['to_id'])
        properties = {"weight": 5}
        for child_id in child_ids:
            conn2.upsertEdge("Disease", f"{parent_id}", "reverse_reinforces", "Risk_Factors", f"{child_id}", f"{properties}")

    elif event_data[0]['attributes']['action'] == "Key Symptoms":
        parent_id = ""
        child_ids = []
        for vertex in event_edges:
            if vertex['to_type'] == "Disease":
                e_edges = conn2.getEdges("Disease", vertex['to_id'])
                parent_id = e_edges[1]['to_id']
            elif vertex['to_type'] == "Symptom":
                child_ids.append(vertex['to_id'])
        properties = {"weight": 5}
        for child_id in child_ids:
            conn2.upsertEdge("Disease", f"{parent_id}", "reverse_indicates", "Symptom", f"{child_id}", f"{properties}")


        # Build case of rare disease, common disease, uncommon disease with similar symptoms
        # SINGLE DISEASE, first patient, covid
        # MULTIPLE DISEASE, second patient, multiple melinoma + skin cancer + another similar disease
        # Build case study for patient exsibiting similar symptoms
        # P2 experiancing symptom [a,b] == D1
        # P2 ex sympton [c, d] == D2 -> getting worse
        # P2 ex symp [a,b,c,d] == multiple melinoma, and/or D1, and/or D2
        # go to GP give symps -> common D -> D1 specialist -> new symp -> rare D
        # GOAL: mini time loss, possibility of all diseases and making appropriate treatment desision.
        # REDUCE KNOWLEDGE GAP BETWEEN ACTORS global knowledge pool shared in real time with actors
        # THis model provides a wider visibility into multiple diseases at any instance rather than sequencilly
        # Reduce time, increase knowledge to actors. Actors have the some knowledge therefore the some desicion
        # Lack of time and knowlege generate stress in professionals.


