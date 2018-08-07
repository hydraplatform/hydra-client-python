

"""
    This example show how to create a network with nodes and links, but no data.
"""


# coding: utf-8

import hydra_client as hc
import datetime
import time

import util

import argparse

import logging
log = logging.getLogger(__name__)

def make_network(conn, network_name):
    
    project = util.create_project(conn, 'simple network container')

    #Create some attributes so we can get IDs to reference.
    inflow = util.create_attr(conn, "inflow", dimension='Volume')
    outflow = util.create_attr(conn, "outflow", dimension='Volume')
    losses = util.create_attr(conn, "losses", dimension='Volume')


    network = {
        'project_id': project.id,
        'name': network_name,
        'nodes': [
            {
                'name': 'Node 1',
                'id': -1,
                'x':0,
                'y':0,
                'attributes' : [
                    {'id':-1, 'attr_id': inflow.id}
                ]
            },
            {
                'name': 'Node 2',
                'id'  : -2,
                'x':1,
                'y':1,
                'attributes' : [
                    {'id':-2, 'attr_id': outflow.id, 'attr_is_var':'Y'}
                ]
            }

        ],
        'links': [
            {
                'name' : 'Link 1',
                'node_1_id' : -1,
                'node_2_id' : -2,
                'attributes' : [
                    {'id':-3, 'attr_id': losses.id}
                ]

            }
        ],

        'scenarios' : [
            {
                'name': 'Baseline',
                'resourcescenarios' : [
                    {
                        'resource_attr_id': -1,
                        'dataset': {
                            'name': 'simple inflow',
                            'type' : 'scalar',
                            'value': '10',
                            'unit' : 'm^3',
                        }

                    },
                    {
                        'resource_attr_id': -3,
                        'dataset': {
                            'name': 'simple loss',
                            'type' : 'scalar',
                            'value': '1',
                            'unit' : 'm^3',
                        }

                    }
                ]
            }
        ]
    }
    return network

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--name', type=str, 
                   help='the network name', default='Simple Network')
parser.add_argument('--url', type=str, 
                   help='the connection URL', default='http://127.0.0.1:8080/json')
parser.add_argument('--username', type=str, 
                   help='Username', default='root')
parser.add_argument('--password', type=str, 
                   help='Password', default='')

if __name__ == '__main__':

    args = parser.parse_args()

    conn = hc.RemoteJSONConnection(url=args.url)
    conn.login(username=args.username, password=args.password)
    network = make_network(conn, args.name)
    conn.add_network({'net':network})
