"""
    This example show how to create a network with nodes and links, but no data.
"""


# coding: utf-8

import hydra_client as hc
import datetime
import time

import argparse

import logging
log = logging.getLogger('scalabilitytester')


def make_network(conn, name, num_nodes=10, num_links=10):
    """
        Build a network with the specified number of nodes and links
    """
    
    #A user can have access to multiple projects of the same name, so get them
    #all, and use the first one.
    projects = conn.get_project_by_name({'project_name':'scalability_project'})
    if len(projects) == 0:
        new_project = {'name':'scalability_project'}
        new_project_j = conn.add_project({'project':new_project})
        project_id = new_project_j.id
    else:
        project_id = projects[0].id

    log.info("Using project with ID: %s", project_id)
        
    nodes = []
    links = []
    
    network = {
        'project_id' : project_id,
        'name' : 'name',
        'attributes' : []
    }
    for node_idx in range(1, num_nodes):
        nodes.append(
            {
                'id'         : node_idx * -1,
                'name'       :'node_%s'%(node_idx,),
                'attributes' : [],
                'x'          : 0,
                'y'          : 0,
            })

    link_offset = 1
    num_added_links = 0
    for node_idx in range(1, num_nodes):
        
        if num_added_links == num_links:
            break
            
        #If we've reached the end of the list of nodes, but still haven't 
        #made the required number of links, then reset the indices
        if node_idx == num_nodes or (node_idx + link_offset >= len(nodes)):
            if num_added_links < num_links:
                node_idx = 0
                link_offset = 2
            continue
        
        links.append(
            {
                'id'         : ( num_added_links + 1 ) * -1,
                'name'       :'node_%s_to_node_%s'%(node_idx, (node_idx+link_offset)),
                'attributes' : [],
                'node_1_id'  : nodes[node_idx]['id'],
                'node_2_id'  : nodes[node_idx+link_offset]['id'],
            })

        num_added_links = num_added_links + 1
        
    network['links'] = links
    network['nodes'] = nodes
    network['scenarios'] = []

    start_time = time.time()
    log.info('Calling add network')
    conn.call('add_network', {'net':network})
    
    end_time = time.time()-start_time
    
    return end_time
    
parser = argparse.ArgumentParser(description='Process some arguments.')
parser.add_argument('--name', type=str, 
                   help='the network name', default='Empty Network')
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
    make_network(conn, args.name)
