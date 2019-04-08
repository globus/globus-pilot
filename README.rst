pilot1-tools
------------



A Command Line tool for managing data in Globus Search as well as transferring corresponding data to and from a Globus Endpoint. 


Installation
------------

Pilot1 tools supported on Python 3.5 and higher

Install with pip:

.. code-block:: python

    pip install -e git+git@github.com:globusonline/pilot1-tools.git#egg=pilot1-tools


You will also need Globus Connect Personal installed on your machine. You can download
a copy here: https://www.globus.org/globus-connect-personal


Usage
-----

First, login using Globus:

.. code-block:: bash

    pilot login

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
    pilot upload my_data.tsv test_dir --test --dry-run --verbose -j my_metadata.json

The three flags '--test --dry-run --verbose' are optional but handy for testing. '-j my_metadata.json'
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



