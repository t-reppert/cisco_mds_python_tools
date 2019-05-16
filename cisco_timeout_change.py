#!/usr/bin/python3
#
#  Name:  cisco_timeout_change.py
#  Author:  T. Reppert
#  Description:  This script sets the exec-timeout value to 15 on all switches in 
#                switchlistfile
#
#  Original creation date: 11/05/18
#

import re
import sys
import time
import os
import getpass
import socket
import argparse
import paramiko


def connect(switch_file):
    global remote_conn
    global host
    
    if os.path.isfile(switch_file):
        myfile = open(switch_file, 'r')
        for ip in myfile:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            remote_conn = ()
            ip = ip.strip('\n')
            host = ip
            print_host = host
            print_host = print_host.replace('\n', '')
            try:
                print('\n----- Connecting to %s -----\n' % print_host)
                client.connect(host,timeout=5)
                print('\t*** SSH session established with %s ***' % print_host)
                remote_conn = client.invoke_shell()
                output = remote_conn.recv(1000)
                time.sleep(1)
                if '(config)' not in output:
                    time.sleep(1)
                    print('\t*** Switching to Config Mode ***')
                    remote_conn.send("config t\n")
                    remote_conn.send('\n')
                    time.sleep(1)
                    output = remote_conn.recv(1000)
                if '#' in output:
                    print('\t*** Successfully entered Config Mode ***')
                    remote_conn.send('terminal length 0\n')
                    time.sleep(1)
                    print('\t*** Changing exec-timeout on '+host+' ***')
                    remote_conn.send("line vty\n")
                    time.sleep(1)
                    remote_conn.send("exec-timeout 15\n")
                    time.sleep(1)
                    remote_conn.send("exit\n")
                    time.sleep(1)
                    remote_conn.send("exit\n")
                    print(remote_conn.recv(1000))
                else:
                    print('\t*** Error in attempting config mode ***')
            except paramiko.SSHException:
                print('\t*** Authentication Failed ***')
            except socket.error:
                print('\t*** %s is Unreachable ***' % host)
            client.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('switchlistfile', help='filename including path if not in current directory for switch list')
    args = parser.parse_args()
    
    if os.path.isfile(args.switchlistfile):
        connect(args.switchlistfile)
    else:
        print("Please make sure to have switchlist file.")
    

if __name__ == '__main__':
    main()



