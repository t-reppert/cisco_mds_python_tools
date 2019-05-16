#!/usr/bin/python3
#
#  Name:  cisco_mds_snmp_trap.py
#  Author:  T. Reppert
#  Description:  This script will enable/disable SNMP traps on all switches listed in the switchlistfile
#
#  Original creation date: 3/15/17
#

import re
import sys
import time
import os
import getpass
import socket
import argparse
import paramiko


def connect(state,switch_file):
    if state == "enable":
        statestring = ""
        commandmsg = "Enabling"
    elif state == "disable":
        statestring = "no "
        commandmsg = "Disabling"
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
                    print('\t*** '+commandmsg+' SNMP traps on switch '+host+' ***')
                    remote_conn.send(statestring+"snmp-server enable traps link\n")
                    time.sleep(1)
                    remote_conn.send("exit\n")
                    time.sleep(1)
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
    parser.add_argument('action', help='(enable or disable) SNMP traps on switch list')
    parser.add_argument('switchlistfile', help='filename including path if not in current directory for switch list')
    args = parser.parse_args()
    
    if os.path.isfile(args.switchlistfile):
        if args.action == "enable":
            connect("enable",args.switchlistfile)
        elif args.action == "disable":
            connect("disable",args.switchlistfile)
        else: 
            print("enable OR disable are expected arguments.")
    else:
        print("Please make sure to use 'enable' or 'disable' followed by switchlist file.")
    

if __name__ == '__main__':
    main()



