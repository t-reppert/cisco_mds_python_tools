#!/usr/bin/python3
#
#  Title:  san_switch_port_desc_validator.py
#  Author:  T. Reppert
#  Description:
#    This script scans every switch in the switch list in the main() section for port description and flogi'd device-alias or wwn on that port
#
#    If the description and the device-alias flogi'd match, the port is not printed.
#
#    This does not include blade chassis ISL ports or ISL's between 9710's or any ports labeled with the word: "decom"
#    This script assumes that SSH keys were configured on all involved switches for the user executing this script
#
#  Original creation date:  2/22/17

import re
import subprocess

def build_port_dict(switch):
    # Parse list of port descriptions defined on switch
    port_dict = {}
    output = subprocess.Popen(
        ['/usr/bin/ssh', '-q', '-o UserKnownHostsFile=/dev/null', '-o StrictHostKeyChecking=no', '-o ConnectTimeout=10',
         switch, "sh int desc"], stdout=subprocess.PIPE).communicate()[0]
    desc_regex = re.compile(r'^(fc[1-9][0-5]*/[1-9][0-9]*)\s+(.*)',re.M)
    desc_data = output.splitlines()
    for line in desc_data:
        desc_match = desc_regex.search(line)
        if desc_match:
            port_dict[(desc_match.group(1))] = desc_match.group(2).strip()

    return port_dict

def build_status_dict(switch):
    # Parse list of port brief defined on switch
    port_status_dict = {}
    output = subprocess.Popen(
        ['/usr/bin/ssh', '-q', '-o UserKnownHostsFile=/dev/null', '-o StrictHostKeyChecking=no', '-o ConnectTimeout=10',
         switch, "sh int"], stdout=subprocess.PIPE).communicate()[0]
    status_regex = re.compile(r'^(fc[1-9][0-5]*/[1-9][0-9]*)\s+([ a-zA-Z\(\)\-]+).*',re.M)
    status_data = output.splitlines()

    for line in status_data:
        status_match = status_regex.search(line)
        if status_match:
            port_status_dict[(status_match.group(1))] = status_match.group(2).strip()

    return port_status_dict

def build_devalias_dict(switch):
    # Parse list of device aliases defined on switch
    output = subprocess.Popen(
        ['/usr/bin/ssh', '-q', '-o UserKnownHostsFile=/dev/null', '-o StrictHostKeyChecking=no', '-o ConnectTimeout=10',
         switch, "sh device-alias database"], stdout=subprocess.PIPE).communicate()[0]
    deval_info = {}
    deval_regex = re.compile('^device-alias name (.*) pwwn (.*)$',re.M)
    deval_data = output.split('\n')
    for line in deval_data:
        deval_match = deval_regex.search(line)
        if deval_match:
            deval_info[(deval_match.group(2))] = deval_match.group(1).strip()

    return deval_info

def build_flogi_dict(switch):
    # Parse flogi database for device aliases logged in on port
    output = subprocess.Popen(
        ['/usr/bin/ssh', '-q', '-o UserKnownHostsFile=/dev/null', '-o StrictHostKeyChecking=no', '-o ConnectTimeout=10',
         switch, "sh flogi database"], stdout=subprocess.PIPE).communicate()[0]
    
    flogi_out_regex = re.compile(r'^(fc[\s\S]*?)(port|Total)',re.M)
    fc_only_flogi = flogi_out_regex.search(output)
    fc_only_string = fc_only_flogi.group(1)
    fc_line_check = re.compile(r'^(fc[1-9][0-5]*\/[1-9][0-9]*)\s+.*')
    devalias_line_check = re.compile(r'\[(.*)\]')
    wwn_regex = re.compile(r'^(fc[1-9][0-5]*\/[1-9][0-9]*)\s+([0-9]*[0-9]*)\s+([\w\d]+)\s+([\w\d:]+)\s+([\w\d:]+)')
    fc_section = fc_only_string.split('\n')
    flogi_info = {}
    last_port_name = ''
    port_name = ''
    for line in fc_section:
        line = line.strip()
        port_check = fc_line_check.match(line)
        devalias_check = devalias_line_check.search(line)
        wwn_check = wwn_regex.search(line)
        if port_check:
            port_name = port_check.group(1)
            if port_name == last_port_name:
                flogi_info[port_name] = "trunk"
                continue
            if wwn_check:
                flogi_info[port_name] = wwn_check.group(4)
        elif devalias_check:
            if flogi_info.get(port_name) != "trunk":
                flogi_info[port_name] = devalias_check.group(1)

        last_port_name = port_name
    return flogi_info

def main():
    # switches is a list of the switch names that can be ssh'd into using that name 
    # from the server where this script is executed
    switches = ['mds1','mds2','mds3','mds4']
    port_desc = {}
    flogi_info = {}
    devalias_info = {}
    port_state = {}
    flogi_data = {}
    # Build port description, flogi info, devalias info, and port state dictonaries
    for switch in switches:
        port_desc[switch] = build_port_dict(switch)
        flogi_info[switch] = build_flogi_dict(switch)
        devalias_info[switch] = build_devalias_dict(switch)
        port_state[switch] = build_status_dict(switch)

    decom_line_check = re.compile(r'decom',re.I)
    
    # Generate report of switch port descriptions and the devalias flogi'd on that port 
    print("%18s%10s%40s%40s%40s%20s" % ("Switch","Port","Description","Status","FLOGI","Match?"))
    for switch in switches:
        flogi_data = flogi_info[switch]
        state_data = port_state[switch]
        match_chk = ''
        
        for port, desc in sorted(port_desc[switch].items()):
            match_chk = "NO"
            if desc == flogi_data.get(port):
                match_chk = "YES"
            if flogi_data.get(port) == "trunk" or 'ISL' in desc or '_EXT' in desc or '_X' in desc:
                match_chk = "ISL"
            if desc == '--':
                match_chk = "--"
            if decom_line_check.search(desc):
                match_chk = "decom"
            if match_chk != "ISL" and match_chk != "--" and "trunking" not in state_data.get(port) and match_chk != "YES" and match_chk != "decom" and "Administratively down" not in state_data.get(port):
                print("%18s%10s%40s%40s%40s%20s" % (switch, port, desc, state_data.get(port), flogi_data.get(port), match_chk))
        print()
            

if __name__ == '__main__':
    main()


