import os
import config
from dotenv import load_dotenv
from flask import Flask, jsonify, request, session
import requests, json
import argparse
from tigerGraph import get_user_profile, check_existing_symptom, check_existing_disease,\
                       create_new_patient_vertex, user_login, create_new_provider_vertex,\
                       care_provider_login, get_provider_profile, provider_add_patient, confirm_diagnosis,\
                       get_patient_info, get_symptom_info, creat_new_location_vertex, check_existing_risk_factors, \
                       check_existing_risk_factors_for_patient, create_event #, get_diseases_id

from stats import do_stats_stuff

app = Flask(__name__)

# TODO:
# Show disease risk factors and or comorbidities (patient risk to disease)
# Optional update when new symptoms are made aware
# Update symptoms disease relationships
# Update patient symptom relationships (if they occure)
# Update model as new information is acquired

# Symptoms to possible recomentations

# Finish covid work through
# Possible treatment

def check_for_server(url_lst):
    for url in url_lst:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Server is running: ", url)
                return url
            else:
                print("Server is not running")
        except requests.exceptions.RequestException as e:
            print("Request error:", e)
            
@app.route('/', methods = ['GET'])
def test():
    if(request.method == 'GET'):
        data = "hello Class!"
        return jsonify({'data': data})

@app.route('/KAN_server', methods=['GET'])
def KAN_server():
    url_lst = [config.KANURL1]
    test_url = check_for_server(url_lst)
    data = {'url': test_url}
    return jsonify(data)

# define a route for the API endpoint
@app.route('/patient_server', methods=['GET'])
def patient_server():
    user_ip = request.remote_addr
    print("IP: ", user_ip)
    print("WHATS GOING ON?")
    # TODO:
        # get ip location 
        # connect to nearest edge cloud
    url_lst = [config.PURL1, config.PURL2]
    # url_lst = [config.PURL1]
    test_url = check_for_server(url_lst)
    data = {'url': test_url}
    return jsonify(data)

@app.route('/care_provider_server', methods=['GET'])
def care_provider_server():
    user_ip = request.remote_addr
    print("IP: ", user_ip)
    print("PROVIDER LOGIN")
    # url_lst = [config.CPURL1] 
    url_lst = [config.CPURL1]
    test_url = check_for_server(url_lst)
    data = {'url': test_url}
    return jsonify(data)


@app.route('/symptoms_server', methods=['GET'])
def symptoms_server():
    user_ip = request.remote_addr
    print("IP: ", user_ip)
    print("WHATS GOING ON?")
    # TODO:
        # get ip location 
        # connect to nearest edge cloud
    # url_lst = [config.SURL1]
    url_lst = [config.SURL1]
    print("SURL: ",url_lst)
    test_url = check_for_server(url_lst)
    data = {'url': test_url}
    return jsonify(data)

@app.route('/disease_server', methods=['GET'])
def disease_server():
    user_ip = request.remote_addr
    print("IP: ", user_ip)
    print("WHATS GOING ON?")
    # TODO:
        # get ip location 
        # connect to nearest edge cloud
    # url_lst = [config.DURL1]
    url_lst = [config.DURL1]
    print("SURL: ",url_lst)
    test_url = check_for_server(url_lst)
    data = {'url': test_url}
    return jsonify(data)

@app.route('/risk_factors_server', methods=['GET'])
def risk_factor_server():
    user_ip = request.remote_addr
    print("IP: ", user_ip)
    print("WHATS GOING ON?")
    # TODO:
        # get ip location 
        # connect to nearest edge cloud
    # url_lst = [config.DURL1]
    url_lst = [config.RFURL1]
    print("RURL: ",url_lst)
    test_url = check_for_server(url_lst)
    data = {'url': test_url}
    return jsonify(data)

@app.route('/event_server', methods=['GET', 'POST'])
def event_server():
    user_ip = request.remote_addr
    print("IP: ", user_ip)
    print("WHATS GOING ON?")
    # TODO:
        # get ip location 
        # connect to nearest edge cloud
    # url_lst = [config.DURL1]
    url_lst = [config.EURL1]
    print("EURL: ",url_lst)
    test_url = check_for_server(url_lst)
    data = {'url': test_url}
    return jsonify(data)

@app.route('/register', methods=['GET', 'POST'])
def register():
    data = request.get_json()

    first_name = data['first_name']
    last_name = data['last_name']
    username = data['username']
    password = data['password']
    email = data['email']
    DOB = data['DOB']
    location = data['location']

    new_patient_id = create_new_patient_vertex(first_name, last_name, username, password, email, DOB)
    print(new_patient_id)
    location_data(new_patient_id, location)
    return jsonify(new_patient_id)

def location_data(user_id, location):
    set_location = creat_new_location_vertex(user_id, location)
    return jsonify(set_location)


@app.route('/provider-register', methods=['GET', 'POST'])
def provider_register():
    data = request.get_json()

    name = data['name']
    email = data['email']
    password = data['password']
    specialty = data['specialty']

    new_provider = create_new_provider_vertex(name, email, password, specialty)
    return jsonify(new_provider)

@app.route('/login', methods=['GET', 'POST'])
def login():
    data = request.get_json()

    email = data['email']
    password = data['password']

    response = user_login(email, password)
    return response

@app.route('/provider-login', methods=['GET', 'POST'])
def provider_login():
    data = request.get_json()

    email = data['email']
    password = data['password']

    response = care_provider_login(email, password)
    return response
    

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    data = request.get_json()

    current_user = data['identity']
    current_user_info = get_user_profile(current_user)

    return jsonify(current_user_info)

@app.route('/provider-profile', methods=['GET', 'POST'])
def provider_profile():
    data = request.get_json()

    current_user = data['identity']
    current_user_info = get_provider_profile(current_user)

    return jsonify(current_user_info)

@app.route('/add-patient', methods=['GET', 'POST'])
def add_patient():
    data = request.get_json()
    patient_id_data = data['patient']
    provider_id_data = data['provider']
    result = get_user_profile(patient_id_data)
    print(result)
    if result == [{'User': []}]:
        return jsonify(result[0])
    else:
        patient_id = provider_add_patient(patient_id_data, provider_id_data)
        return jsonify(patient_id)

@app.route('/symptoms', methods=['GET', 'POST'])
def symptoms():
    data = request.get_json()
    current_user = data['identity']
    current_user_symptoms = json.loads(data['symptoms'])
    symptom_id_list = check_existing_symptom(current_user, current_user_symptoms)
    id_list = json.dumps(symptom_id_list)
    return jsonify(id_list)

@app.route('/disease_data', methods=['GET', 'POST'])
def disease_data():
    data = request.get_json()
    current_user = data['identity']
    current_user_symptoms = json.loads(data['symptoms'])
    user_data = get_patient_info(current_user)
    print("USER DATA:", user_data)
    symptom_data = get_symptom_info(current_user_symptoms)
    print("SYMPTOM DATA:", symptom_data)
    json_list_data = json.dumps(symptom_data)
    return jsonify(user_data, json_list_data)

@app.route('/diseases', methods=['GET', 'POST'])
def diseases():
    data = request.get_json()
    diseases_list = json.loads(data['diseases'])
    symptoms_list = json.loads(data['symptoms'])
    print(diseases_list)
    print(symptoms_list)
    result = check_existing_disease(diseases_list, symptoms_list)
    result = json.dumps(result)
    print("Result: ", result)
    return jsonify(result)

# @app.route('/diseases_id', methods=['GET', 'POST'])
# def diseases_id():
#     data = request.get_json()
#     diseases_list = data['diseases']
#     diseases_id_list = get_diseases_id(diseases_list)
#     print('ID LIST', diseases_id_list)
#     return jsonify(diseases_id_list)

@app.route('/disease_stats', methods=['GET', 'POST'])
def disease_stats():
    data = request.get_json()
    disease = data['item']
    symptoms_list = json.loads(data['message'])
    symptoms = get_symptom_info(data['message'])
    print("STATS:", disease, symptoms)

    stats = do_stats_stuff(disease, symptoms)
    return jsonify(stats)

@app.route('/diagnose', methods=['GET', 'POST'])
def diagnose():
    data = request.get_json()
    patient_id = data['patient_id']
    disease_name = data['disease_name']
    care_provider_id = data['care_provider_id']
    print(disease_name, patient_id)
    result = confirm_diagnosis(disease_name, patient_id, care_provider_id)
    return jsonify(result)

@app.route('/get_symptom_names', methods=['GET', 'POST'])
def get_symptom_names():
    data = request.get_json()
    symptoms = get_symptom_info(data['symptoms'])
    return jsonify(symptoms)

@app.route('/risk_factors_disease', methods=['GET', 'POST'])
def risk_factors_disease_relationship():
    data = request.get_json()
    risk_factors = data['risk_factors_list']
    disease_name = data['disease_name']
    patient_id = data['patient_id']
    risk_factor_name_lists = check_existing_risk_factors(risk_factors, disease_name, patient_id)
    risk_factors_name_list = risk_factor_name_lists[0]
    patient_risk_factors_list = risk_factor_name_lists[1]
    print("PRFL", patient_risk_factors_list)
    return jsonify(risk_factors_name_list, patient_risk_factors_list)


@app.route('/risk_factors', methods=['GET', 'POST'])
def risk_factors_patient_relationship():
    data = request.get_json()
    risk_factors = data['risk_factors']
    patient_id = data['patient_id']
    print("RISK: ", risk_factors, patient_id)
    check_existing_risk_factors_for_patient(risk_factors, patient_id)

    return('hi')

@app.route('/risk_factors_input', methods=['GET', 'POST'])
def risk_factors_input():
    data = request.get_json()
    risk_factors = data['risk_factors']
    patient_id = data['patient_id']
    risk_factors_id_list = check_existing_risk_factors_for_patient(risk_factors, patient_id)
    return jsonify(risk_factors_id_list)


@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    data = request.get_json()
    vertex1_id_list = data['vertex1_id_list']
    vertex2_id_list = data['vertex2_id_list']
    send_vertex = data['send_vertex']
    receive_vertex = data['receive_vertex']
    send_edge_name = data['send_edge_name']
    receive_edge_name = data['receive_edge_name']
    # print("THIS:",vertex1_id_list, vertex2_id_list)
    create_event(vertex1_id_list, vertex2_id_list, send_vertex, receive_vertex, send_edge_name, receive_edge_name)
    return('hi')





if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=6000, help="Port to run the server on")
    args = parser.parse_args()
    port = args.port
    app.run(host="0.0.0.0", port=port)