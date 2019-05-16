#!/usr/bin/python3
#
#  Name:  cisco_ssh_key_user_add.py
#  Author:  T. Reppert
#  Description:  This script adds a new user's sshkey to each switch listed in the
#                switchlistfile provided
#
#  Original creation date: 10/16/18
#

import re
import sys
import time
import os
import socket
import argparse
import paramiko


def connect(username, sshkeyfile, switch_file):
    global remote_conn
    global host
    with open(sshkeyfile, 'r') as f:
        sshkey=f.read()
    
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
                    print('\t*** Adding user and their ssh key on '+host+' ***')
                    # remove user before adding again
                    remote_conn.send("no username "+username+"\n")
                    time.sleep(1)
                    remote_conn.send("username "+username+" password 5 ! role network-admin\n")
                    time.sleep(1)
                    remote_conn.send("username "+username+" sshkey "+sshkey+"\n")
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
    parser.add_argument('sshkeyfile', help='filename including path if not in current directory for users sshkey')
    parser.add_argument('switchlistfile', help='filename including path if not in current directory for switch list')
    parser.add_argument('username', help='username of user to add to switch')
    args = parser.parse_args()
    
    # sshkeyfile should be in this format:
    # ssh-rsa AAAAB3NzaC12cyEAAAADAQABAAABAQDnZNT3fEvvROHtB+uKgkVso+XQfh2PanSx9WhYm/TH4L1LqwM5H/3+YiEpgD2Mm5tjMSJDTZAWkagTAm5GmrnC0MuvhD2/gmsSFzOp2PR2vTieIqWawAQTAdssZOA8StZzAOmVkLpHGkZtsutP0ZPqXSU3dxP5HcoYSqWEyMDUOxwTfNKStmVGlw+nK8G3RTU+i8Y8m/SD+TJxB4v0Sbkh32S6d6CuNmVmuhhZIB74Ly7qwz6C8S/FvDSesZRO9iDWgDSbu5qULD1S+q2Vu97LE5d/7efaDSgnytasJl1yKAqn/KpL2/KDCYX6nMVbVSEaMdXzUCbhCeyKhDcHVUVn somebody@somewhere
    # 
    # switchlistfile should just be a text file with a list of each switch name accessible via ssh
    # 
    # Assumption:  The user executing this script has admin access and SSH key enabled on all switches in switchlistfile to avoid having to login to each
    #              switch.

    if os.path.isfile(args.switchlistfile) and os.path.isfile(args.sshkeyfile) and args.username:
        connect(args.username,args.sshkeyfile,args.switchlistfile)
    else:
        print("Please make sure to have username and both sshkey and switchlist files.")
     

if __name__ == '__main__':
    main()



