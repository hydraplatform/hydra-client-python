from hydra_base import JSONObject, Dataset
import json
import datetime
import logging
log = logging.getLogger(__name__)

def build_network(conn, name=None, project_id=None, num_nodes=10):
    
    """
        Create a network with the correct 
    """

    #Does nothing if project id is None, just returns the project id, otherwise
    #finds or creates the project 

    project_id = get_project(conn, project_id)

    template = create_template(conn)

    network_type  = template.templatetypes[0]
    node_type     = template.templatetypes[1] #For the purposes of this example, there is only 1 type of node. The 'default node'
    link_type     = template.templatetypes[2] #For the purposes of this example, there is only 1 type of link. The 'default link'
    group_type    = template.templatetypes[3]
     
    nodes, links = create_nodes_and_links(node_type, link_type, num_nodes=num_nodes)
    
    groups, group_items = create_groups(nodes, links, group_type)

    #way so I can check the value is correct after the network is created.
    layout = dict(
        color = 'red',
        shapefile = 'blah.shp'
    )

    network_attributes = create_network_attributes(conn, network_type)

    net_type= []
    net_type = JSONObject(dict(
        template_id = template.id,
        template_name = template.name,
        id = network_type.id,
        name = network_type.name,
    ))
    
    #The the contents of a group are scenario-dependent
    scenario = create_scenario(nodes, links, groups, group_items, node_type, link_type)

    network = JSONObject(dict(
        name        = 'Network @ %s'%datetime.datetime.now(),
        description = 'An example network',
        project_id  = project_id,
        links       = links,
        nodes       = nodes,
        layout      = layout,
        scenarios   = [scenario], #a list as a network can contain multipl scenarios
        resourcegroups = groups,
        projection  = 'EPSG:4326',
        attributes  = network_attributes,
        types       = [net_type],#a list as a network can have multiple types
    ))

    return network

def create_scenario(nodes, links, groups, resourcegroupitems, node_type, link_type):
    
    log.info('Creating Scenario')

    #Create the scenario
    scenario = JSONObject()
    scenario.id = -1
    scenario.name        = 'Scenario 1'
    scenario.description = 'Scenario Description'
    scenario.layout      = json.dumps({'app': ["Unit Test1", "Unit Test2"]})

    scenario.resourcegroupitems = resourcegroupitems 

    node_data, link_data, group_data = populate_network_with_data(nodes, links, groups, node_type, link_type)

    #Set the scenario's data to the array we have just populated
    scenario.resourcescenarios = node_data + link_data + group_data

    return scenario

def create_attr(conn, name="Test attribute", dimension="dimensionless"):
    attr_i = conn.get_attribute({'name':name, 'dimension':dimension})
    if attr_i is None or len(attr_i) == 0:
        attr = JSONObject({'name'  : name,
                'dimension' : dimension
               })
        attr = JSONObject(conn.add_attribute({'attr':attr}))
    else:
        attr = JSONObject(attr_i)
    return attr

def create_template(conn, name="Example Template"):
    
    log.info('Creating Template')


    existing_template = conn.get_template_by_name({'template_name':name})

    if len(existing_template) > 0:
        log.info("Existing template found. Continuing")
        return JSONObject(existing_template)
    else:
        log.info("No existing template found. Making new one.")


    net_attr1    = create_attr(conn, "net_attr_a", dimension='Volume')
    net_attr2    = create_attr(conn, "net_attr_c", dimension='dimensionless')
    link_attr_1  = create_attr(conn, "link_attr_a", dimension='Pressure')
    link_attr_2  = create_attr(conn, "link_attr_b", dimension='Speed')
    link_attr_3  = create_attr(conn, "link_attr_c", dimension='Length')
    node_attr_1  = create_attr(conn, "node_attr_a", dimension='Volume')
    node_attr_2  = create_attr(conn, "node_attr_b", dimension='Speed')
    node_attr_3  = create_attr(conn, "node_attr_c", dimension='Monetary value')
    node_attr_4  = create_attr(conn, "node_attr_d", dimension='Volumetric flow rate')
    group_attr_1 = create_attr(conn, "grp_attr_1", dimension='Monetary Value')
    group_attr_2 = create_attr(conn, "grp_attr_2", dimension='Displacement')

    template = JSONObject()
    template['name'] = name


    types = []
    #**********************
    #network type         #
    #**********************
    net_type = JSONObject()
    net_type.name = "Default Network"
    net_type.alias = "Test type alias"
    net_type.resource_type='NETWORK'

    typeattrs = []

    typeattr_1 = JSONObject()
    typeattr_1.attr_id = net_attr1.id
    typeattr_1.data_restriction = {'LESSTHAN': 10, 'NUMPLACES': 1}
    typeattr_1.unit = 'm^3'
    typeattrs.append(typeattr_1)

    typeattr_2 = JSONObject()
    typeattr_2.attr_id = net_attr2.id
    typeattrs.append(typeattr_2)

    net_type.typeattrs = typeattrs

    types.append(net_type)
    #**********************
    # node type           #
    #**********************
    node_type = JSONObject()
    node_type.name = "Default Node"
    node_type.alias = "Test type alias"
    node_type.resource_type='NODE'

    typeattrs = []

    typeattr_1 = JSONObject()
    typeattr_1.attr_id = node_attr_1.id
    typeattr_1.data_restriction = {'LESSTHAN': 10, 'NUMPLACES': 1}
    typeattr_1.unit = 'm^3'
    typeattrs.append(typeattr_1)

    typeattr_2 = JSONObject()
    typeattr_2.attr_id = node_attr_2.id
    typeattr_2.data_restriction = {'INCREASING': None}
    typeattrs.append(typeattr_2)

    typeattr_3 = JSONObject()
    typeattr_3.attr_id = node_attr_3.id
    typeattrs.append(typeattr_3)

    typeattr_4 = JSONObject()
    typeattr_4.attr_id = node_attr_4.id
    typeattr_4.unit = "m^3 s^-1"
    typeattrs.append(typeattr_4)

    node_type.typeattrs = typeattrs

    types.append(node_type)
    #**********************
    #link type            #
    #**********************
    link_type = JSONObject()
    link_type.name = "Default Link"
    link_type.resource_type='LINK'

    typeattrs = []

    typeattr_1 = JSONObject()
    typeattr_1.attr_id = link_attr_1.id
    typeattrs.append(typeattr_1)

    typeattr_2 = JSONObject()
    typeattr_2.attr_id = link_attr_2.id
    typeattrs.append(typeattr_2)

    typeattr_3 = JSONObject()
    typeattr_3.attr_id = link_attr_3.id
    typeattrs.append(typeattr_3)

    link_type.typeattrs = typeattrs

    types.append(link_type)

    #**********************
    #group type           #
    #**********************
    group_type = JSONObject()
    group_type.name = "Default Group"
    group_type.resource_type='GROUP'

    typeattrs = []

    typeattr_1 = JSONObject()
    typeattr_1.attr_id = group_attr_1.id
    typeattrs.append(typeattr_1)

    typeattr_2 = JSONObject()
    typeattr_2.attr_id = group_attr_2.id
    typeattrs.append(typeattr_2)

    group_type.typeattrs = typeattrs

    types.append(group_type)

    template.templatetypes = types

    new_template_i = conn.add_template({'tmpl':template})
    new_template   = JSONObject(new_template_i)

    assert new_template.name == template.name, "Names are not the same!"
    assert new_template.id is not None, "New Template has no ID!"
    assert new_template.id > 0, "New Template has incorrect ID!"

    assert len(new_template.templatetypes) == len(types), "Resource types did not add correctly"
    for t in new_template.templatetypes[1].typeattrs:
        assert t.attr_id in (node_attr_1.id, node_attr_2.id, node_attr_3.id, node_attr_4.id);
        "Node types were not added correctly!"

    for t in new_template.templatetypes[2].typeattrs:
        assert t.attr_id in (link_attr_1.id, link_attr_2.id, link_attr_3.id);
        "Link types were not added correctly!"

    return new_template

def create_node(node_id, attributes=None, node_name="test node name"):

    if attributes is None:
        attributes = []
    #turn 0 into 1, -1 into 2, -2 into 3 etc..
    coord = (node_id * -1) + 1
    node = JSONObject({
        'id' : node_id,
        'name' : node_name,
        'description' : "a node representing a water resource",
        'layout'      : None,
        'x' : 10 * coord,
        'y' : 10 * coord -1,
        'attributes' : attributes,
    })

    return node


def create_link(link_id, node_1_name, node_2_name, node_1_id, node_2_id):

    ra_array = []

    link = JSONObject({
        'id'          : link_id,
        'name'        : "%s_to_%s"%(node_1_name, node_2_name),
        'description' : 'A test link between two nodes.',
        'layout'      : None,
        'node_1_id'   : node_1_id,
        'node_2_id'   : node_2_id,
        'attributes'  : ra_array,
    })

    return link

def create_nodes_and_links(node_type, link_type, num_nodes=10):


    log.info('Creating Nodes and Links')

    #keeps track of the last node looked at, as the first node can't be linked
    #to anything
    prev_node = None

    #resource attribute index. Used to assign IDs to nodes
    ra_index = 2

    nodes = []
    links = []
    
    for n in range(num_nodes):
        node = create_node(n*-1, node_name="Node %s"%(n))

        #From our attributes, create a resource attr for our node
        #We don't assign data directly to these resource attributes. This
        #is done when creating the scenario -- a scenario is just a set of
        #data for a given list of resource attributes.
        node_ra1         = JSONObject(dict(
            ref_key = 'NODE',
            ref_id  = None,
            attr_id = node_type.typeattrs[0].attr_id,
            id      = ra_index * -1,
            attr_is_var = 'N',
        ))
        ra_index = ra_index + 1
        node_ra2         = JSONObject(dict(
            ref_key = 'NODE',
            ref_id  = None,
            attr_id = node_type.typeattrs[1].attr_id,
            id      = ra_index * -1,
            attr_is_var = 'Y', #Note that this is a 'var' meanint it's an OUTPUT, so is not assigned a value here
        )) 
        ra_index = ra_index + 1
        node_ra3         = JSONObject(dict(
            ref_key = 'NODE',
            ref_id  = None,
            attr_id = node_type.typeattrs[2].attr_id,
            id      = ra_index * -1,
            attr_is_var = 'N',
        ))
        ra_index = ra_index + 1
        node_ra4         = JSONObject(dict(
            ref_key = 'NODE',
            ref_id  = None,
            attr_id = node_type.typeattrs[3].attr_id,
            id      = ra_index * -1,
            attr_is_var = 'N',
        ))
        ra_index = ra_index + 1

        node.attributes = [node_ra1, node_ra2, node_ra3, node_ra4]

        type_summary = JSONObject(dict(
            id = node_type.id,
            name = node_type.name
        ))

        type_summary_arr = [type_summary]

        node.types = type_summary_arr

        nodes.append(node)

        if prev_node is not None:
            #Connect the two nodes with a link
            link = create_link(
                n*-1,
                node['name'],
                prev_node['name'],
                node['id'],
                prev_node['id'])

            link_ra1         = JSONObject(dict(
                ref_id  = None,
                ref_key = 'LINK',
                id     = ra_index * -1,
                attr_id = link_type.typeattrs[0].attr_id,
                attr_is_var = 'N',
            ))
            ra_index = ra_index + 1
            link_ra2         = JSONObject(dict(
                ref_id  = None,
                ref_key = 'LINK',
                attr_id = link_type.typeattrs[1].attr_id,
                id      = ra_index * -1,
                attr_is_var = 'N',
            ))
            ra_index = ra_index + 1
            link_ra3         = JSONObject(dict(
                ref_id  = None,
                ref_key = 'LINK',
                attr_id = link_type.typeattrs[2].attr_id,
                id      = ra_index * -1,
                attr_is_var = 'N',
            ))
            ra_index = ra_index + 1

            link.attributes = [link_ra1, link_ra2, link_ra3]
            if link['id'] % 2 == 0:
                type_summary_arr = []
                type_summary = JSONObject(
                    {'id': link_type.id,
                     'name':link_type.name
                    }
                )
                type_summary_arr.append(type_summary)

                link.types = type_summary_arr
            links.append(link)

        prev_node = node

    return nodes, links

def create_groups(nodes, links, group_type):

    """
        Create resource groups and their items
        A resource group is a container for nodes and links, used to represent
        political or social hierarchies, or logical groupings of nodes where a
        rule must be applied to them
        
        The contents of a group are scenario dependent, so the group configuration
        can be changed within a network.
    """
    log.info('Creating Groups')

    # Put an attribute on a group
    group_ra = JSONObject(dict(
        ref_id  = None,
        ref_key = 'GROUP',
        attr_is_var = 'N',
        attr_id = group_type.typeattrs[0].attr_id,
        id      = -1
    ))
    group_attrs = [group_ra]

    groups       = []
    group             = JSONObject(dict(
        id          = -1,
        name        = "Test Group",
        description = "Test group description"
    ))

    group.attributes = group_attrs

    type_summary = JSONObject(dict(
        id = group_type.id,
        name = group_type.name
    ))

    type_summary_arr = [type_summary]

    group.types = type_summary_arr
    
    groups.append(group)

    group_items      = []
    group_item_1 = JSONObject(dict(
        ref_key  = 'NODE',
        ref_id   = nodes[0]['id'],
        group_id = group['id'],
    ))
    group_item_2  = JSONObject(dict(
        ref_key  = 'NODE',
        ref_id   = nodes[1]['id'],
        group_id = group['id'],
    ))

    group_items = [group_item_1, group_item_2]

    return groups, group_items

def populate_network_with_data(nodes, links, groups, node_type, link_type):
    
    """
        Crate datasets and associate them with the nodes, links and groups in the network.
        The datasets created are scalars, timeseries and dataframes.
    """

    node_data = []
    link_data = []
    group_data = []
    for n in nodes:
        for na in n.attributes:
            if na.get('attr_is_var', 'N') == 'N':
                if na['attr_id'] == node_type.typeattrs[0].attr_id:
                    dataset = create_timeseries(na)
                elif na['attr_id'] == node_type.typeattrs[2].attr_id:
                    dataset = create_scalar(na)
                elif na['attr_id'] == node_type.typeattrs[3].attr_id:
                    dataset = create_dataframe(na)
                else:
                    continue

                node_data.append(dataset)
    for l in links:
        for na in l.attributes:
            if na['attr_id'] == link_type.typeattrs[0].attr_id:
                dataset      = create_array(na)
            elif na['attr_id'] == link_type.typeattrs[1].attr_id:
                dataset = create_descriptor(na)
            else:
                continue

            link_data.append(dataset)

    grp_timeseries = create_timeseries(groups[0].attributes[0])
    group_data = [grp_timeseries]

    return node_data, link_data, group_data

def create_project(conn, name):

    user_projects = conn.get_project_by_name({'project_name':name})

    if len(user_projects) == 0:
        log.info('Project "%s" not found, creating a new one', name)
        project = JSONObject()
        project.name = name
        project.description = "Project which contains all example networks"
        project = JSONObject(conn.add_project({'project':project}))

        return project
    else:
        return user_projects[0]

def get_project(conn, project_id, project_name=None):
    """
        Create a new project with the specified name, or return a project ID
        of a project with this name.
    """

    log.info('Getting Project')

    if project_id is None:
        proj_name = project_name if project_name else "Example Project"
        project_id = create_project(conn, name=proj_name).id
    else:
        project_id = project_id

    return project_id

def create_network_attributes(conn, network_type):
    log.info('Creating Network Attributes')

    net_attr = create_attr(conn, "net_attr_b", dimension='Pressure')

    net_ra_notmpl = JSONObject(dict(
        ref_id  = None,
        ref_key = 'NETWORK',
        attr_is_var = 'N',
        attr_id = net_attr.id,
    ))
    net_ra_tmpl = JSONObject(dict(
        ref_id  = None,
        ref_key = 'NETWORK',
        attr_is_var = 'N',
        attr_id = network_type.typeattrs[0].attr_id,
    ))
    
    return [net_ra_notmpl, net_ra_tmpl]

def create_scalar(resource_attr, val=1.234):
    #with a resource attribute.

    dataset = dict(
        id=None,
        type = 'scalar',
        name = 'Flow speed',
        unit = 'm s^-1',
        hidden = 'N',
        value = val,
    )

    scenario_attr = JSONObject(dict(
        attr_id = resource_attr.attr_id,
        resource_attr_id = resource_attr.id,
        dataset = dataset,
    ))

    return scenario_attr

def create_descriptor(resource_attr, val="test"):
    #A scenario attribute is a piece of data associated
    #with a resource attribute.

    dataset = dict(
        id=None,
        type = 'descriptor',
        name = 'Flow speed',
        unit = 'm s^-1', # This does not match the type on purpose, to test validation
        hidden = 'N',
        value = val,
    )

    scenario_attr = JSONObject(dict(
        attr_id = resource_attr.attr_id,
        resource_attr_id = resource_attr.id,
        dataset = dataset,
    ))

    return scenario_attr


def create_timeseries(resource_attr):
    #A scenario attribute is a piece of data associated
    #with a resource attribute.
    #[[[1, 2, "hello"], [5, 4, 6]], [[10, 20, 30], [40, 50, 60]]]

    fmt = "%Y-%m-%dT%H:%M:%S.%f000Z"

    t1 = datetime.datetime.now()
    t2 = t1+datetime.timedelta(hours=1)
    t3 = t1+datetime.timedelta(hours=2)

    val_1 = [10, 20, 30]
    val_2 = [1.0, 2.0, 3.0]

    val_3 = [3.0, 4.0, 5.0]

    ts_val = {"test_column": {t1.strftime(fmt): val_1,
                  t2.strftime(fmt): val_2,
                  t3.strftime(fmt): val_3}}

    metadata = json.dumps({'created_by': 'Test user'})

    dataset = dict(
        id=None,
        type = 'timeseries',
        name = 'my time series',
        unit = 'cm^3', # This does not match the type on purpose, to test validation
        hidden = 'N',
        value = json.dumps(ts_val),
        metadata = metadata
    )

    scenario_attr = JSONObject(dict(
        attr_id = resource_attr.attr_id,
        resource_attr_id = resource_attr.id,
        dataset = dataset,
    ))

    return scenario_attr

def create_dataframe(resource_attr):
    #A scenario attribute is a piece of data associated
    #with a resource attribute.

    val_1 = "df_a"
    val_2 = "df_b"
    val_3 = "df_c"

    ts_val = {"test_column":
                {
                  'key1': val_1,
                  'key2': val_2,
                  'key3': val_3
                }
            }

    metadata = json.dumps({'created_by': 'Test user'})

    dataset = dict(
        id=None,
        type = 'dataframe',
        name = 'my data frame',
        unit = 'm^3 s^-1',
        hidden = 'N',
        value = json.dumps(ts_val),
    )

    scenario_attr = JSONObject(dict(
        attr_id = resource_attr.attr_id,
        resource_attr_id = resource_attr.id,
        dataset = dataset,
    ))

    return scenario_attr

def create_array(resource_attr):
    #A scenario attribute is a piece of data associated
    #with a resource attribute.
    #[[1, 2, 3], [4, 5, 6], [7, 8, 9]]

    arr = json.dumps([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])

    metadata_array = json.dumps({'created_by': 'Test user'})

    dataset = dict(
        id=None,
        type = 'array',
        name = 'my array',
        unit = 'bar',
        hidden = 'N',
        value = arr,
        metadata = metadata_array,
    )

    scenario_attr = JSONObject(dict(
        attr_id = resource_attr.attr_id,
        resource_attr_id = resource_attr.id,
        dataset = dataset,
    ))

    return scenario_attr

