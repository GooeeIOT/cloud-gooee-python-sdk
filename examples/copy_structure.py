#!/usr/bin/env python
"""
Copies an API hierarchy for a Customer to the depth of Devices.  Includes Manufacturer/Products.

Usage:
    python copy_structure.py -c 095c5c4f-be42-4c5a-98da-20c6e4509799 -o qa1 -u ramon@gooee.com
        -p foo -d localhost -U ramon@gooee.com -P bar
"""
from argparse import ArgumentParser
from copy import deepcopy

from gooee import GooeeClient

COPY_STRUCTURE = True

# Fields entirely omitted.
IGNORED_MANUFACTURER_FIELDS = ('devices_total', 'logo', 'css', 'tags', 'users', 'modified',
                               'created', 'favicon', 'preferences')
IGNORED_PRODUCT_FIELDS = ('created', 'modified', 'meta', 'image', 'tags', 'owner',
                          'manufacturer_name', 'manufacturer_logo', 'activated_date')
IGNORED_CUSTOMER_FIELDS = ('created', 'logo', 'modified', 'tags')
IGNORED_BUILDING_FIELDS = ('meta', 'modified', 'tags', 'users', 'last_activity', 'created')
IGNORED_SPACE_FIELDS = ('bg_image', 'created', 'last_activity', 'meta', 'modified',
                        'service_profile', 'tags')
IGNORED_DEVICE_FIELDS = ('created', 'commissioned_date', 'commission_state', 'meta', 'modified',
                         'custom_fields', 'service_profile', 'tags')

# Fields omitted during initial creation.
MANUFACTURER_PKS = ('customers', 'products')
PRODUCT_PKS = ('manufacturer',)
CUSTOMER_PKS = ('partner', 'buildings')
BUILDING_PKS = ('customer', 'spaces')
SPACE_PKS = ('scenes', 'connected_products', 'building', 'parent_space', 'devices', 'child_spaces')
DEVICE_PKS = ('building', 'connected_products', 'spaces', 'parent_device', 'child_devices')

new_ids = {}


def copy_building_devices(building):
    """Copies the Devices of a Building."""
    response = origin_client.get('/devices?building={}'.format(building['id']))
    if response.status_code != 200:
        raise Exception('[{}]: {}'.format(response.status_code, response.json))
    print('[origin] Found {} Devices for Building: {} ({})'
          .format(len(response.json), building['name'], building['id']))

    devices = []
    for device in response.json:
        # Remove ignored fields
        for key in IGNORED_DEVICE_FIELDS:
            device.pop(key)

        if COPY_STRUCTURE:
            temp_device = deepcopy(device)
            # Remove old UUIDs
            for key in DEVICE_PKS:
                temp_device.pop(key)

            temp_device['product'] = new_ids[device['product']]
            temp_device['building'] = new_ids[device['building']]
            upsert_object('Building Device', temp_device, '/devices')

        # Only display the Device without Spaces
        if not device['spaces']:
            devices.append(device)

    return devices


def copy_building_spaces(building):
    """Copies the Spaces of a Building."""
    response = origin_client.get('/spaces?building={}'.format(building['id']))
    print('[origin] Found {} Spaces for Building: {} ({})'
          .format(len(response.json), building['name'], building['id']))

    spaces = []
    for space in response.json:
        # Remove ignored fields
        for key in IGNORED_SPACE_FIELDS:
            space.pop(key)

        if COPY_STRUCTURE:
            temp_space = deepcopy(space)
            # Remove old UUIDs
            for key in SPACE_PKS:
                temp_space.pop(key)

            temp_space['building'] = new_ids[space['building']]
            upsert_object('Building Space', temp_space, '/spaces')

        if not space['child_spaces']:
            space.pop('child_spaces')
        else:
            space['child_spaces'] = relate_spaces(space)

        space['devices'] = relate_devices(space)
        if not space['parent_space']:
            space.pop('parent_space')
            spaces.append(space)

    return spaces


def copy_customer(customer_id):
    """Copies the Customer."""
    # Fetch Customer
    response = origin_client.get('/customers/{}'.format(customer_id))
    if response.status_code != 200:
        raise Exception('[origin]: Cannot locate Customer')
    customer = response.json

    # Remove ignored fields
    for key in IGNORED_CUSTOMER_FIELDS:
        customer.pop(key)

    if COPY_STRUCTURE:
        temp_customer = deepcopy(customer)
        # Remove old UUIDs
        for key in CUSTOMER_PKS:
            temp_customer.pop(key)
        temp_customer['partner'] = new_ids[customer['partner']]
        upsert_object('Customer', temp_customer, '/customers')

    customer['buildings'] = copy_customer_buildings(customer)

    return [customer]


def copy_customer_buildings(customer):
    """Copies the Buildings of the Customer."""
    response = origin_client.get('/buildings?customer={}'.format(customer['id']))
    print('[origin] Found {} Buildings for Customer: {} ({})'
          .format(len(response.json), customer['name'], customer['id']))

    new_buildings = []
    for building in response.json:
        # Remove ignored fields
        for key in IGNORED_BUILDING_FIELDS:
            building.pop(key)

        if COPY_STRUCTURE:
            temp_building = deepcopy(building)
            # Remove old UUIDs
            for key in BUILDING_PKS:
                temp_building.pop(key)
            temp_building['customer'] = new_ids[building['customer']]
            upsert_object('Building', temp_building, '/buildings')

        building['devices'] = copy_building_devices(building)
        building['spaces'] = copy_building_spaces(building)
        new_buildings.append(building)

    return new_buildings


def copy_manufacturer(customer_id):
    """Copies the Manufacturer of the Customer and related objects down to Device."""
    # Identify Customer
    response = origin_client.get('/customers/{}'.format(customer_id))
    if response.status_code != 200:
        raise Exception('[origin]: Cannot locate Customer')
    customer_id, customer_name = response.json['id'], response.json['name']
    print('[origin] Found Customer: {}'.format(customer_name))

    # Identify Partner/Manufacturer of Customer
    print('[origin] Locating Manufacturer for Customer: {}'.format(customer_name))
    response = origin_client.get('/partners?customers__id={}'.format(customer_id))
    if len(response.json) == 1:
        manufacturer = response.json[0]
    else:
        raise Exception('[origin] Manufacturer not found for Customer {}'.format(customer_name))

    for key in IGNORED_MANUFACTURER_FIELDS:
        manufacturer.pop(key)

    if COPY_STRUCTURE:
        temp_manufacturer = deepcopy(manufacturer)
        # Remove old UUIDs
        for key in MANUFACTURER_PKS:
            temp_manufacturer.pop(key)
        upsert_object('Manufacturer', temp_manufacturer, '/partners')

    manufacturer['products'] = copy_manufacturer_products(manufacturer)
    manufacturer['customers'] = copy_customer(customer_id)

    return manufacturer


def copy_manufacturer_products(manufacturer):
    """Copies the Products of the Manufacturer."""
    response = origin_client.get('/products?manufacturer={}'.format(manufacturer['id']))
    print('[origin] Found {} Products for Manufacturer: {} ({})'
          .format(len(response.json), manufacturer['name'], manufacturer['id']))

    new_products = []
    for product in response.json:
        # Remove ignored fields
        for key in IGNORED_PRODUCT_FIELDS:
            product.pop(key)

        if COPY_STRUCTURE:
            temp_product = deepcopy(product)
            # Remove old UUIDs
            for key in PRODUCT_PKS:
                temp_product.pop(key)
            temp_product['manufacturer'] = new_ids[product['manufacturer']]

            new_obj = upsert_object('Product', temp_product, '/products')
            if product['state'] == 'active' and new_obj['state'] != 'active':
                destination_client.put('/products/{}/activate'.format(new_obj['id']))
                print('[destination] Activated Product: {} ({})'.format(new_obj['name'],
                                                                        new_obj['id']))

        product.pop('specs')
        new_products.append(product)

    return new_products


def relate_spaces(space):
    """Relates the newly copied Spaces to each other."""
    response = origin_client.get('/spaces?parent_space={}'.format(space['id']))
    print('[origin] Found {} Spaces for Space: {} ({})'
          .format(len(response.json), space['name'], space['id']))

    spaces = []
    for child_space in response.json:
        if not child_space['child_spaces']:
            child_space.pop('child_spaces')
        else:
            child_space['child_spaces'] = relate_spaces(child_space)

        if not child_space['devices']:
            child_space.pop('devices')
        else:
            child_space['devices'] = relate_devices(child_space)

        # Remove ignored fields
        for key in IGNORED_SPACE_FIELDS:
            child_space.pop(key)

        if COPY_STRUCTURE:
            response = destination_client.get('/spaces/{}'.format(new_ids[child_space['id']]))
            if response.status_code != 200:
                raise Exception('[{}]: {}'.format(response.status_code, response.json))

            temp_child_space = response.json
            temp_child_space['id'] = child_space['id']
            temp_child_space['parent_space'] = new_ids[child_space['parent_space']]
            upsert_object('Child Space', temp_child_space, '/spaces', updating=True)

        spaces.append(child_space)

    return spaces


def relate_devices(space):
    """Relates the Devices to their Spaces and Devices."""
    response = origin_client.get('/devices?spaces={}'.format(space['id']))
    if response.status_code != 200:
        raise Exception('[{}]: {}'.format(response.status_code, response.json))

    print('[origin] Found {} Devices for Space: {} ({})'
          .format(len(response.json), space['name'], space['id']))

    devices = []
    for device in response.json:
        # Remove ignored fields
        for key in IGNORED_DEVICE_FIELDS:
            device.pop(key)

        if COPY_STRUCTURE:
            response = destination_client.get('/devices/{}'.format(new_ids[device['id']]))
            if response.status_code != 200:
                raise Exception('[{}]: {}'.format(response.status_code, response.json))

            temp_device = response.json
            temp_device['id'] = device['id']
            if device['parent_device']:
                temp_device['parent_device'] = new_ids[device['parent_device']]
            temp_device['spaces'] = [new_ids[space_id] for space_id in device['spaces']]
            upsert_object('Space Device', temp_device, '/devices', updating=True)

        devices.append(device)

    return devices


def upsert_object(obj_type, obj, list_url, updating=False):
    """Creates or updates the destination object and stores the UUID."""
    partial_uuid = obj['id'].split('-')[0]
    new_name = obj['name'] if updating else '{} ({})'.format(obj['name'], partial_uuid)
    response = destination_client.get('{}?name__contains={}'.format(list_url, partial_uuid))

    if len(response.json):
        new_obj = obj if updating else deepcopy(response.json[0])
        new_obj['id'] = response.json[0]['id']
        new_obj['name'] = new_name
        print('[destination] Found a matching {}: {} ({})'.format(obj_type, obj['name'], obj['id']))

        # Remove Product Specs for Active Products
        # TODO: Move this!
        if new_obj.get('state', 'draft') == 'active' and 'specs' in new_obj:
            new_obj.pop('specs')

        response = destination_client.patch(list_url + '/{}'.format(new_obj['id']), data=new_obj)
        if response.status_code != 200:
            raise Exception('[{}] {}: {}'.format(response.status_code, obj_type, response.json))
        print('[destination] Updated {}: {} ({})'.format(obj_type, obj['name'], obj['id']))
    else:
        new_obj = deepcopy(obj)
        new_obj['name'] = new_name
        response = destination_client.post(list_url, data=new_obj)
        if response.status_code != 201:
            raise Exception('[{}] {}: {}'.format(response.status_code, obj_type, response.json))
        new_obj = response.json
        print('[destination] Created {}: {} ({})'.format(obj_type, obj['name'], obj['id']))

    # Store new UUID.  Look-up using old UUID as key.
    new_ids[obj['id']] = new_obj['id']

    return new_obj

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
    (options, args) = parser.parse_known_args()
    options = vars(options)

    # Clean Origin/Destination
    for key in ('origin', 'destination'):
        options[key] = 'http://{}-api.gooee.io'.format(options[key]) \
            if options[key] != 'localhost' else 'http://localhost:8000'
    print('Copying Customer from {} to {}'.format(options['origin'], options['destination']))

    # Configure clients
    origin_client = GooeeClient(api_base_url=options['origin'])
    origin_client.authenticate(options['origin_user'], options['origin_pass'])
    destination_client = GooeeClient(api_base_url=options['destination'])
    destination_client.authenticate(options['destination_user'], options['destination_pass'])

    # Initiate copy
    structure = copy_manufacturer(options['customer'])
