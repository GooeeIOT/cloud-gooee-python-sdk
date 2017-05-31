#!/usr/bin/env python
"""
Copies an API hierarchy for a Customer to the depth of Devices.
Includes Manufacturer/Products and Users.

Usage:
    python copy_structure.py -c 095c5c4f-be42-4c5a-98da-20c6e4509799 -o qa1 -u ramon@gooee.com
        -p foo -d localhost -U ramon@gooee.com -P bar
"""
import base64, pprint, requests
from argparse import ArgumentParser
from copy import deepcopy

from gooee import GooeeClient

# Fields entirely omitted.
IGNORED_MANUFACTURER_FIELDS = ('devices_total', 'css', 'users', 'modified', 'created')
IGNORED_PRODUCT_FIELDS = ('created', 'modified', 'owner', 'manufacturer_name',
                          'activated_date')
IGNORED_CUSTOMER_FIELDS = ('created', 'modified')
IGNORED_BUILDING_FIELDS = ('modified', 'users', 'last_activity', 'created')
IGNORED_SPACE_FIELDS = ('created', 'last_activity', 'modified', 'service_profile')
IGNORED_DEVICE_FIELDS = ('created', 'commissioned_date', 'commission_state', 'modified',
                         'custom_fields', 'service_profile')

# Fields omitted during initial creation.
MANUFACTURER_PKS = ('customers', 'products')
PRODUCT_PKS = ('manufacturer',)
CUSTOMER_PKS = ('partner', 'buildings')
BUILDING_PKS = ('customer', 'spaces')
SPACE_PKS = ('scenes', 'connected_products', 'building', 'parent_space', 'devices', 'child_spaces')
DEVICE_PKS = ('building', 'connected_products', 'spaces', 'parent_device', 'child_devices')
USER_PKS = ('partner', 'customer', 'buildings')

# Roles
CUSTOMER_ADMIN = {
    'name': 'Customer Admin',
    'permission_sets': [
        'edit_customers',
        'manage_customer_users',
        'manage_buildings',
        'manage_customer_resources',
        'control_fixtures'
    ]
}
PARTNER_ADMIN = {
    'name': 'Partner Admin',
    'permission_sets': [
        'edit_customers',
        'manage_customer_users',
        'manage_buildings',
        'manage_customer_resources',
        'control_fixtures',
        'edit_partners',
        'manage_partner_users',
        'manage_customers'
    ]
}

ids = {
    'partners': {},
    'customers': {},
    'products': {},
    'buildings': {},
    'spaces': {},
    'devices': {},
    'users': {},
}

# TODO: Support pagination on worthy requests so we don't miss anything.
# TODO: Use an external tool to move the password hashes?
# TODO: Add support for Rules, Scenes, Schedules, and Connected Products.


def copy_building_devices(building, new_partner_id, new_customer_id):
    """Copies the Devices of a Building."""
    response_devices = []
    while True:
        response = o_client.get('/devices?building={}'.format(building['id']))
        if response.status_code != 200:
            raise Exception('[{}]: {}'.format(response.status_code, response.text))
        response_devices += response.json
        href = response._next_link
        if not href:
            break

    print('[origin] Found {} Devices for Building: {} ({})'
          .format(len(response_devices), building['name'], building['id']))

    devices = []
    for device in response_devices:
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
            temp_device['customer_scopes'] = [new_customer_id]
            temp_device['partner_scopes'] = [new_partner_id]

            # Update/Create Device and store the UUID
            meta = temp_device.pop('meta', [])
            new_obj = upsert_object('Building Device', temp_device, '/devices')
            ids['devices'][device['id']] = new_obj['id']

            # Upload Device Meta separately
            if meta:
                update_meta('Device', new_obj, meta, device)

        # Only display the Device without Spaces
        if not device['spaces']:
            devices.append(device)

    return devices


def copy_building_spaces(building, new_partner_id, new_customer_id):
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
            temp_space['customer_scopes'] = [new_customer_id]
            temp_space['partner_scopes'] = [new_partner_id]

            # Retain Logo
            temp_space['bg_image'] = get_image_data(space, 'bg_image')

            # Update/Create Space and store the UUID
            meta = temp_space.pop('meta', [])
            new_obj = upsert_object('Building Space', temp_space, '/spaces')
            ids['spaces'][space['id']] = new_obj['id']

            # Upload Space Meta separately
            if meta:
                update_meta('Space', new_obj, meta, space)

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
        temp_customer['partner_scopes'] = [ids['partners'][customer['partner']]]

        # Retain Logo
        temp_customer['logo'] = get_image_data(customer, 'logo')

        # Update/Create Customer and store the UUID
        new_obj = upsert_object('Customer', temp_customer, '/customers')
        ids['customers'][customer['id']] = new_obj['id']

    customer['buildings'] = copy_customer_buildings(customer, temp_customer['partner'])
    customer['users'] = copy_users(customer=customer)

    return [customer]


def copy_customer_buildings(customer, new_partner_id):
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
            new_customer_id = ids['customers'][building['customer']]
            temp_building['customer'] = new_customer_id
            temp_building['customer_scopes'] = [new_customer_id]
            temp_building['partner_scopes'] = [new_partner_id]

            # Update/Create Building and store the UUID
            meta = temp_building.pop('meta', [])
            new_obj = upsert_object('Building', temp_building, '/buildings')
            ids['buildings'][building['id']] = new_obj['id']

            # Upload Building Meta separately
            if meta:
                update_meta('Building', new_obj, meta, building)

        building['devices'] = copy_building_devices(building, new_partner_id, new_customer_id)
        building['spaces'] = copy_building_spaces(building, new_partner_id, new_customer_id)
        new_buildings.append(building)

    return new_buildings


def copy_manufacturers(old_customer_id):
    """
    Copies the Manufacturer of the Customer and related objects down to Device.

    A Customer might have a Partner different than the one that owns the Products they use.
    """
    # Identify Customer
    response = o_client.get('/customers/{}'.format(old_customer_id))
    if response.status_code != 200:
        raise Exception('[origin]: Cannot locate Customer')
    old_customer_id, customer_name = response.json['id'], response.json['name']
    print('[origin] Found Customer: {}'.format(customer_name))

    # Identify Partner of Customer
    print('[origin] Locating Manufacturer(s) for Customer: {}'.format(customer_name))
    pcresponse = o_client.get('/partners?customers__id={}'.format(old_customer_id))
    if len(pcresponse.json) == 1:
        manufacturers = [pcresponse.json[0]]
    else:
        raise Exception('[origin] Manufacturer not found for Customer {}'.format(customer_name))

    # Identify Partners of Device Products
    dresponse = o_client.get('/devices/?building__customer={}&_include=product'.format(old_customer_id))
    product_ids = set([d['product'] for d in dresponse.json] if dresponse.json else [])
    dpresponse = o_client.get('/partners/?customers!={}'.format(old_customer_id))
    manufacturers += dpresponse.json if dpresponse else []

    # Populate Partners
    initial_results = []
    for manufacturer in manufacturers:
        # Skip Partners that don't match our Products and/or Customer
        if not product_ids.intersection(set(manufacturer['products'])) \
                and old_customer_id not in manufacturer['customers']:
            continue

        for key in IGNORED_MANUFACTURER_FIELDS:
            manufacturer.pop(key)

        if not options['structure_only']:
            # Remove old UUIDs
            temp_manufacturer = deepcopy(manufacturer)
            for key in MANUFACTURER_PKS:
                temp_manufacturer.pop(key)

            # Retain Images
            for key in ('logo', 'favicon'):
                temp_manufacturer[key] = get_image_data(manufacturer, key)

            # Update/Create Manufacturer and store the UUID
            new_obj = upsert_object('Manufacturer', temp_manufacturer, '/partners')
            ids['partners'][manufacturer['id']] = new_obj['id']

        # Populate Partner Products
        manufacturer['products'] = copy_manufacturer_products(manufacturer)
        manufacturer['users'] = copy_users(partner=manufacturer)
        initial_results.append(manufacturer)

    # Only fetch the Customer of interest.
    secondary_results = []
    for manufacturer in initial_results:
        if pcresponse.json[0]['id'] == manufacturer['id']:
            manufacturer['customers'] = copy_customer(old_customer_id)
        secondary_results.append(manufacturer)

    return secondary_results


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

            # Retain Images
            for key in ('image', 'manufacturer_logo'):
                temp_product[key] = get_image_data(product, key)

            # Update/Create Product and store the UUID
            new_obj = upsert_object('Product', temp_product, '/products')
            ids['products'][product['id']] = new_obj['id']

            # Upload Product Meta separately
            if meta:
                update_meta('Product', new_obj, meta, product)

            # Update Product Specs and Activate Product
            if product['state'] == 'active' and new_obj['state'] != 'active':
                response = d_client.patch('/products/{}'
                                          .format(new_obj['id']), data={'specs': specs})
                if response.status_code != 200:
                    # Obsolete Specs, fallback to new Specs.
                    if 'specs' in response.text:
                        reset_specs(new_obj)
                    else:
                        raise Exception('[{}]: {}'.format(response.status_code, response.text))

                response = d_client.put('/products/{}/activate'.format(new_obj['id']))
                if response.status_code != 204:
                    # Missing Specs, fallback to new Specs.
                    if 'All the specs' in response.text:
                        reset_specs(new_obj)
                        d_client.put('/products/{}/activate'.format(new_obj['id']))
                    else:
                        raise Exception('[{}]: {}'.format(response.status_code, response.text))
                print('[destination] Activated Product: {} ({})'.format(new_obj['name'],
                                                                        new_obj['id']))

        new_products.append(product)

    return new_products


def copy_users(partner=None, customer=None):
    """
    Copies the Users of the Partner or Customer.

    Passwords of the Users need to be reset since we don't know what the passwords are via API.
    """
    obj_type = 'Partner User(s)' if partner else 'Customer User(s)'
    role = get_role(PARTNER_ADMIN) if partner else get_role(CUSTOMER_ADMIN)
    parent_data = partner if partner else customer
    if partner:
        response = o_client.get('/users?partner={}'.format(partner['id']))
    elif customer:
        response = o_client.get('/users?customer={}'.format(customer['id']))

    if response.status_code != 200:
        raise Exception('[{}]: {}'.format(response.status_code, response.text))
    print('[origin] Found {} {} for {}: {} ({})'.format(
        len(response.json), obj_type, obj_type.split()[0], parent_data['name'], parent_data['id']))

    users = []
    for user in response.json:
        if not options['structure_only']:
            # Remove old UUIDs
            temp_user = deepcopy(user)
            for key in USER_PKS:
                temp_user.pop(key)

            # # TODO: Copy the non-default Roles.
            # if temp_user['role'] != 1:
            #     # Remove non-existent Role
            #     temp_user.pop('role')

            # Assign Customer/Partner Admin Role for missing Roles.
            temp_user['role'] = role['id']
            temp_user['account_type'] = 'partner' if partner else 'customer'

            # LEGACY?: This isn't a valid account type.
            if temp_user['account_type'] == 'api':
                temp_user.pop('account_type')

            # LEGACY?: I've seen Users without invalid e-mails.
            if '@' not in temp_user['username']:
                continue

            # TODO: GC-3652 - +'s doesn't work on filters.
            if '+' in temp_user['username']:
                continue

            # Apply new UUIDs
            temp_user['partner'] = ids['partners'][user['partner']] if user['partner'] else None
            temp_user['customer'] = ids['customers'][user['customer']] if user['customer'] else None

            # Update/Create User and store the UUID
            new_obj = upsert_object('User', temp_user, '/users')
            ids['users'][user['id']] = new_obj['id']

            # Activate User
            response = d_client.post('/users/{}/activate'.format(new_obj['id']))
            if response.status_code != 200:
                raise Exception('[{}]: {}'.format(response.status_code, response.text))
            print('[destination] Activated User: {}'.format(new_obj['username']))

    return users


def get_image_data(data, key):
    """Gets the field data for an image."""
    image_url = data.pop(key)
    if image_url:
        image_response = requests.get(image_url, stream=True)
        return base64.b64encode(image_response.raw.read())

    return ''


def get_role(role_data):
    """Finds or creates the Role using Name and Permission Sets."""
    # Check for Role using Name
    response = d_client.get('/roles?name={}'.format(role_data['name']))
    if len(response.json):
        return response.json[0]

    # Check for Role using Permission Sets
    response = d_client.get('/roles')
    for role in response.json:
        if set(role['permission_sets']) == set(role_data['permission_sets']):
            return role

    # Create Role
    response = d_client.post('/roles', data=role_data)
    if response.status_code != 201:
        raise Exception('[{}]: {}'.format(response.status_code, response.text))

    return response.json


def reset_specs(new_product):
    """Reset the Product Specs."""
    new_specs = []
    for spec in new_product['specs']:
        if 'modified' in spec:
            spec.pop('modified')
        new_specs.append(spec)

    response = d_client.patch('/products/{}'.format(new_product['id']), data={'specs': new_specs})

    if response.status_code != 200:
        raise Exception('[{}]: {}'.format(response.status_code, response.text))


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
            upsert_object('Child Space with Parent Space', temp_child_space, '/spaces')

        # Remove ignored fields
        for key in IGNORED_SPACE_FIELDS:
            child_space.pop(key)

        spaces.append(child_space)

    return spaces


def relate_devices(space):
    """Relates the Devices to their Spaces and Devices."""
    response = o_client.get('/devices?spaces={}'.format(space['id']))
    if response.status_code != 200:
        raise Exception('[{}]: {}'.format(response.status_code, response.text))

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
            upsert_object('Space with Device', temp_device, '/devices')

        # Remove ignored fields
        for key in IGNORED_DEVICE_FIELDS:
            device.pop(key)

        devices.append(device)

    return devices


def restore_names():
    """Restores the original names of the objects."""
    for obj_type in ('buildings', 'spaces', 'devices', 'products'):
        print('[destination] Restoring original names for {}'.format(obj_type.title()))
        for old_id, new_id in ids[obj_type].items():
            response = d_client.get('/{}/{}'.format(obj_type, new_id))
            original_name = response.json['name'].replace(' ({})'.format(old_id.split('-')[0]), '')
            d_client.patch('/{}/{}'.format(obj_type, new_id), data={'name': original_name})


def update_meta(obj_type, new_obj, meta, old_obj):
    """Updates Meta of an object."""
    new_meta = []
    for meta in meta:
        # Omit System Meta
        if '~' not in meta['name']:
            new_meta.append(meta)

    # Stash old IDs in Meta
    if old_obj['data_service_id']:
        new_meta.append({'name': 'old_data_service_id', 'value': old_obj['data_service_id']})
    new_meta.append({'name': 'old_id', 'value': old_obj['id']})

    response = d_client.post('/{}s/{}/meta'.format(obj_type.lower(), new_obj['id']), data=new_meta)
    if response.status_code != 201:
        raise Exception('[{}]: {}'.format(response.status_code, response.text))
    print('[destination] Updated {} Meta for {}'.format(obj_type, new_obj['name']))


def upsert_object(obj_type, obj, list_url):
    """Creates or updates the destination object and stores the UUID."""
    # Determine suitable Name and URL.
    new_name = None
    partial_uuid = obj['id'].split('-')[0]
    if obj_type in ('Manufacturer', 'Customer'):
        name_key = 'name'
        response = d_client.get('{}?name={}&_include=id,name'.format(list_url, obj['name']))
    elif obj_type == 'User':
        name_key = 'username'
        response = d_client.get('{}?username={}&_include=id,name'.format(list_url, obj['username']))
    else:
        name_key = 'name'
        new_name = '{} ({})'.format(obj['name'], partial_uuid)
        response = d_client.get('{}?name__contains={}&_include=id,name'
                                .format(list_url, partial_uuid))

    # Update object
    if len(response.json):
        new_obj = deepcopy(obj)
        new_obj['id'] = response.json[0]['id']

        # Apply custom Name
        if new_name:
            new_obj['name'] = new_name

        response = d_client.patch(list_url + '/{}'.format(new_obj['id']), data=new_obj)
        if response.status_code != 200:
            raise Exception('[{}] {}: {}'.format(response.status_code, obj_type, response.text))
        print('[destination] Updated {}: {} ({})'.format(obj_type, obj[name_key], obj['id']))
    # Create object
    else:
        new_obj = deepcopy(obj)

        # Apply custom Name
        if new_name:
            new_obj['name'] = new_name

        response = d_client.post(list_url, data=new_obj)
        if response.status_code != 201:
            raise Exception('[{}] {}: {}'.format(response.status_code, obj_type, response.text))
        print('[destination] Created {}: {} ({})'.format(obj_type, obj[name_key], obj['id']))

    return response.json

if __name__ == '__main__':
    """Copy Customer API structure to another API instance."""
    parser = ArgumentParser(prog='endpoint_tests')
    parser.add_argument('-c', '--customer', help='Customer ID to copy data for.', required=True)
    parser.add_argument('-o', '--origin', help='Origin API to copy from (ex: qa1).', required=True)
    parser.add_argument('-u', '--origin-user', help='Origin API Username.', required=True)
    parser.add_argument('-p', '--origin-pass', help='Origin API Password.', required=True)
    parser.add_argument('-d', '--destination', help='Destination API to copy to (ex: localhost).',
                        required=True)
    parser.add_argument('-U', '--destination-user', help='Destination API Username.',
                        required=True)
    parser.add_argument('-P', '--destination-pass', help='Destination API Password.',
                        required=True)
    parser.add_argument('-s', '--structure-only', help='Display the API structure, don\'t copy.',
                        action='store_true')
    parser.add_argument('-r', '--restore-names', help='Restore original names.  Avoid dupes, only '
                                                      'use once.',
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
    try:
        structure = copy_manufacturers(options['customer'])
        if options['structure_only']:
            pprint.pprint(structure)
        if not options['structure_only'] and options['restore_names']:
            restore_names()
    except Exception as e:
        print('\a')
        raise e

