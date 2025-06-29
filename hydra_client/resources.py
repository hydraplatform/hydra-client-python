# (c) Copyright 2013, 2014, University of Manchester
#
# HydraLib is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HydraPlatform is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with HydraPlatform.  If not, see <http://www.gnu.org/licenses/>
#
# -*- coding: utf-8 -*-

__all__ = ['HydraResource', 'HydraNetwork', 'HydraAttribute', 'temp_ids']

import logging
log = logging.getLogger(__name__)


class HydraResource(object):
    """A prototype for Hydra resources. It supports attributes and groups
    object types by template. This allows to export group nodes by object
    type based on the template used.
    """
    def __init__(self):
        self.name = None
        self.id = None
        self.attributes = []
        self.groups = []
        self.types = []

    def add_attribute(self, attr, res_attr, res_scen):
        attribute = HydraAttribute(attr, res_attr, res_scen)

        self.attributes.append(attribute)

    def delete_attribute(self, attribute):
        idx = self.attributes.index(attribute)
        del self.attributes[idx]

    def get_attribute(self, attr_name=None, attr_id=None):

        if attr_name is not None:
            return self._get_attr_by_name(attr_name)
        elif attr_id is not None:
            return self._get_attr_by_id(attr_id)

    def get_type_by_template(self, template_id):
        for ttype in self.types:
            if ttype.template_id == template_id:
                return ttype
        return None

    def get_type(self, id):
        for ttype in self.types:
            if ttype.id == id:
                return ttype
        return None

    def set_type(self, types):
        if isinstance(types, list):
            self.types.extend(types)
        else:
            self.types.append(types)

    def group(self, group_id):
        self.groups.append(group_id)
        #attr = self._get_attr_by_name(group_attr)
        #if attr is not None:
        #    group = attr.value.__getitem__(0)
        #    self.groups.append(group)
        #    # The attribute is used for grouping and will not be exported
        #    self.delete_attribute(attr)

    def _get_attr_by_name(self, attr_name):
        for attr in self.attributes:
            if attr.name.lower() == attr_name.lower():
                return attr

    def _get_attr_by_id(self, attr_id):
        for attr in self.attributes:
            if attr.attr_id == attr_id:
                return attr


class HydraNetwork(HydraResource):
    """
    """

    description = None
    scenario_id = None
    nodes = []
    links = []
    groups = []
    node_groups = []
    link_groups = []

    def load(self, json_net, json_attrs):

        # load network
        #build dictionary of resource scenarios:
        resource_scenarios = {
            res_scen.resource_attr_id: res_scen
            for res_scen in json_net.scenarios[0].resourcescenarios
        }

        attributes = {attr.id: attr for attr in json_attrs}
        self.name = json_net.name
        self.ID = json_net.id
        self.description = json_net.description
        self.scenario_id = json_net.scenarios[0].id
        self.set_type(json_net.types)

        if json_net.attributes is not None:
            for res_attr in json_net.attributes:
                if res_attr.attr_id not in attributes:
                    log.warning("Attribute %s not found in attributes",
                                res_attr)
                    continue
                self.add_attribute(attributes[res_attr.attr_id],
                                   res_attr,
                                   resource_scenarios.get(res_attr.id))

        # build dictionary of group members:
        if json_net.scenarios[0].resourcegroupitems is not None:
            groupitems = \
                json_net.scenarios[0].resourcegroupitems
        else:
            groupitems = []

        nodegroups = dict()
        linkgroups = dict()
        groupgroups = dict()
        log.info("Loading group items")
        for groupitem in groupitems:
            if groupitem.ref_key == 'NODE':
                if groupitem.node_id not in nodegroups:
                    nodegroups[groupitem.node_id] = [groupitem.group_id]
                else:
                    nodegroups[groupitem.node_id].append(groupitem.group_id)
            elif groupitem.ref_key == 'LINK':
                if groupitem.link_id not in linkgroups:
                    linkgroups[groupitem.link_id] = [groupitem.group_id]
                else:
                    linkgroups[groupitem.link_id].append(groupitem.group_id)
            elif groupitem.ref_key == 'GROUP':
                if groupitem.subgroup_id not in groupgroups:
                    groupgroups[groupitem.subgroup_id] = [groupitem.group_id]
                else:
                    groupgroups[groupitem.subgroup_id].append(groupitem.group_id)

        log.info("Loading groups")
        # load groups
        if json_net.resourcegroups is not None:
            for resgroup in json_net.resourcegroups:
                new_group = HydraResource()
                new_group.ID = resgroup.id
                new_group.name = resgroup.name
                if resgroup.attributes is not None:
                    for res_attr in resgroup.attributes:
                        new_group.add_attribute(attributes[res_attr.attr_id],
                            res_attr, resource_scenarios.get(res_attr.id))
                new_group.set_type(resgroup.types)
                if new_group.ID in groupgroups.keys():
                    new_group.groups = groupgroups[new_group.ID]
                self.add_group(new_group)
                del new_group
        log.info("Loading nodes")
        # load nodes
        for node in json_net.nodes:
            new_node = HydraResource()
            new_node.ID = node.id
            new_node.name = node.name
            new_node.X=node.x
            new_node.Y=node.y
            if node.attributes is not None:
                for res_attr in node.attributes:
                    new_node.add_attribute(attributes[res_attr.attr_id],
                                           res_attr,
                                           resource_scenarios.get(res_attr.id))

            new_node.set_type(node.types)
            if new_node.ID in nodegroups.keys():
                new_node.groups = nodegroups[new_node.ID]
            self.add_node(new_node)
            del new_node

        # load links
        log.info("Loading links")
        for link in json_net.links:
            new_link = HydraResource()
            new_link.ID = link.id
            new_link.name = link.name
            new_link.from_node = self.get_node(node_id=link.node_1_id).name
            new_link.to_node = self.get_node(node_id=link.node_2_id).name
            if link.attributes is not None:
                for res_attr in link.attributes:
                    new_link.add_attribute(attributes[res_attr.attr_id],
                                           res_attr,
                                           resource_scenarios.get(res_attr.id))
            new_link.set_type(link.types)
            if new_link.ID in linkgroups.keys():
                new_link.groups = linkgroups[new_link.ID]
            self.add_link(new_link)
            del new_link

    def add_node(self, node):
        self.nodes.append(node)

    def delete_node(self, node):
        pass

    def get_node(self, node_name=None, node_id=None, node_type_id=None,
                 group=None):
        if node_name is not None:
            return self._get_node_by_name(node_name)
        elif node_id is not None:
            return self._get_node_by_id(node_id)
        elif node_type_id is not None:
            return self._get_nodes_by_type(node_type_id)
        elif group is not None:
            return self._get_nodes_by_group(group)

    def add_link(self, link):
        self.links.append(link)

    def delete_link(self, link):
        pass

    def get_link(self, link_name=None, link_id=None, link_type_id=None,
                 group=None):
        if link_name is not None:
            return self._get_link_by_name(link_name)
        elif link_id is not None:
            return self._get_link_by_id(link_id)
        elif link_type_id is not None:
            return self._get_links_by_type(link_type_id)
        elif group is not None:
            return self._get_links_by_group(group)

    def add_group(self, group):
        self.groups.append(group)

    def delete_group(self, group):
        pass

    def get_group(self, **kwargs):
        if kwargs.get('group_name') is not None:
            return self._get_group_by_name(kwargs.get('group_name'))
        elif kwargs.get('group_id') is not None:
            return self._get_group_by_id(kwargs.get('group_id'))
        elif kwargs.get('group_type_id') is not None:
            return self._get_groups_by_type(kwargs.get('group_type_id'))
        elif kwargs.get('group') is not None:
            return self._get_groups_by_group(kwargs.get('group'))

    def get_node_types(self, template_id=None):
        node_types = []
        for node in self.nodes:
            for n_type in node.template[template_id]:
                if n_type not in node_types:
                    node_types.append(n_type)
        return node_types

    def get_link_types(self, template_id=None):
        link_types = []
        for link in self.links:
            for l_type in link.template[template_id]:
                if l_type not in link_types:
                    link_types.append(l_type)
        return link_types

    def _get_node_by_name(self, name):
        for node in self.nodes:
            if node.name == name:
                return node

    def _get_node_by_id(self, ID):
        for node in self.nodes:
            if node.ID == ID:
                return node

    def _get_nodes_by_type(self, node_type_id):
        nodes = []
        for node in self.nodes:
            for type in node.types:
                if node_type_id == type.id:
                    nodes.append(node)
        return nodes

    def _get_nodes_by_group(self, node_group):
        nodes = []
        for node in self.nodes:
            if node_group in node.groups:
                nodes.append(node)
        return nodes

    def _get_link_by_name(self, name):
        for link in self.links:
            if link.name == name:
                return link

    def _get_link_by_id(self, ID):
        for link in self.links:
            if link.ID == ID:
                return link

    def _get_links_by_type(self, link_type_id):
        links = []
        for link in self.links:
            for type in link.types:
                if type.id == link_type_id:
                    links.append(link)
        return links

    def _get_links_by_group(self, link_group):
        links = []
        for link in self.links:
            if link_group in link.groups:
                links.append(link)
        return links

    def _get_group_by_name(self, name):
        for group in self.groups:
            if group.name == name:
                return group

    def _get_group_by_id(self, ID):
        for group in self.groups:
            if group.ID == ID:
                return group

    def _get_groups_by_type(self, group_type_id):
        groups = []
        for group in self.groups:
            for type in group.types:
                if type.id == group_type_id:
                    groups.append(group)
        return groups

    def _get_groups_by_group(self, group_group):
        groups = []
        for group in self.groups:
            if group_group in group.groups:
                groups.append(group)
        return groups


class HydraAttribute(object):

    name = None

    attr_id = None
    resource_attr_id = None
    is_var = False

    dataset_id = None
    dataset_type = ''

    value = None

    def __init__(self, attr, res_attr, res_scen):
        self.name = attr.name
        self.attr_id = attr.id
        self.resource_attr_id = res_attr.id
        if res_attr.attr_is_var == 'Y':
            self.is_var = True
        if res_scen is not None:
            self.dataset_id = res_scen.dataset.id
            self.dataset_type = res_scen.dataset.type
            self.value = res_scen.dataset.value


def temp_ids(n=-1):
    """
    Create an iterator for temporary IDs for nodes, links and other entities
    that need them. You need to initialise the temporary id first and call the
    next element using the ``.next()`` function::

        temp_node_id = PluginLib.temp_ids()

        # Create a node
        # ...

        Node.id = temp_node_id.next()
    """
    while True:
        yield n
        n -= 1
