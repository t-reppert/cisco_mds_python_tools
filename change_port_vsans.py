#!/usr/local/bin/python3.6
#
#  Name:  change_port_vsans.py
#  Author:  T. Reppert
#  Description:  This script Tests or Executes changing VSAN assignment on csv list of switch, port, target_vsan 
# 
#  Original creation date:  8/21/2018
#

import paramiko
import re
import sys
import os
import csv
from pprint import pprint
import json
import time
from datetime import datetime
import argparse
import socket
from pathlib import Path

switch_ports = {}

def main():
    startTime = datetime.now()
    # Argument options:
    # -f <csv file with switchname,port,vsan> 
    # -t test mode
    # -e execute mode
    # Example csv file format:
    # switch,port,vsan
    # name1,fc1/1,10
    # name2,fc1/2,20
    # name3,fc2/1,30
      
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', action='store',dest='file', type=str, help="csv file with switch, port, vsan info to process.", required=True)
    parser.add_argument('-t', action='store_true', help="test without executing change...")
    parser.add_argument('-e', action='store_true', help="Execute change...")
    args = parser.parse_args()
    
    file = Path(args.file)
    if file.is_file():
        print('Processing file {} ...'.format(file.name))
        reader = csv.DictReader(open(args.file))
        switch = ""
        for row in reader:
            switch = row.pop('switch')
            if switch not in switch_ports: 
                switch_ports[switch] = {} 
            port = row.pop('port')
            vsan = row.pop('vsan')
            switch_ports[switch][port] = vsan             

    if args.t:
        print('TEST Mode.')
        pprint(switch_ports)
        test_vsan_change(switch_ports)

    if args.e:
        print('EXECUTE Mode.')
        # Process switch port vsan changes
        execute_vsan_change(switch_ports)
    if not args.t and not args.e:
        print('PRINT DATA Mode.')
        pprint(switch_ports)

    print('Processing finished.')
    print(datetime.now() - startTime)

def execute_vsan_change(switch_ports):
    # Execute all changes on provided switch ports
    for switch, ports in switch_ports.items():
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        remote_conn = ()
        switch = switch.strip('\n')
        try:
            print('\n----- Connecting to {} -----\n'.format(switch))
            client.connect(switch,timeout=5)
        except paramiko.SSHException:
            print('\t*** Authentication Failed ***')
            sys.exit()
        except socket.error:
            print('\t*** {} is Unreachable ***'.format(switch))
            sys.exit()
        print('\t*** SSH session established with {} ***'.format(switch))
        remote_conn = client.invoke_shell()
        for port, vsan in ports.items():
            remote_conn.send('\n')
            time.sleep(1)
            remote_conn.send('\n')
            time.sleep(1)
            remote_conn.send('\n')
            output = remote_conn.recv(1000).decode()
            time.sleep(1)
            if '(config)' not in output:
                time.sleep(1)
                print('\t*** Switching to Config Mode ***')
                remote_conn.send("config t\n")
                remote_conn.send('\n')
                time.sleep(1)
                output = remote_conn.recv(1000).decode()
            if '#' in output:
                print('\t*** Successfully entered Config Mode ***')
                remote_conn.send('terminal length 0\n')
                time.sleep(1)
                print('\t*** Entering vsan database on '+switch+' ***')
                remote_conn.send("vsan database\n")
                time.sleep(1)
                output = remote_conn.recv(1000).decode()
            if '(config-vsan-db)' in output:
                print('\t*** Changing vsan on '+switch+' port '+port+' to vsan '+vsan+' ***')
                remote_conn.send("vsan "+vsan+" interface "+port+"\n")
                time.sleep(1)
                remote_conn.send("y\n")
                time.sleep(1)
                remote_conn.send("exit\n")
                time.sleep(1)
                output = remote_conn.recv(1000).decode()
                print(output)
            else:
                print('\t*** Error in attempting config mode ***')
        client.close()

def test_vsan_change(switch_ports):
    # Test run through target list of switch ports to be changed
    # This will only show current settings for each port and not make any change
    for switch, ports in switch_ports.items():
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        remote_conn = ()
        switch = switch.strip('\n')
        try:
            print('\n----- Connecting to {} -----\n'.format(switch))
            client.connect(switch,timeout=5)
        except paramiko.SSHException:
            print('\t*** Authentication Failed ***')
            sys.exit()
        except socket.error:
            print('\t*** {} is Unreachable ***'.format(switch))
            sys.exit()
        print('\t*** SSH session established with {} ***'.format(switch))
        remote_conn = client.invoke_shell()
        for port, vsan in ports.items():
            remote_conn.send('\n')
            time.sleep(1)
            remote_conn.send('\n')
            time.sleep(1)
            remote_conn.send('\n')
            output = remote_conn.recv(1000).decode()
            time.sleep(1)
            if '(config)' not in output:
                time.sleep(1)
                print('\t*** Switching to Config Mode ***')
                remote_conn.send("config t\n")
                remote_conn.send('\n')
                time.sleep(1)
                output = remote_conn.recv(1000).decode()
            if '#' in output:
                print('\t*** Successfully entered Config Mode ***')
                remote_conn.send('terminal length 0\n')
                time.sleep(1)
                print('\t*** Showing vsan membership for port '+port+' ***')
                remote_conn.send("sh vsan membership interface "+port+"\n")
                time.sleep(1)
                remote_conn.send("sh interface "+port+" brief\n")
                time.sleep(1)
                output = remote_conn.recv(1000).decode()
                print(output)
            else:
                print('\t*** Error in attempting config mode ***')
        client.close()

if __name__ == '__main__':
    main()
