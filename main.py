import subprocess
import time
import requests
import os
import pandas as pd
import datetime

class DeviceConnectionError(Exception):
    pass

def get_wifi_list(string_contains: str):
    """
    This function get the whole wifi list and return those who conatins @param.
    :param: string_contains: a specific word you search for in wifi_list
    :return: list of wifi elements which is available and contains the string_contains or empty list if nothing found
    :except: trying to get wifilist, if something failed exception will be called.
    :raise: An CalledProcessError, as an example could be when wifi is turned off.
    """
    if not isinstance(string_contains, str):
        raise TypeError("The input must be a string")

    try:
        # Getting wifi list (available)
        output = subprocess.check_output(['netsh', 'wlan', 'show', 'network'])
        # Decoding data and split it
        networks = [line.split(':')[1][1:-1] for line in output.decode('latin-1').split('\n') if "SSID" in line]
        # Filter network and get those that contain the given string
        result = [network for network in networks if string_contains in network]
        if len(result) > 0:
            return result
        else:
            return []
    except subprocess.CalledProcessError as e:
        # Could be if wifi is switched off on laptop
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
    time.sleep(1)
    return []


def connect_to_device(ssid: str):
    """
    This function take a name of the device as parameter,
    and trying to connect with the device by using OS library
    :param ssid: the name of the device
    :return: basic data of device as type, mac, ect.
    :except: if device failed to connect, exception will be called
    """

    if not isinstance(ssid, str):
        print("Ssid not a string")
        return {}
    else:
        # Command to connect to the device
        command = "netsh wlan connect name=\"" + ssid + "\" ssid=\"" + ssid + "\" interface=Wi-Fi"
        # Try to connect
        try:
            print("Trying to connect with", ssid)
            connect = os.system(command)
            print(connect, "printer")
            # Delay for 2 seconds until connecting
            time.sleep(2)

            # If connecting sucessfully
            if connect == 0:
                url_shelly = 'http://192.168.33.1/shelly'
                data_shelly = requests.get(url_shelly)
                if data_shelly.status_code == 200:
                    print("Mac addresse:", data_shelly.json()['mac'])
                    return data_shelly.json()
                else:
                    raise DeviceConnectionError("Failed to retrieve data from device")
            else:
                raise DeviceConnectionError("Failed to connect to device")

        # connection failed
        except Exception as e:
            raise DeviceConnectionError("Could not connect with device") from e

def connect_device_to_wifi(string_example: str, costumer_name: str = "", work_id: int = 0,
    wifi_backup_name: str = "NNEHotspotTest", wifi_backup_password: str = "NNEHotspotTest",
    program_version: str = 'v.0.1'):

    """
    This function has to connect each device with the wifi, and setting the values
    :param string_example: The part of device name you searching for
    :param wifi_name
    :param wifi_key
    :param wifi_backup_name
    :param wifi_backup_password
    :return: Device connected to wifi, and all values is set
    """
    if not costumer_name:
        costumer_name = input("Kundenavn: ")
    if not work_id:
        work_id = input("Indtast workspace id: ")
    #Declare attribute
    wifi_name = 'NNEHotspotTest'
    wifi_key = 'NNEHotspotTest'
    remark_wifi = ""
    url_rawdata = "https://rawdata-cifpsw2ysq-ew.a.run.app/rawentry"
    #Getting wifi from workspace if exist else use backup
    try:
        workspace_res = requests.get(
            f'https://workspaces-services-cifpsw2ysq-ew.a.run.app/api/workspaces?text={costumer_name}')
        print(workspace_res.json())
        for workspace in workspace_res.json():
            if workspace_res.ok and workspace['id'] == int(work_id):
                if workspace['ssid'] != 'not provided' and workspace['ssid_pass'] != 'not provided':
                    wifi_name = workspace['ssid']
                    wifi_key = workspace['ssid_pass']
                    break #Stops the loop if found
                else:
                    remark_wifi = "Primary wifi not found"
            else:
                remark_wifi = "Primary wifi not found"
    except:
        remark_wifi = "Primary wifi not found"
        print("Workspace not found - Continue with backupWIFI")

    # Trying 2 times to connect to the list of devices
    connected = True
    test = 0

    while connected:
        # All element in wifi list
        wifi_list = get_wifi_list(string_example)

        if len(wifi_list) == 0:
            print(f"Wifi list dont conatain any element with '{string_example}'")
            test += 1

            if test == 2:
                connected = False
            # Ignoring forthcoming code
            continue

        print(wifi_list)
        print("-----------------------------------------")

        # Dataframe header:
        df = pd.DataFrame(
            columns=['Version','Costumer_name','Workspace_id','Name_of_device', 'Type', 'Mac_Address','Date', 'Wifi_name', 'Wifi_backup_name', 'Mqtt_server',
                     'Mqtt_enable', 'Mqtt_retain', 'Mqtt_user', 'Mqtt_update_period', 'Auto_on', 'Wifi status','SPECIAL remark'])

        for device_name in wifi_list:
            count = 0
            while count < 2:
                count += 1
                # Connecting to each device
                device_data = connect_to_device(device_name)
                if device_data == None:
                    break
                print(f"This is {count} time for device:{device_data['mac']}")
                data_df = {
                    'Version': program_version,
                    'Costumer_name': costumer_name,
                    'Workspace_id': work_id,
                    'Name_of_device': device_name,
                    'Type': device_data['type'].upper(),
                    'Mac_Address': device_data['mac'],
                    'Date': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    'Wifi_name': wifi_name,
                    'Wifi_backup_name': wifi_backup_name
                }

                # Generation 1
                if device_data['type'].upper() == 'SHPLG-S':
                    # Url for request
                    url_settings = 'http://192.168.33.1/settings'
                    # Data that needs to be posted
                    payload_first_wifi = {'ssid': f'{wifi_name}', 'key': f'{wifi_key}'}
                    payload_second_wifi = {'ssid': f'{wifi_backup_name}', 'key': f'{wifi_backup_password}'}
                    # Checking status code of request
                    payload_settings = {
                        'mqtt_enable': True,
                        'mqtt_retain': True,
                        'mqtt_user': "",
                        'mqtt_update_period': 300,
                        'mqtt_server': "35.206.187.30:" +
                                       requests.get(url_settings).json()['mqtt']['server'].split(':')[1]
                    }

                    # HTTP reuqest
                    try:
                        res_relay = requests.post(url_settings + '/relay/0', data={'auto_on': 120})
                        res_settings = requests.post(url_settings, data=payload_settings)
                        res_second_wifi = requests.post(url_settings + '/sta1', data=payload_second_wifi)
                        res_first_wifi = requests.post(url_settings + '/sta', data=payload_first_wifi)
                        data_get = requests.get(url_settings).json()
                        print(
                            f'Relay: {res_relay.status_code} {res_relay.text}  \nSettings_ {res_settings.status_code} {res_settings.text}  '
                            f'\nWifi_First {res_first_wifi.status_code} {res_first_wifi.text}  \nWifi_Second {res_second_wifi.status_code} {res_second_wifi.text}')

                        #TODO: must be changed after connection enabled
                        remark_connection = "OK"

                        # Define a row for dataframe
                        data_df.update({
                            'Mqtt_server': data_get['mqtt']['server'] ,
                            'Mqtt_enable': data_get['mqtt']['enable'],
                            'Mqtt_retain': data_get['mqtt']['retain'],
                            'Mqtt_user': data_get['mqtt']['user'],
                            'Mqtt_update_period': data_get['mqtt']['update_period'],
                            'Auto_on': data_get['relays'][0]['auto_on'],
                            'Wifi status': remark_wifi,
                            'SPECIAL remark': remark_connection
                        })
                        df.loc[len(df)] = data_df

                        #TODO send rawdata back by http req
                        payload_rawData_sensor38 = {
                            "physical_id": data_get['mqtt']['id'],
                            "hub_id": costumer_name,
                            "measured_ts":datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                            "relayed_ts": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                            "sensor_type": 38,
                            "topic": "SHELLY",
                            "value": wifi_name,
                            "packet_version": 1
                        }
                        payload_rawData_sensor0 = {
                            "physical_id": data_get['mqtt']['id'],
                            "hub_id": costumer_name,
                            "measured_ts":datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                            "relayed_ts": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                            "sensor_type": 0,
                            "topic": "SHELLY",
                            "value": f"Restart cause: 0; Version: {program_version}, Woke: {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')}",
                            "packet_version": 1

                        }
                        requests.post(url_rawdata, data= payload_rawData_sensor38)
                        requests.post(url_rawdata, data= payload_rawData_sensor0)

                        # Enable wifi
                        # enable_wifi = requests.post(url_settings + '/sta', {'enabled': 1})
                        # print("wifi enabled", enable_wifi.status_code)

                    except requests.exceptions.ConnectionError:
                        # Continue with next
                        print("Wifi enabled, connection lost")
                        break
                    except Exception as e:
                        remark_connection = f"Failed {e}"
                        data_df.update({
                            'Wifi status': remark_wifi,
                            'SPECIAL remark': remark_connection
                        })
                        df.loc[len(df)] = data_df
                        break
                    # Exit loop
                    count = 2
                # Generation PLUS S MODEL
                elif device_data['type'].upper() != 'SHPLG-S':
                    # Url for request
                    url_gen2_wifi_set = "http://192.168.33.1/rpc/WiFi.SetConfig"
                    url_gen2_mqtt_set = "http://192.168.33.1/rpc/MQTT.SetConfig"
                    url_gen2_wifi_get = "http://192.168.33.1/rpc/WiFi.GetConfig"
                    url_gen2_mqtt_get = "http://192.168.33.1/rpc/MQTT.GetConfig"
                    # Data for request
                    payload_gen2_wifi = {
                        "sta": {
                            'ssid': f'{wifi_name}',
                            'key': f'{wifi_key}'
                        },
                        "sta1": {
                            'ssid': f'{wifi_backup_name}',
                            'key': f'{wifi_backup_password}'
                        }
                    }
                    res_mqtt_gen2 = requests.get(url_gen2_mqtt_get)
                    payload_gen2_mqtt = {
                        "enable": True,
                        "user": "",
                        "server": "35.206.187.30:" + res_mqtt_gen2.json()['server'].split(':')[1]

                    }

                    # HTTP request
                    try:
                        requests.post(url_gen2_wifi_set, params={"config": payload_gen2_wifi})
                        requests.post(url_gen2_mqtt_set, params={"config": payload_gen2_mqtt})

                        # Get information and append information to dict list (rows of csv file)
                        data_get_wifi = requests.get(url_gen2_wifi_get)
                        data_get_mqtt = requests.get(url_gen2_mqtt_get)

                        # TODO: must be changed after connection enabled
                        remark_connection = "OK"
                        data_df.update({
                            'Mqtt_server': data_get_mqtt['mqtt']['server'],
                            'Mqtt_enable':  data_get_mqtt['mqtt']['enable'],
                            'Mqtt_retain': "",
                            'Mqtt_user': data_get_mqtt['mqtt']['user'],
                            'Mqtt_update_period': "",
                            'Auto_on': "",
                            'Wifi status': remark_wifi,
                            'SPECIAL remark': remark_connection
                        })
                        df.loc[len(df)] = data_df

                        #TODO send rawdata back by http req
                        payload_rawData_sensor38_gen2 = {
                            "physical_id": data_get_mqtt['mqtt']['client_id'],
                            "hub_id": costumer_name,
                            "measured_ts": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                            "relayed_ts": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                            "sensor_type": 38,
                            "topic": "SHELLY",
                            "value": wifi_name,
                            "packet_version": 1
                        }
                        payload_rawData_sensor0_gen2 = {
                            "physical_id": data_get_mqtt['mqtt']['client_id'],
                            "hub_id": costumer_name,
                            "measured_ts": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                            "relayed_ts": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                            "sensor_type": 0,
                            "topic": "SHELLY",
                            "value": f"Restart cause: 0; Version: {program_version}, Woke: {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')}",
                            "packet_version": 1

                        }
                        requests.post(url_rawdata, data=payload_rawData_sensor38_gen2)
                        requests.post(url_rawdata, data=payload_rawData_sensor0_gen2)

                        # Connecting to wifi
                        payload_gen2_wifi["sta"]["enable"] = True
                        requests.post(url_gen2_wifi_set, params={"config": payload_gen2_wifi})


                    except requests.exceptions.ConnectionError:
                        print("Wifi enabled, connection lost")
                        break
                    except Exception as e:
                        remark_connection = f"Failed {e}"
                        data_df.update({
                            'Wifi status': remark_wifi,
                            'SPECIAL remark': remark_connection
                        })
                        df.loc[len(df)] = data_df
                        break
                    # Exit loop
                    count = 2

        # Converting to a csv
        df.to_csv("Shelly-Plug.csv")
        #Breaking whole loop and program stops
        break



# Main
#connect_device_to_wifi("shelly", costumer_name='nne', work_id=22)
connect_device_to_wifi("shelly")