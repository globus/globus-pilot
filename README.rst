Globus Pilot
------------
.. image:: https://readthedocs.org/projects/globus-pilot/badge/?version=latest&style=flat

.. image:: https://github.com/globusonline/globus-pilot/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/globusonline/globus-pilot/actions/workflows/

.. image:: https://img.shields.io/pypi/v/globus-pilot.svg
    :target: https://pypi.python.org/pypi/globus-pilot

.. image:: https://img.shields.io/pypi/wheel/globus-pilot.svg
    :target: https://pypi.python.org/pypi/globus-pilot

.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :alt: License
    :target: https://opensource.org/licenses/Apache-2.0

A Command Line tool for managing data in Globus Search as well as transferring corresponding data to and from a Globus Endpoint.


Installation
------------

Pilot requires python 3.6+, you can install with the following:

.. code-block:: bash

    pip install globus-pilot


See the `Read-The-Docs Page
<https://globus-pilot.readthedocs.io/en/latest/index.html>`_ for more options.


Quick Start
-----------

For a full walkthrough, see the `User Guide
<https://github.com/globusonline/pilot1-tools/blob/master/docs/user-guide.rst>`_.
Administrators can also view the `Admin Guide
<https://github.com/globusonline/pilot1-tools/blob/master/docs/project-admin.rst>`_.

A quick walkthrough is below.

First, login using Globus:

.. code-block:: bash

    pilot login

Set your Search Index:

.. code-block:: bash

    pilot index set <myindex>


Then choose your project. See ``pilot project info`` for info on any listed project:

.. code-block:: bash

    pilot project
    pilot project set <myproject>

You can use ``list`` to get a high level overview of the data:

.. code-block:: bash

    pilot list

If you want more detail about a specific search record, you can use ``describe`` to view details:

.. code-block:: bash

    pilot describe dose_response/rescaled_combined_single_drug_growth

You can also download the data associated with the search record:

.. code-block:: bash

    pilot download dose_response/rescaled_combined_single_drug_growth


When you want to add more data to the collection, you can use the ``upload`` command. This will upload the
data in addition to creating a record in Globus Search to track it.


.. code-block:: bash

    touch my_data.tsv
    pilot upload my_data.tsv test_dir --dry-run --verbose -j my_metadata.json

The two flags '--dry-run --verbose' are optional but handy for testing. '-j my_metadata.json'
is for providing any extra metadata the pilot tool can't automatically determine. Here is an example of the metadata:

.. code-block:: json

    {
        "title": "Drug Identifiers",
        "description": "Drug identifiers, including InChIKey, SMILES, and PubChem.",
        "data_type": "Drug Response",
        "dataframe_type": "List",
        "source": [
            "InChIKey",
            "SMILES",
            "PubChem"
        ]
    }


Running Tests
-------------

Ensure packages in test-requirements.txt are installed, then run:

.. code-block:: bash

    pytest

And for coverage:

.. code-block:: bash

    pytest --cov pilot


