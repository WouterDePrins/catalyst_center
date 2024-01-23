## Script to bulk asign devices to a specific site

import requests
import urllib3
urllib3.disable_warnings()
import time

# Catalyst Center creds
catalyst_center_ip = "10.10.10.10"
catalyst_center_username = "admin"
catalyst_center_password = "password"

# Array of objects where YOU need to define the siteName (that corresponds to the siteName in Catalyst Center) and the device IP address you want to add.
# => TO BE FILLED IN or load it through CSV.
device_list = [
    {"siteName" : "DEV", "deviceIp": "10.10.10.10"}
]

# Generic API call
def api(url, method, **kwargs):
    try:
        a = requests.request(method, url, data=None, **kwargs, verify=False, timeout=5)
        if a.status_code == 200:
            return a.json()
        else:
            return False
    except requests.exceptions.RequestException as e:
        return False

# Auth against Catalyst Center
def auth():
    url = f"https://{catalyst_center_ip}/api/system/v1/auth/token"
    return api(url, "POST", auth=(catalyst_center_username, catalyst_center_password))

# Set token globally so you don't need to auth every time when iterating
token = auth()

# Get all sites !be aware this has a limit of 500 records!
def getSites():
    sites = []

    ## infinite loop unless none or only one site is returned (from my testing if you offset >500, you always get 1 object back)
    offset = 1
    while True: 
        url = f"https://{catalyst_center_ip}/dna/intent/api/v2/site?offset={offset}"
        headers = {'x-auth-token': token['Token']}
        response = api(url, "GET", headers=headers)
        # break if none or 1 is returned
        if len(response['response']) <= 1:
            break
        # add sites with SiteName and SiteId to sites array
        for i in response['response']:
            sites.append({'siteName': i["name"], 'siteId': i["id"]})
        offset += 500
    return sites

sites = getSites()

# Filter if siteName is equal to siteName defined in "device_list"
def filter_by_siteName(site, siteName):
    return site["siteName"] == siteName

# iteration to assign specific device to site.
for j in device_list:
    # Find SiteID
    siteId = list(filter(lambda site: filter_by_siteName(site, j['siteName']), sites))
    url = f"https://{catalyst_center_ip}/dna/intent/api/v1/assign-device-to-site/${siteId[0]['siteId']}/device"
    headers = {"x-auth-token": token['Token'], "__runsync": "false", "__persistbapioutput": "true"}
    data = { "device": [
        {
            "ip": j["deviceIp"]
        }
    ]}
    response = api(url, "POST", json=data, headers=headers)
    if response != False:
        print(f"Device with IP: {j['deviceIp']} is added to site: {siteId[0]['siteName']}")
    else:
        print(f"Error trying to add device with IP: {j['deviceIp']} to site: {siteId[0]['siteName']}")
    time.sleep(0.100)