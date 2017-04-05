#!/usr/bin/python

from collections import defaultdict
import json

from ansible.module_utils.basic import AnsibleModule


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


def generate_inventory(nodes):
    """Generate ansible inventory from node list in json format

    Modified from https://github.com/martineg/ansible-fuel-inventory/blob/master/fuel.py

    :param nodes: output of fuel node --json
    :return inventory: ansible inventory in json

    >>> nodes = json.load(open('fuel-nodes-sample.json'))
    >>> dict(generate_inventory(nodes))
    {'node-24': [u'node-24'], 'cluster-4': [u'node-24'], u'controller': [u'node-24'], '_meta': {'hostvars': {u'node-24': {'status': u'ready', 'ip': u'10.20.11.11', 'ansible_ssh_host': u'10.20.11.11', 'cluster': 4, 'mac': u'74:4a:a4:01:73:50', 'online': True, 'os_platform': u'ubuntu'}}}, 'hw-zte-servers': [u'node-24'], u'mongo': [u'node-24']}
    """
    inventory = defaultdict(list)
    inventory['_meta'] = {
        'hostvars': {},
    }
    for node in nodes:
        # skip deleting, offline, deploying and discovering/unprovisioned nodes
        if node['pending_deletion'] or (not node['online']) \
                or node['status'] == 'deploying' or node['status'] == 'discover':
            continue

        hostname = node['hostname']
        cluster_id = node['cluster']
        hw_vendor = node['meta']['system']['manufacturer'].lower()
        [inventory[role.strip()].append(hostname) for role in node['roles'].split(",")]
        inventory["cluster-{0}".format(cluster_id)].append(hostname)
        inventory["hw-{0}-servers".format(hw_vendor)].append(hostname)
        node_meta = {
            'name': node['hostname'],
            'online': node['online'],
            'os_platform': node['os_platform'],
            'status': node['status'],
            'ip': node['ip'],
            'mac': node['mac'],
            'cluster': cluster_id,
            'ansible_ssh_host': node['ip']
        }
        inventory["node-{}".format(node['id'])].append(hostname)
        inventory['_meta']['hostvars'][hostname] = node_meta

    return inventory


def main():
    module = AnsibleModule(argument_spec=dict())

    cmd = [module.get_bin_path('fuel', True), 'node', '--json']
    (rc, out, err) = module.run_command(cmd)

    if rc is not None and rc != 0:
        return module.fail_json(msg=err)

    nodes = json.loads(out)

    module.exit_json(changed=False, ansible_facts=generate_inventory(nodes))

if __name__ == '__main__':
    main()
