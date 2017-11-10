import json, requests, sys
from http import HTTPStatus

# Will be set below
motherShipUrl = ''

def setMotherShipUrl(url):
    global motherShipUrl
    motherShipUrl = url



''' Return a list of all customers in the system '''
def get_users(token):
    return get(token, '/api/customers?limit=99999', "Error retrieving customers")["data"]



def get_customer(token, name):
    customers = get(token, '/api/customers?limit=99999&textSearch=' + name, msg)
    for customer in customers['data']:
        if(customer['title'] == name):
            return customer

    return None


''' Returns UUID of public customer, or None if there is none '''
def get_public_user_uuid(token):
    return get_user_uuid(token, 'public')



''' Returns UUID of named customer, or None if user not found '''
def get_user_uuid(token, name):
    return get_id(get_customer(token, name))



''' Adds customer and returns JSON customer from database '''
def add_customer(token, name, address, address2, city, state, zip, country, email, phone):
    data = {
        "title": name,
        "address": address,
        "address2": address2,
        "city": city,
        "state": state,
        "zip": zip,
        "country": country,
        "email": email,
        "phone": phone
    }

    return post(token, '/api/customer', data, "Error adding customer '" + name + "'")



''' Returns true if successful, False if the customer wasn't found '''
def delete_customer_by_id(token, id):
    return delete(token, "/api/customer/" + id, "Error deleting customer '" + id + "'")



''' Returns True if successful, False if the customer wasn't found '''
def delete_customer_by_name(token, name):
    id = get_user_uuid(token, name)
    if id == None:
        print("Could not find customer with name " + name)
        return False

    return delete_customer_by_id(token, id)



''' Returns the access token needed by most other methods '''
def get_token(username, password):
    data = '{"username":"' + username + '", "password":"' + password + '"}'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    # json = post("/api/auth/login", None, data, "Error requesting token")

    url = motherShipUrl + "/api/auth/login"
    response = requests.post(url, data=data, headers=headers)
    validateResponse(response, "Error requesting token")

    return json.loads(response.text)["token"]



''' Returns dashboard definition '''
def assign_dash_to_user(token, dashboard_id, customer_id):
    return post(token, '/api/customer/' + customer_id + '/dashboard/' + dashboard_id, None, "Could not assign dashboard '" + dashboard_id + "' to customer '" + customer_id + "'")



''' Returns True if dashboard was deleted, False if it did not exist '''
def delete_dashboard(token, dashboard_id):
    return delete(token, '/api/dashboard/' + dashboard_id, "Error deleting dashboard '" + dashboard_id +"'")



''' Returns dashboard definition '''
def create_dashboard_for_customer(token, customer_name, dash_def):

    dash_name = customer_name + ' Dash' 
    data = {
        "configuration": dash_def["configuration"],
        "title": dash_name,
        "name": dash_name
    }

    # Update the configuration

    return post(token, '/api/dashboard', data, "Error creating new dashboard")



''' Returns dashboard with specified name, or None if we can't find one '''
def get_dashboard_by_name(token, dash_name):
    dashes = get(token, '/api/tenant/dashboards?limit=99999&textSearch=' + dash_name, "Error retrieving dashboard '" + dash_name + "'")['data']
    for dash in dashes:
        if dash['title'] == dash_name:
            return dash

    return None



''' Retrieve dashboard by id '''
def get_dashboard_by_id(token, dash_id):
    return get(token, '/api/dashboard/info/' + dash_id, "Error retrieving dashboard '" + dash_id + "'")



def get_dashboard_definition(token, dash_id):
    return get(token, '/api/dashboard/' + dash_id, "Error retrieving dashboard definition '" + dash_id + "'")



''' Returns named device object, or None if it can't be found '''
def get_device_by_name(token, device_name):
    devices = get(token, '/api/tenant/devices?limit=99999&textSearch=' + device_name, "Error fetching device list with search param '" + device_name + "'")['data']
    for device in devices:
        if device['name'] == device_name:
            return device

    return None



def get_device_name(customer_name):
    return customer_name + ' Device'



''' Returns device object '''
def add_device(token, customer_name, device_type, latitude, longitude):
    if latitude is None or longitude is None:
        print("Must have valid lat/lon in order to add device!")
        exit(1)

    data = {
        "name": get_device_name(customer_name),
        "type": device_type,
    }

    device = post(token, '/api/device', data, "Error adding device '" +  device_type +"' for '" + customer_name + "'")
    device_id = get_id(device)

    data = {
        "latitude": latitude,
        "longitude": longitude
    }
    set_server_attributes(token, device_id, data)

    data = {
        "LED": "Unknown",
        "nonce": 0
    }
    set_shared_attributes(token, device_id, data)
    
    return device



def set_server_attributes(token, device_id, attributes):
    set_attributes(token, device_id, attributes, 'SERVER_SCOPE')



def set_shared_attributes(token, device_id, attributes):
    set_attributes(token, device_id, attributes, 'SHARED_SCOPE')



def set_attributes(token, device_id, attributes, scope):
    post(token, '/api/plugins/telemetry/DEVICE/' + device_id + '/' + scope, attributes, "Error setting " + scope + " attributes for device '" + device_id + "'")



''' Works with Customers, Devices, Dashes '''
def get_id(obj):
    if obj is None:
        return None

    return obj['id']['id']



''' Returns device object we just made pubic '''
def assign_device_to_public_user(token, device_id):
    return post(token, '/api/customer/public/device/' + device_id, None, "Error assigning device '" + device_id + "' to public customer")



''' Returns True if device was deleted, False if it did not exist '''
def delete_device(token, device_id):
    return delete(token, '/api/device/' + device_id, "Error deleting device '" +  device_id +"'")




def pretty_print_request(req):
    print('{}\n{}\n{}\n\n{}'.format('-----------START-----------', req.method + ' ' + req.url, '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()), req.body, ))



def get(token, params, msg):
    url = motherShipUrl + params
    headers = {'Accept': 'application/json'}
    if token is not None:
        headers['X-Authorization'] = 'Bearer ' + token
        
    # req = requests.Request('GET', url, headers=headers)
    # prepared = req.prepare()
    # pretty_print_request(prepared)

    response = requests.get(url, headers=headers)
    validateResponse(response, msg)

    return json.loads(response.text)



def delete(token, params, msg):
    url = motherShipUrl + params
    headers = {'Accept': 'application/json'}
    if token is not None:
        headers['X-Authorization'] = 'Bearer ' + token
        
    # req = requests.Request('DELETE', url, headers=headers)
    # prepared = req.prepare()
    # pretty_print_request(prepared)

    response = requests.delete(url, headers=headers)

    # Don't fail if not found
    if(response.status_code == HTTPStatus.NOT_FOUND):
        return False

    validateResponse(response, msg)

    return True



def post(token, params, data, msg):
    url = motherShipUrl + params
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    if token is not None:
        headers['X-Authorization'] = 'Bearer ' + token

    # req = requests.Request('POST', url, json=data, headers=headers)
    # prepared = req.prepare()
    # pretty_print_request(prepared)

    response = requests.post(url, json=data, headers=headers)
    validateResponse(response, msg)

    if response.text is None or response.text == "":
        return { }

    return json.loads(response.text)



def validateResponse(response, msg):
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(msg + "! " + str(e))
        print("----- BEGIN BODY -----")
        print(response.content)
        print("----- END BODY -----")
        sys.exit(1)
