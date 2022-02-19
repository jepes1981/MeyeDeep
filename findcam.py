#!/usr/bin/env python

import nmap
nm = nmap.PortScanner()
print('running nmap....')
nm.scan('192.168.1.0/24', '554')
if not len(nm.all_hosts())>0:
    print('no hosts found....')
    exit(1)
for hosts in nm.all_hosts():
    if nm[hosts]['tcp'][554]['product'] == 'DoorBird video doorbell rtspd':
        print(nm[hosts]['tcp'][554]['product'])

