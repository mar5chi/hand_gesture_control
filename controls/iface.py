import requests
from furl import furl
from HgcException import HgcException

url_string = 'http://10.5.55.3:8080/rest/items'
test_url_string = 'http://192.168.43.142:8080/rest/items'
test_url_string2 = 'http://192.168.43.62:8080/rest/items'

url_str = test_url_string2

def get_state(item_name):
    item_url = furl(url_str)
    item_url.path = item_url.path / item_name / 'state'
    try:
        r = requests.get(item_url.url, timeout=5)
        print(f'GET request status_code: {r.status_code}')
        if r.status_code == 200:    # 200 OK
            return r.text
        else:
            return 'Error'
    except requests.ConnectTimeout as ct:
        print('get_state() ConnectTimeout: raising HgcException')
        raise HgcException("Connection time out.")
    except requests.exceptions.RequestException as re:
        print("get_state() Error: ", re)
        raise HgcException("No connection.")
        

def post_state(item_name, state):
    item_url = furl(url_str)
    # Add item name to url:
    item_url.path = item_url.path / item_name 
    
    headers = {'Content-type': 'text/plain'}
    try:
        r = requests.post(item_url.url, state, headers=headers, timeout=5)
        print(f'request status_code: {r.status_code}')
        if r.status_code == 200:    # 200 OK 
            return 'OK'
    except requests.ConnectTimeout as ct:
        print('raising HgcException')
        raise HgcException("Connection time out.")
    except requests.ConnectionError as e:
        print('raising HgcException')
        raise HgcException("Connection error.") 
    except requests.exceptions.RequestException as re:
        print("Error: ", re)
        raise HgcException("No connection.")

