#!/usr/bin/env python
"""
Copies an API hierarchy for a Customer to the depth of Devices.  Includes Manufacturer/Products.

Usage:
    python copy_structure.py -c 095c5c4f-be42-4c5a-98da-20c6e4509799 -o qa1 -u ramon@gooee.com
        -p foo -d localhost -U ramon@gooee.com -P bar
"""
import pprint
from argparse import ArgumentParser
from copy import deepcopy

from gooee import GooeeClient

COPY_STRUCTURE = True

# Fields entirely omitted.
IGNORED_MANUFACTURER_FIELDS = ('devices_total', 'logo', 'css', 'tags', 'users', 'modified',
                               'created', 'favicon')
IGNORED_PRODUCT_FIELDS = ('created', 'modified', 'image', 'tags', 'owner', 'manufacturer_name',
                          'manufacturer_logo', 'activated_date')
IGNORED_CUSTOMER_FIELDS = ('created', 'logo', 'modified', 'tags')
IGNORED_BUILDING_FIELDS = ('modified', 'tags', 'users', 'last_activity', 'created')
IGNORED_SPACE_FIELDS = ('bg_image', 'created', 'last_activity', 'modified', 'service_profile',
                        'tags')
IGNORED_DEVICE_FIELDS = ('created', 'commissioned_date', 'commission_state', 'modified',
                         'custom_fields', 'service_profile', 'tags')

# Fields omitted during initial creation.
MANUFACTURER_PKS = ('customers', 'products')
PRODUCT_PKS = ('manufacturer',)
CUSTOMER_PKS = ('partner', 'buildings')
BUILDING_PKS = ('customer', 'spaces')
SPACE_PKS = ('scenes', 'connected_products', 'building', 'parent_space', 'devices', 'child_spaces')
DEVICE_PKS = ('building', 'connected_products', 'spaces', 'parent_device', 'child_devices')

ids = {
    'partners': {},
    'customers': {},
    'products': {},
    'buildings': {},
    'spaces': {},
    'devices': {},
}


def copy_building_devices(building):
    """Copies the Devices of a Building."""
    response = o_client.get('/devices?building={}'.format(building['id']))
    if response.status_code != 200:
        raise Exception('[{}]: {}'.format(response.status_code, response.json))
    print('[origin] Found {} Devices for Building: {} ({})'
          .format(len(response.json), building['name'], building['id']))

    devices = []
    for device in response.json:
        # Remove ignored fields
        for key in IGNORED_DEVICE_FIELDS:
            device.pop(key)

        if not options['structure_only']:
            # Remove old UUIDs
            temp_device = deepcopy(device)
            for key in DEVICE_PKS:
                temp_device.pop(key)

            # Apply new UUIDs
            temp_device['product'] = ids['products'][device['product']]
            temp_device['building'] = ids['buildings'][device['building']]

            # Update/Create Device and store the UUID
            meta = temp_device.pop('meta', [])
            new_obj = upsert_object('Building Device', temp_device, '/devices')
            ids['devices'][device['id']] = new_obj['id']

            # Upload Device Meta separately
            if meta:
                response = d_client.post('/devices/{}/meta'.format(new_obj['id']), data=meta)
                if response.status_code != 201:
                    raise Exception('[{}]: {}'.format(response.status_code, response.json))
                print('[destination] Updated Device Meta for {}'.format(new_obj['name']))

        # Only display the Device without Spaces
        if not device['spaces']:
            devices.append(device)

    return devices


def copy_building_spaces(building):
    """Copies the Spaces of a Building."""
    response = o_client.get('/spaces?building={}'.format(building['id']))
    print('[origin] Found {} Spaces for Building: {} ({})'
          .format(len(response.json), building['name'], building['id']))

    spaces = []
    for space in response.json:
        # Remove ignored fields
        for key in IGNORED_SPACE_FIELDS:
            space.pop(key)

        if not options['structure_only']:
            # Remove old UUIDs
            temp_space = deepcopy(space)
            for key in SPACE_PKS:
                temp_space.pop(key)

            # Apply new UUIDs
            temp_space['building'] = ids['buildings'][space['building']]

            # Update/Create Space and store the UUID
            meta = temp_space.pop('meta', [])
            new_obj = upsert_object('Building Space', temp_space, '/spaces')
            ids['spaces'][space['id']] = new_obj['id']

            # Upload Space Meta separately
            if meta:
                response = d_client.post('/spaces/{}/meta'.format(new_obj['id']), data=meta)
                if response.status_code != 201:
                    raise Exception('[{}]: {}'.format(response.status_code, response.json))
                print('[destination] Updated Space Meta for {}'.format(new_obj['name']))

        space['child_spaces'] = relate_spaces(space) if space['child_spaces'] else []
        space['devices'] = relate_devices(space)

        # Hide Building Devices that will be displayed on Spaces.
        if not space['parent_space']:
            space.pop('parent_space')
            spaces.append(space)

    return spaces


def copy_customer(customer_id):
    """Copies the Customer."""
    # Fetch Customer
    response = o_client.get('/customers/{}'.format(customer_id))
    if response.status_code != 200:
        raise Exception('[origin]: Cannot locate Customer')
    customer = response.json

    # Remove ignored fields
    for key in IGNORED_CUSTOMER_FIELDS:
        customer.pop(key)

    if not options['structure_only']:
        # Remove old UUIDs
        temp_customer = deepcopy(customer)
        for key in CUSTOMER_PKS:
            temp_customer.pop(key)

        # Apply new UUIDs
        temp_customer['partner'] = ids['partners'][customer['partner']]

        # Update/Create Customer and store the UUID
        new_obj = upsert_object('Customer', temp_customer, '/customers')
        ids['customers'][customer['id']] = new_obj['id']

    customer['buildings'] = copy_customer_buildings(customer)

    return [customer]


def copy_customer_buildings(customer):
    """Copies the Buildings of the Customer."""
    response = o_client.get('/buildings?customer={}'.format(customer['id']))
    print('[origin] Found {} Buildings for Customer: {} ({})'
          .format(len(response.json), customer['name'], customer['id']))

    new_buildings = []
    for building in response.json:
        # Remove ignored fields
        for key in IGNORED_BUILDING_FIELDS:
            building.pop(key)

        if not options['structure_only']:
            # Remove old UUIDs
            temp_building = deepcopy(building)
            for key in BUILDING_PKS:
                temp_building.pop(key)

            # Apply new UUIDs
            temp_building['customer'] = ids['customers'][building['customer']]

            # Update/Create Building and store the UUID
            meta = temp_building.pop('meta', [])
            new_obj = upsert_object('Building', temp_building, '/buildings')
            ids['buildings'][building['id']] = new_obj['id']

            # Upload Building Meta separately
            if meta:
                response = d_client.post('/buildings/{}/meta'.format(new_obj['id']), data=meta)
                if response.status_code != 201:
                    raise Exception('[{}]: {}'.format(response.status_code, response.json))
                print('[destination] Updated Building Meta for {}'.format(new_obj['name']))

        building['devices'] = copy_building_devices(building)
        building['spaces'] = copy_building_spaces(building)
        new_buildings.append(building)

    return new_buildings


def copy_manufacturer(customer_id):
    """Copies the Manufacturer of the Customer and related objects down to Device."""
    # Identify Customer
    response = o_client.get('/customers/{}'.format(customer_id))
    if response.status_code != 200:
        raise Exception('[origin]: Cannot locate Customer')
    customer_id, customer_name = response.json['id'], response.json['name']
    print('[origin] Found Customer: {}'.format(customer_name))

    # Identify Partner/Manufacturer of Customer
    print('[origin] Locating Manufacturer for Customer: {}'.format(customer_name))
    response = o_client.get('/partners?customers__id={}'.format(customer_id))
    if len(response.json) == 1:
        manufacturer = response.json[0]
    else:
        raise Exception('[origin] Manufacturer not found for Customer {}'.format(customer_name))

    for key in IGNORED_MANUFACTURER_FIELDS:
        manufacturer.pop(key)

    if not options['structure_only']:
        # Remove old UUIDs
        temp_manufacturer = deepcopy(manufacturer)
        for key in MANUFACTURER_PKS:
            temp_manufacturer.pop(key)

        # Update/Create Manufacturer and store the UUID
        new_obj = upsert_object('Manufacturer', temp_manufacturer, '/partners')
        ids['partners'][manufacturer['id']] = new_obj['id']

    manufacturer['products'] = copy_manufacturer_products(manufacturer)
    manufacturer['customers'] = copy_customer(customer_id)

    return manufacturer


def copy_manufacturer_products(manufacturer):
    """Copies the Products of the Manufacturer."""
    response = o_client.get('/products?manufacturer={}'.format(manufacturer['id']))
    print('[origin] Found {} Products for Manufacturer: {} ({})'
          .format(len(response.json), manufacturer['name'], manufacturer['id']))

    new_products = []
    for product in response.json:
        # Remove ignored fields
        for key in IGNORED_PRODUCT_FIELDS:
            product.pop(key)

        if not options['structure_only']:
            # Remove old UUIDs
            temp_product = deepcopy(product)
            for key in PRODUCT_PKS:
                temp_product.pop(key)

            # Apply new UUIDs
            temp_product['manufacturer'] = ids['partners'][product['manufacturer']]

            # Remove Meta and Specs for separate updates.
            meta = temp_product.pop('meta', [])
            specs = temp_product.pop('specs', [])

            # Update/Create Product and store the UUID
            new_obj = upsert_object('Product', temp_product, '/products')
            ids['products'][product['id']] = new_obj['id']

            # Upload Product Meta separately
            if meta:
                response = d_client.post('/products/{}/meta'.format(new_obj['id']), data=meta)
                if response.status_code != 201:
                    raise Exception('[{}]: {}'.format(response.status_code, response.json))
                print('[destination] Updated Product Meta for {}'.format(new_obj['name']))

            # Update Product Specs and Activate Product
            if product['state'] == 'active' and new_obj['state'] != 'active':
                response = d_client.patch('/products/{}'
                                          .format(new_obj['id']), data={'specs': specs})
                if response.status_code != 200:
                    print(response)
                    raise Exception('[{}]: {}'.format(response.status_code, response.json))

                response = d_client.put('/products/{}/activate'.format(new_obj['id']))
                if response.status_code != 204:
                    print(response)
                    raise Exception('[{}]: {}'.format(response.status_code, response.json))
                print('[destination] Activated Product: {} ({})'.format(new_obj['name'],
                                                                        new_obj['id']))

        new_products.append(product)

    return new_products


def relate_spaces(space):
    """Relates the newly copied Spaces to each other."""
    response = o_client.get('/spaces?parent_space={}'.format(space['id']))
    print('[origin] Found {} Spaces for Space: {} ({})'
          .format(len(response.json), space['name'], space['id']))

    spaces = []
    for child_space in response.json:
        child_space['child_spaces'] = relate_spaces(child_space) \
            if child_space['child_spaces'] else []
        child_space['devices'] = relate_devices(child_space) if child_space['devices'] else []

        if not options['structure_only']:
            temp_child_space = {
                'id': child_space['id'],
                'name': child_space['name'],
                'parent_space': ids['spaces'][child_space['parent_space']]
                if child_space['parent_space'] else None,
            }
            upsert_object('Child Space', temp_child_space, '/spaces')

        # Remove ignored fields
        for key in IGNORED_SPACE_FIELDS:
            child_space.pop(key)

        spaces.append(child_space)

    return spaces


def relate_devices(space):
    """Relates the Devices to their Spaces and Devices."""
    response = o_client.get('/devices?spaces={}'.format(space['id']))
    if response.status_code != 200:
        raise Exception('[{}]: {}'.format(response.status_code, response.json))

    print('[origin] Found {} Devices for Space: {} ({})'
          .format(len(response.json), space['name'], space['id']))

    devices = []
    for device in response.json:
        if not options['structure_only']:
            temp_device = {
                'id': device['id'],
                'name': device['name'],
                'parent_device': ids['devices'][device['parent_device']]
                if device['parent_device'] else None,
                'spaces': [ids['spaces'][space_id] for space_id in device['spaces']],
            }
            upsert_object('Space Device', temp_device, '/devices')

        # Remove ignored fields
        for key in IGNORED_DEVICE_FIELDS:
            device.pop(key)

        devices.append(device)

    return devices


def restore_names():
    """Restores the original names of the objects."""
    # TODO: Not so many requests would be nice.
    for obj_type in ('buildings', 'spaces', 'devices', 'products'):
        print('Restoring original names for {}'.format(obj_type.title()))
        for old_id, new_id in ids[obj_type].items():
            response = d_client.get('/{}/{}'.format(obj_type, new_id))
            original_name = response.json['name'].replace(' ({})'.format(old_id.split('-')[0]), '')
            d_client.patch('/{}/{}'.format(obj_type, new_id), data={'name': original_name})


def upsert_object(obj_type, obj, list_url):
    """Creates or updates the destination object and stores the UUID."""
    # Determine suitable Name and identifier.
    partial_uuid = obj['id'].split('-')[0]
    if obj_type in ('Manufacturer', 'Customer'):
        new_name = obj['name']
        identifier = obj['name']
    else:
        new_name = '{} ({})'.format(obj['name'], partial_uuid)
        identifier = partial_uuid

    # Locate object
    response = d_client.get('{}?name__contains={}&_include=id,name'.format(list_url, identifier))

    # Update object
    if len(response.json):
        new_obj = deepcopy(obj)
        new_obj['id'] = response.json[0]['id']
        new_obj['name'] = response.json[0]['name']
        response = d_client.patch(list_url + '/{}'.format(new_obj['id']), data=new_obj)
        if response.status_code != 200:
            raise Exception('[{}] {}: {}'.format(response.status_code, obj_type, response.json))
        print('[destination] Updated {}: {} ({})'.format(obj_type, obj['name'], obj['id']))
    # Create object
    else:
        new_obj = deepcopy(obj)
        new_obj['name'] = new_name
        response = d_client.post(list_url, data=new_obj)
        if response.status_code != 201:
            raise Exception('[{}] {}: {}'.format(response.status_code, obj_type, response.json))
        print('[destination] Created {}: {} ({})'.format(obj_type, obj['name'], obj['id']))

    return response.json

if __name__ == '__main__':
    """Copy Customer API structure to another API instance."""
    parser = ArgumentParser(prog='endpoint_tests')
    parser.add_argument('-c', '--customer', help='Customer ID to copy data for', required=True)
    parser.add_argument('-o', '--origin', help='Origin API to copy from (ex: qa1)', required=True)
    parser.add_argument('-u', '--origin-user', help='Origin API Username', required=True)
    parser.add_argument('-p', '--origin-pass', help='Origin API Password', required=True)
    parser.add_argument('-d', '--destination', help='Destination API to copy to (ex: localhost)',
                        required=True)
    parser.add_argument('-U', '--destination-user', help='Destination API Username',
                        required=True)
    parser.add_argument('-P', '--destination-pass', help='Destination API Password',
                        required=True)
    parser.add_argument('-s', '--structure-only', help='Display the API structure, don\'t copy',
                        action='store_true')
    (options, args) = parser.parse_known_args()
    options = vars(options)

    # Clean Origin/Destination
    for field in ('origin', 'destination'):
        options[field] = 'http://{}-api.gooee.io'.format(options[field]) \
            if options[field] != 'localhost' else 'http://localhost:8000'
    print('Copying Customer from {} to {}'.format(options['origin'], options['destination']))

    # Configure clients
    o_client = GooeeClient(api_base_url=options['origin'])
    o_client.authenticate(options['origin_user'], options['origin_pass'])
    d_client = GooeeClient(api_base_url=options['destination'])
    d_client.authenticate(options['destination_user'], options['destination_pass'])

    # Initiate copy
    structure = copy_manufacturer(options['customer'])
    if options['structure_only']:
        pprint.pprint(structure)
    restore_names()
