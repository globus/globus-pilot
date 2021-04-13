Uploading Data
==============


Making Directories
------------------

You can make directories within your project with the ``mkdir`` command.

.. code-block:: bash

    (pilot1-env) $ pilot mkdir tabular


Uploading Datasets to a Project
-------------------------------

Prerequisites: Make sure your project is set! You can check this with the ``pilot project`` command.

Upload datasets to your project with the ``upload`` subcommand.

Given the file example.tsv:

.. code-block::

   Numbers Title
   5       foo
   6       foo

We can upload ``example.tsv`` to our project with:

.. code-block:: bash

   (pilot1-env) $ pilot upload example.tsv /

If you want to place your file inside a folder, such as after running ``pilot mkdir tabular``,
you can provide the relative path instead:

.. code-block:: bash

   (pilot1-env) $ pilot upload example.tsv tabular


The above command will upload a file to the root directory of your project.
It will now be visible in the portal, and will show up when doing a ``pilot list``
or ``pilot describe example.tsv``.

You may notice some fields are missing from the metadata. Pilot will attempt to
gather as much metadata as possible about the file you are uploading, but you can
supplement the data by providing a JSON document ``example_metadata.json``:

.. code-block::

    {
        "data_type": "Metadata",
        "dataframe_type": "List,
    }

You can add a metadata JSON document with the ``-j`` flag.


.. code-block:: bash

   (pilot1-env) $ pilot upload -j my_metadata.json example.tsv /

You can find more info about what to include in ``my_metadata.json`` in the `Reference Guide
<https://github.com/globusonline/pilot1-tools/blob/master/docs/reference.rst>`_.

Uploading Directories
---------------------

In addition to files, you can also upload entire directories. In this mode, every
file within the directory is treated as the same record. `pilot describe` and
`pilot download` will behave differently to show/act on the files contained
in the result instead of the result itself, but all command invocations remain
the same.

.. code-block:: bash

   (pilot1-env) $ pilot upload my_folder /

The above results in the `my_folder` record containing metadata on all files
inside the local folder. All files in the folder are then uploaded to the
destination.

Deleting Datasets
-----------------

Deleting datasets removes both the file and the search record. Like the ``describe`` command,
you will refer to the search record by its relative path within the project.

Delete the above example file ``example.tsv`` with the following:

.. code-block:: bash

   (pilot1-env) $ pilot delete tabular/example.tsv
