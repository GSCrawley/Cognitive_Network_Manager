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
    print("DATA", data)
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
        # properties = {"weight": 5}
        # conn2.upsertEdge(f"Event", f"{event_id}", f"{send_edge_name}", f"{send_vertex}", f"{id}", f"{properties}")
        # get list of vertex events, return most recent event.
        history = conn1.runInstalledQuery("getEventHistory", {"vertexType": send_vertex, "vertexId": id})
        history = history[0]['result'][0]['attributes']['result.event']
        connect_history(history, new_vertex_id, send_vertex)


    for id in vertex2_id_list:
        new_vertex_id = update_attributes(event_id, receive_vertex, id, receive_edge_name)
        # properties = {"weight": 5}
        # conn2.upsertEdge(f"Event", f"{event_id}", f"{receive_edge_name}", f"{receive_vertex}", f"{id}", f"{properties}")
        if vertex1_id_list[0] == "genesis":
            break
        history = conn1.runInstalledQuery("getEventHistory", {"vertexType": receive_vertex, "vertexId": id})
        # print("HISTORY", vertex1_id_list[0])
        history = history[0]['result'][0]['attributes']['result.event']
        connect_history(history, new_vertex_id, receive_vertex)
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
    keylist = []
    valuelist = []
    for key, value in events.items():
        keylist.append(key)
        valuelist.append(value)
    attributes["event"] = {
            "keylist": keylist,
            "valuelist": valuelist,
        }
    conn2.upsertVertex(f"{vertex}", f"{vertex_id}", attributes)

    properties = {"weight": 5}
    conn2.upsertEdge(f"Event", f"{event_id}", f"{edge}", f"{vertex}", f"{vertex_id}", f"{properties}")
    return(vertex_id)

def connect_history(history, new_vertex_id, vertex):
    items = [(int(time), value) for time, value in history.items()]
    # Sort the list of tuples by timestamp
    sorted_items = sorted(items, key=lambda x: x[0])
    if len(sorted_items) > 1:
        latest_event = sorted_items[-2][1]
        data = conn2.getEdges("Event", latest_event)
        print("LATEST", data)
        connect_self(data, vertex, new_vertex_id)
    else:
        # NOT THE WAY???
        # current_event = sorted_items[0][1]
        # data = conn2.getEdges("Event", current_event)
        # print("CURRENT EVENT", current_event)
        # connect_parent(data, vertex, new_vertex_id)
        return()
    return()
    

def connect_self(data, vertex, new_vertex_id):
    print("TEST", data[0]["to_type"])
    print("SEND", vertex)
    # extracted_data = {}
    # conn2.getVerticesById(item.key, id)
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
            print("PREVIOUS", prev)
            print("CURRENT", curr)

def connect_parent(data, vertex, new_vertex_id):
    print("CURRENT EVENT DATA", data)



