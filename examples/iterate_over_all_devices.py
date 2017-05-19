from time import sleep

from gooee import GooeeClient


client = GooeeClient('https://api.gooee.io')
client.authenticate('username@domain.com', 'password')

href = '/devices?limit=100'

while True:
    # Make the request to the Gooee API to get a full page of Devices.
    print('GET\'ing {}'.format(href))
    response = client.get(href)
    print('response = {}'.format(response))

    # Loop through each Device in this response.
    for device in response.json:
        print(device['id'], device['name'])

    #
    # Do stuff here, maybe.
    #

    # Traverse to the next link or terminate the loop.
    href = response._next_link
    if not href:
        break

    # Be nice.
    sleep(.1)
