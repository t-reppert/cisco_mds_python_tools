#!/usr/local/bin/python3.6
#
#  Title:  collect_san_port_usage_data.py
#  Author:  T. Reppert
#  Description:  This script will collect port usage count for every MDS switch and write it to a PostgreSQL database
#
#  Original creation date: 12/7/2018
#

import psycopg2
import os
import sys
import subprocess
import string
import re
from pprint import pprint
import datetime
from datetime import date
import paramiko
import logging

# Setup logging globally
logging.basicConfig(filename='/var/log/san_port_usage_table_update.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p :')


def run_switch_cmd(switch, cmd):
    """
        Run the provided switch command against given switch and return output as list.  Log and exit on error.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(switch, timeout=8)
    except Exception as e:
        print(f"Issue with connecting to {switch}.  Please investigate: {e}")
        logging.info("Issue with connecting to %s.  Please investigate: %s " % (switch, e))
        sys.exit()
    try:
        stdin1, stdout1, stderr1 = ssh.exec_command(cmd)
        stdin1.flush()
    except Exception as e:
        print(f"Issue with executing command {cmd} on {switch}.  Please investigate: {e}")
        logging.info("Issue with executing command %s on %s.  Please investigate: %s " % (cmd, switch, e))
        sys.exit()
    
    return stdout1.read().decode("utf-8").splitlines()


def parse_port_detail_array(port_detail_output):
    port_admin_down_regex = re.compile(r'Administratively down', re.I)
    admin_down_ports = 0
    for line in port_detail_output:
        # Check if line starts with port name and collect fields
        if port_admin_down_regex.search(line):
            admin_down_ports += 1  
    return admin_down_ports


def parse_port_brief_array(port_brief_output):

    port_fc_regex = re.compile(r'^fc', re.I)
    total_ports = 0
    for line in port_brief_output:
        # Check if line starts with port name and collect fields
        if port_fc_regex.search(line):
            total_ports += 1           
    return total_ports


def main():
    # Get current date/time
    now = datetime.datetime.now().strftime('%Y-%m-%d')

    # Connect to PostgreSQL database
    try:
        con = psycopg2.connect(host='dbserver', database='dbname', user='dbuser', password='##############')
        cur = con.cursor()
    
    except psycopg2.DatabaseError as e:
        print(e)
        logging.error(e)
        sys.exit(1)

    logging.info("Starting collection of switch port usage data.")

    switches = {'mds1': '192.168.100.100',
                'mds2': '192.168.100.101'
                }

    for switch, switchip in sorted(switches.items()):
        port_detail_output = run_switch_cmd(switch, 'sh int')
        port_brief_output = run_switch_cmd(switch, 'sh int brief')

        if port_brief_output and port_detail_output:
            port_detail_output = filter(None, port_detail_output)
            port_brief_output = filter(None, port_brief_output)

            admin_down_ports = parse_port_detail_array(port_detail_output)
            total_ports = parse_port_brief_array(port_brief_output)

        if admin_down_ports and total_ports:
            # Database schema
            #            Table "public.san_port_usage"
            #    Column    |         Type          | Modifiers
            #    -------------+-----------------------+-----------
            #    switchname  | character varying(34) | not null
            #    used_ports  | integer               | not null
            #    total_ports | integer               | not null
            #    date        | date                  | not null
            #    Indexes:
            #        "san_port_usage_pkey" PRIMARY KEY, btree (switchname, date)
            #
            # Query db with "SELECT * FROM san_port_usage WHERE switchname = '$switchname' and date = '$date'"

            used_ports = total_ports - admin_down_ports
            percent_used = round((used_ports / total_ports) * 100)
            print(f'{switch}    Used: {used_ports}    Total: {total_ports}    Percent Used: {percent_used}')

            # Insert data into database
            try:
                cur.execute("INSERT INTO san_port_usage (switchname, used_ports, total_ports, date) VALUES (%s, %s, %s, %s)", (switch, used_ports, total_ports, now))
                con.commit()

            except psycopg2.DatabaseError as e:
                logging.info("Error with database insert.  Error: %s" % e)
                print(f'Error: {e}')
                sys.exit(1)            

    print()
    logging.info("Completed switch port usage data collection/update.")

    # Disconnect from san_db database
    if con:
        cur.close()
        con.close()


if __name__ == '__main__':
    main()
