import requests
from furl import furl

url_string = 'http://10.5.55.3:8080/rest/items'
test_url_string = 'http://192.168.43.142:8080/rest/items'
test_url_string2 = 'http://192.168.43.62:8080/rest/items'

url_str = test_url_string2

def get_state(item_name):
    item_url = furl(url_str)
    item_url.path = item_url.path / item_name / 'state'
    #print(f'iface get_state: item_url url = {item_url.url}')
    r = requests.get(item_url.url)
    print(f'request status_code: {r.status_code}')
    if r.status_code == 200:    # 200 OK
      return r.text
    else:
      return 'Error'

def post_state(item_name, state):
    item_url = furl(url_str)
    # Add item name to url:
    item_url.path = item_url.path / item_name 
    #print(f'iface post_state: item_url url = {item_url.url}')
    # add state param:
    #print(f'iface post state: item_url url = {item_url.url}, param: {state}')
    
    headers = {'Content-type': 'text/plain'}
    try:
        r = requests.post(item_url.url, state, headers=headers)
    except requests.ConnectionError as e:
        print(f'fatal error: {e}')    #should I also sys.exit(1) after this?

    if 'r' in locals():
        print(f'request status_code: {r.status_code}')
        if r.status_code == 200:    # 200 OK 
            return 'OK'
    return 'Error'

# ----------------------------------------------------------------------------------------------------------------
# For testing:
if __name__ == '__main__':
    #put_state('Kueche2_KNX_Licht_Schalten', 'OFF')
    #put_state('Kuche_Jalousie1', '0')
    state = get_state('Kueche2_KNX_Licht_Schalten')  # Kochtisch Licht
    #state = get_state('Kuche_Jalousie1')
    print(state)
    # curl -X POST "http://192.168.43.142:8080/rest/items/Kueche2_KNX_Licht_Schalten" -H "Content-Type: text/plain" -d "OFF"
    post_state('Kueche2_KNX_Licht_Schalten', 'ON')
    state = get_state('Kueche2_KNX_Licht_Schalten')  # Kochtisch Licht
    print(state)


