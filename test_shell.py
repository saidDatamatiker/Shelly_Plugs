import unittest
from unittest import TestCase
from unittest.mock import patch
from main import *

class Test(TestCase):
    """
    Test for get_wifi_list
    """
    @patch('subprocess.check_output')
    def test_get_wifi_list(self, mock_check_output):
        mock_check_output.return_value = b'SSID 1 : MyWifi1 \nSSID 2 : MyWifi2 \nSSID 3 : MyNetwork \n'

        # Test with string "Wifi" - expecting ['MyWifi1', 'MyWifi2']
        self.assertEqual(get_wifi_list("Wifi"), ['MyWifi1', 'MyWifi2'])

        # Test with string "Another" - expecting ['MyNetwork']
        self.assertEqual(get_wifi_list("Network"), ['MyNetwork'])

        # Test with string that doesn't match any element - expect []
        self.assertEqual(get_wifi_list("Default"), [])

    def test_get_wifi_list_non_string_input(self):
        # Test with non string input - expecting raise of TypeError
        with self.assertRaises(TypeError):
            get_wifi_list(123)

    """
    Test for connect_to_device
    """
    @patch('os.system')
    @patch('requests.get')
    def test_connect_to_device(self, mock_get, mock_system):
        # Sets the status code = 200
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'mac': '00:11:22:33:44:55'}
        mock_system.return_value = 0
        result = connect_to_device('my_device')

        # Test with getting result(mac_address) - expecting: 'mac': '00:11:22:33:44:55'
        self.assertEqual(result, {'mac': '00:11:22:33:44:55'})

    @patch('os.system')
    def test_connect_to_device_fail_connection(self, mock_system):
        #Set the connection_code to 1 = not connected
        mock_system.return_value = 1

        # Test with not existing device - expected: DeviceConnectionError
        with self.assertRaises(DeviceConnectionError):
            connect_to_device('my_device')

    @patch('requests.get')
    def test_connect_to_device_fail_get_data(self, mock_get):
        mock_get.return_value.status_code = 400

        # Test with failure connection to http req - expected: DeviceConnectionError
        with self.assertRaises(DeviceConnectionError):
            connect_to_device('my_device')

    def test_connect_to_device_non_string_input(self):
        result = connect_to_device(123)

        # Test with non string input - expected: {}
        self.assertEqual(result, {})

    """
    Test for connect_device_to_wifi
    """
    #Calling the function
    def generate_function_connect_device_to_wifi(self):
        self.string_example = 'my_device'
        self.customer_name = 'Said Mansour'
        self.work_id = 123
        return connect_device_to_wifi(string_example=self.string_example, costumer_name=self.customer_name, work_id=self.work_id)

    @patch('requests.get')
    def test_connect_device_to_wifi_request_error(self, mock_get):

        mock_get.return_value.status_code = 400
        self.generate_function_connect_device_to_wifi()
        # Test with request failure - expected: Exception
        self.assertRaises(Exception)

    @patch('main.connect_to_device')
    def test_connect_device_to_wifi_device_data_is_none(self, mock_connect_to_device):
        self.string_example = 'my_device'
        self.customer_name = 'Said Mansour'
        self.work_id = 123

        mock_connect_to_device.return_value = None
        result = connect_device_to_wifi(string_example=self.string_example, costumer_name=self.customer_name,
                               work_id=self.work_id)
        # Test with device_Data is none - expected: IsNone
        self.assertIsNone(result)

    @patch('requests.post')
    def test_connect_device_to_wifi_requests_call(self, mock_post):
        self.string_example = 'my_device'
        self.customer_name = 'Said Mansour'
        self.work_id = 123

        connect_device_to_wifi(string_example=self.string_example, costumer_name=self.customer_name,
                               work_id=self.work_id)
        mock_post.return_value.status_code = 404

        # Test with request failure - expected: Exception
        self.assertRaises(Exception)


if __name__ == '__main__':
    unittest.main()
