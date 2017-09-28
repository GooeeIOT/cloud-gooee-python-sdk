Gooee Python SDK
================

Official Python SDK for Gooee_ API.
See the LICENSE file for license and copyright information.

-  Installation_
-  Usage_
-  License_

.. _Installation:

Installation
~~~~~~~~~~~~

Minimum System Requirements
___________________________

-  Python 2.6+ or Python 3.3+

Installation from PyPI
______________________

.. code-block:: sh

    $ pip install gooee-sdk

If you need to, you can also use `easy_install`:

.. code-block:: sh

    $ easy_install gooee-sdk

Build from source
_________________


.. code-block:: sh

    git clone https://github.com/GooeeIOT/gooee-python-sdk.git
    cd gooee-python-sdk
    python setup.py install

.. _Usage:

Usage
~~~~~

To use the SDK in your project:

.. code-block:: python

    from gooee import GooeeClient

    client = GooeeClient()
    client.authenticate('username@example.com', 'YourPasswordHere')
    response = client.get('/buildings')

That is all!

.. _Gooee: https://www.gooee.com


.. _License:

License
~~~~~~~

This SDK is distributed under the `Apache License, Version
2.0 <http://www.apache.org/licenses/LICENSE-2.0>`__, see LICENSE
for more information.
