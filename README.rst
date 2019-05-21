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


Mac OSX
~~~~~~~

For Mac OSX, you may need to install headers. Ensure XCode is installed

.. code-block:: bash

    xcode-select --install

Headers for Mac have moved recently, causing some components not to install. You can reinstall
the old headers here:

.. code-block:: bash

    open /Library/Developer/CommandLineTools/Packages/macOS_SDK_headers_for_macOS_10.14.pkg


Conda
~~~~~

These tools are available on Conda for Python 3.6, you can install them with the following:

.. code-block:: bash

    conda create -n pilot1-env -c conda-forge -c nickolaussaint pilot1-tools


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


Running Tests
-------------

Ensure packages in test-requirements.txt are installed, then run:

.. code-block:: bash

    pytest

And for coverage:

.. code-block:: bash

    pytest --cov pilot


Building for Conda
------------------

Currently, the tableschema package has not been built for python 3.7, so this only
lists instructions for python 3.6. Two channels must be used, nickolaussaint and
conda-forge. The nickolaussaint channel contains fair-research-login, and conda-forge
contains various other packages we need including the globus-sdk.


.. code-block:: bash

    conda build -c nickolaussaint -c conda-forge --python 3.6 .

