pilot1-tools
------------
.. image:: https://anaconda.org/nickolaussaint/pilot1-tools/badges/version.svg
  :target: https://anaconda.org/nickolaussaint/pilot1-tools


A Command Line tool for managing data in Globus Search as well as transferring corresponding data to and from a Globus Endpoint.


Installation
------------

These tools are available on Conda for Python 3.6, you can install them with the following:

.. code-block:: bash

    conda create -n pilot1-env -c conda-forge -c nickolaussaint pilot1-tools


You can see the `Developer Guide Installation
<https://github.com/globusonline/pilot1-tools/blob/master/docs/developer-guide.rst>`_ for more options.


Setting Your Local
^^^^^^^^^^^^^^^^^^

The first time you run `pilot`, you may encounter an error an error like the one below:

.. code-block::

    RuntimeError: Click will abort further execution because Python 3 was
      configured to use ASCII as encoding for the environment.


This can happen if on systems with custom configured UTF-8 settings. You should
see a list of encodings your system supports, simply choose one and set it.
For example:

.. code-block::

    export LC_ALL=en_US.utf-8
    export LANG=en_US.utf-8


Replace ``en_US.utf-8`` with an encoding your system supports.


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


Building for Conda
------------------

Currently, the tableschema package has not been built for python 3.7, so this only
lists instructions for python 3.6. Two channels must be used, nickolaussaint and
conda-forge. The nickolaussaint channel contains fair-research-login, and conda-forge
contains various other packages we need including the globus-sdk.


.. code-block:: bash

    conda build -c nickolaussaint -c conda-forge --python 3.6 .

