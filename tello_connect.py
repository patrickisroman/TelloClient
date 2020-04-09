import subprocess
import re
import time
import socket
import threading

from wireless import Wireless

wireless = Wireless()
tello_endpoint_regex = re.compile('TELLO-*')

# single threaded, single-command executions
class TelloClient(object):
    HOST = ''
    PORT = 9000
    LOCAL_ADDRESS = (HOST, PORT)
    TELLO_ADDRESS = ('192.168.10.1', 8889)

    def __init__(self):
        self.socket = None
        self.recv_thread = threading.Thread(target=self.__recv)
        self.commands = []
        self.responses = []
    
    def __recv(self):
        while self.socket:
            try:
                data, server = self.socket.recvfrom(2048)
                self.responses.append(data.decode(encoding='utf-8'))
            except:
                break
    
    def __create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(TelloClient.LOCAL_ADDRESS)
        return sock
    
    def start(self):
        if self.socket:
            return True
        
        if not self.__check_tello_endpoint():
            if not self.__try_tello_connect():
                return False

        self.socket = self.__create_socket()
        if not self.socket:
            return False
        
        self.recv_thread.start()
        return True
    
    def stop(self):
        if not self.socket:
            return True
        
        self.socket.close()
        self.socket = None
        self.recv_thread.join()
        self.recv_thread = threading.Thread(target=self.__recv)
        self.commands = []
        self.responses = []
    
    def send_command(self, cmd, await_response=True):
        cmd = cmd.strip()
        if not self.socket:
            return False

        msg = cmd.encode(encoding="utf-8") 
        if not self.socket.sendto(msg, TelloClient.TELLO_ADDRESS):
            return False
        
        self.commands.append(cmd)
        if not await_response:
            return True
        
        return self.recv_response(block=True)
    
    def recv_response(self, block=False, block_time_ms=50):
        if len(self.responses) == 0:
            if self.socket is None or not block:
                return None
            time.sleep(block_time_ms/1000)
            return self.recv_response(block, block_time_ms)

        return (self.commands.pop(), self.responses.pop())

    def __check_tello_endpoint(self):
        check_endpoint_cmd = subprocess.run(['airport', '-I'], stdout=subprocess.PIPE, text=True)
        endpoint_data = check_endpoint_cmd.stdout
        state = endpoint_data.split('state:')[1].splitlines()[0].strip()
        name = endpoint_data.split(' SSID:')[1].splitlines()[0].strip()
        return tello_endpoint_regex.match(name) is not None and state == 'running'

    def __try_tello_connect(self, max_retries=3, retry_delay_ms=3000):
        if self.__check_tello_endpoint():
            return True
        
        list_endpoints_cmd = subprocess.run(['airport', '-s'], stdout=subprocess.PIPE, text=True)
        endpoints = list_endpoints_cmd.stdout.splitlines()[1:]
        formatted_endpoints = []

        for ep in endpoints:
            ep_entries = ep.split()
            formatted_endpoints.append({
                'name' : ep_entries[0],
                'mac_address' : ep_entries[1],
                'security_protocol' : ep_entries[6]
            })
        
        tello_endpoints = list(filter(tello_endpoint_regex.match, [e['name'] for e in formatted_endpoints]))

        if len(tello_endpoints) == 0:
            print('No Tello endpoint to connect to')
            return False

        wireless.connect(tello_endpoints[0], password='')

        for r in range(max_retries):
            if self.__check_tello_endpoint():
                return True
            time.sleep(retry_delay_ms)
        
        return self.__check_tello_endpoint()
