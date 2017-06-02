#!/usr/bin/env python
"""
Interactive tool for commissioning Devices to a Building Space.

Usage:
    python commission_devices.py -b 095c5c4f-be42-4c5a-98da-20c6e4509799
"""
from argparse import ArgumentParser

from gooee import GooeeClient

# TODO: Paginate!


class CommissionDevices:

    def __init__(self):
        """Commission Devices to a Building Space."""
        parser = ArgumentParser(prog='endpoint_tests')
        parser.add_argument('-a', '--api', help='Host API (ex: qa1-api.gooee.io).', required=True)
        parser.add_argument('-u', '--user', help='Username.', required=True)
        parser.add_argument('-p', '--pass', help='Password.', required=True)
        parser.add_argument('-b', '--building', help='Building ID commission to.')
        parser.add_argument('-s', '--space', help='Space ID to commission to.')

        (options, args) = parser.parse_known_args()
        options = vars(options)

        options['api'] = 'https://{}-api.gooee.io'.format(options['api']) \
            if options['api'] != 'localhost' else 'http://localhost:8000'
        print('API Host: {}\n'.format(options['api']))

        # Configure clients
        self.client = GooeeClient(api_base_url=options['api'])
        self.client.authenticate(options['user'], options['pass'])

        building = self.get_building(options['building'])
        space = self.get_space(building, options['space'])
        gateway = self.get_gateway(building, space)

        # Create WIMs
        count = input('How many Devices will you commission? ')
        for c in range(0, int(count)):
            self.create_device(building, space, gateway)

    def get_building(self, building_id=None):
        """Identifies and provides the Building."""
        # Fetch Building of provided ID
        if building_id:
            response = self.client.get('/buildings/{}'.format(building_id))
            if response.status_code != 200:
                raise Exception('[{}]: {}'.format(response.status_code, response.text))
        else:
            # Create or List Buildings
            action = input('Create or list Buildings? (c/l) ')
            building = None
            if action == 'l':
                # List Buildings
                response = self.client.get('/buildings?limit=100')
                if response.status_code != 200:
                    raise Exception('[{}]: {}'.format(response.status_code, response.text))
                for index, building in enumerate(response.json):
                    print('{}) {}'.format(index, building['name']))

                # Select Building
                if len(response.json):
                    index_selected = input('* Select Building #: ')
                    building = response.json[int(index_selected)]
                else:
                    print('There are no Buildings to choose from.')

            # Create Building
            if not building:
                customer = self.get_customer()
                name = input('Provide a Building Name: ')
                building = {
                    'name': name,
                    'customer': customer['id'],
                    'timezone': 'UTC',
                    'location': {'city': 'Tampa',
                                 'addr1': '33 Goo Street',
                                 'postal_code': '33611',
                                 'state': 'FL',
                                 'country': 'US'}
                }
                response = self.client.post('/buildings', data=building)
                if response.status_code != 201:
                    raise Exception('[{}]: {}'.format(response.status_code, response.text))
                building = response.json

        print('+ Building: {} ({})\n'.format(building['name'], building['id']))

        return building

    def get_space(self, building, space_id=None):
        """Identifies and provides the Space."""
        # Fetch Space of provided ID
        if space_id:
            response = self.client.get('/spaces/{}'.format(space_id))
            if response.status_code != 200:
                raise Exception('[{}]: {}'.format(response.status_code, response.text))
        else:
            # Create or List Spaces
            action = input('Create or list Spaces? (c/l) ')
            space = None
            if action == 'l':
                # List Spaces
                response = self.client.get('/spaces?building={}&limit=100'.format(building['id']))
                if response.status_code != 200:
                    raise Exception('[{}]: {}'.format(response.status_code, response.text))
                for index, space in enumerate(response.json):
                    print('{}) {}'.format(index, space['name']))

                # Select Space
                if len(response.json):
                    index_selected = input('* Select Space #: ')
                    space = response.json[int(index_selected)]
                else:
                    print('There are no Spaces to choose from.')

            # Create Space
            if not space:
                name = input('Provide a Space Name: ')
                space = {'name': name, 'building': building['id'], 'type': 'room'}
                response = self.client.post('/spaces', data=space)
                if response.status_code != 201:
                    raise Exception('[{}]: {}'.format(response.status_code, response.text))
                space = response.json

        print('+ Space: {} ({})\n'.format(space['name'], space['id']))

        return space

    def get_gateway(self, building, space):
        """Identifies and provides the Gateway for a Building Space."""
        # Create or Gateways?
        gateway = None
        action = input('Create or list Gateways? (c/l) ')
        if action == 'l':
            # List Gateways
            response = self.client.get('/devices?building={}&space={}&limit=100'
                                  .format(building['id'], space['id']))
            if response.status_code != 200:
                raise Exception('[{}]: {}'.format(response.status_code, response.text))
            for index, gateway in enumerate(response.json):
                print('{}) {}'.format(index, gateway['name']))

            # Select Gateway
            if len(response.json):
                index_selected = input('Select #: ')
                gateway = response.json[int(index_selected)]
            else:
                print('There are no Gateways to choose from.')

        if not gateway:
            product = self.get_product('gateway')

            # Create Gateway
            name = input('Provide a Gateway Name: ')
            euid = input('Provide a Gateway EUID: ')
            space = {
                'name': name,
                'building': building['id'],
                'space': [space['id']],
                'euid': euid,
                'product': product['id'],
            }
            response = self.client.post('/devices', data=space)
            if response.status_code != 201:
                raise Exception('[{}]: {}'.format(response.status_code, response.text))
            gateway = response.json

        print('+ Gateway: {} ({})\n'.format(gateway['name'], gateway['id']))

        return gateway

    def create_device(self, building, space, gateway):
        """Creates Devices for a Space and associates them with their Gateway."""
        product = self.get_product('wim')

        # Create Device
        name = input('Provide a WIM Name: ')
        euid = input('Provide a WIM EUID: ')
        space = {
            'name': name,
            'building': building['id'],
            'spaces': [space['id']],
            'euid': euid,
            'product': product['id'],
            'parent_device': gateway['id']
        }
        response = self.client.post('/devices', data=space)
        if response.status_code != 201:
            raise Exception('[{}]: {}'.format(response.status_code, response.text))
        device = response.json

        print('+ WIM: {} ({})\n'.format(device['name'], device['id']))
        return device

    def get_customer(self):
        """Identifies a random Customer."""
        response = self.client.get('/customers')
        if response.status_code != 200:
            raise Exception('[{}]: {}'.format(response.status_code, response.text))
        if not len(response.json):
            # Create Customer
            partner = self.get_partner()
            customer = {
                'name': 'Gooee',
                'partner': partner['id'],
                'timezone': 'UTC',
                'location': {'city': 'Tampa',
                             'addr1': '33 Goo Street',
                             'postal_code': '33611',
                             'state': 'FL',
                             'country': 'US'}
            }
            response = self.client.post('/customers', data=customer)
            if response.status_code != 201:
                raise Exception('[{}]: {}'.format(response.status_code, response.text))
            return response.json
        else:
            return response.json

    def get_partner(self, ):
        """Identifies a random Partner Manufacturer."""
        response = self.client.get('/partners?is_manufacturer=True')
        if response.status_code != 200:
            raise Exception('[{}]: {}'.format(response.status_code, response.text))
        if not len(response.json):
            raise Exception('No Partner Manufacturers found.')

        return response.json[0]

    def get_product(self, device_type):
        """Identifies a random Product for the Device Type."""
        response = self.client.get('/products?type={}&active=True'.format(device_type))
        if response.status_code != 200:
            raise Exception('[{}]: {}'.format(response.status_code, response.text))

        # Couldn't find a Product
        if not len(response.json):
            partner = self.get_partner()

            # Create Product
            product = {
                'name': device_type.title(),
                'manufacturer': partner['id'],
                'sku': device_type,
                'type': device_type,
                'description': device_type,
            }
            response = self.client.post('/products', data=product)
            if response.status_code != 201:
                raise Exception('[{}]: {}'.format(response.status_code, response.text))
            product = response.json

            # Activate Product
            new_specs = []
            for spec in product['specs']:
                spec.pop('modified')
                new_specs.append(spec)

            response = self.client.patch('/products/{}'.format(product['id']), data={'specs': new_specs})
            if response.status_code != 200:
                raise Exception('[{}]: {}'.format(response.status_code, response.text))
            product = response.json

            response = self.client.put('/products/{}/activate'.format(product['id']))
            if response.status_code != 204:
                raise Exception('[{}]: {}'.format(response.status_code, response.text))
        # Found a Product
        else:
            product = response.json[0]

        return product


if __name__ == '__main__':
    CommissionDevices()()
