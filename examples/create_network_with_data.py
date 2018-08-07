"""
    This example show how to create a network with nodes and links, but no data.
"""


# coding: utf-8

import hydra_client as hc
import datetime
import time

import argparse

from util import build_network


import logging
log = logging.getLogger(__name__)


parser = argparse.ArgumentParser(description='Process some arguments.')
parser.add_argument('--name', type=str, 
                   help='the network name', default='Network with data')
parser.add_argument('--url', type=str, 
                   help='the connection URL', default='http://127.0.0.1:8080/json')
parser.add_argument('--username', type=str, 
                   help='Username', default='root')
parser.add_argument('--password', type=str, 
                   help='Password', default='')

def run():

    args = parser.parse_args()

    log.info("Connecting to Hydra")
    conn = hc.RemoteJSONConnection(url=args.url)
    conn.login(username=args.username, password=args.password)

    network = build_network(conn, args.name)
    
    log.info("Adding network to Hydra")
    conn.add_network({'net':network})

if __name__ == '__main__':
    run()

