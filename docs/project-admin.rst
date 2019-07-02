pilot1-tools Project Admin Guide
================================

.. contents:: Table of Contents


Introduction
------------

This is guide to using ``pilot`` to create and manage projects and the datasets associated with them.
              
Prerequisites
^^^^^^^^^^^^^

You should review the `User Guide
<https://github.com/globusonline/pilot1-tools/blob/master/docs/user-guide.rst>`_ for:

- installing and configuring ``pilot``
- listing and downloading files

What is a Project?
------------------

A project is a searchable group of files and directories. When you create a new project,
all Pilot commands (list, describe, upload, download) will apply only to the files in
this project.

A project consists of:

- Datasets description?

- Name
- Description
- Short name
- A space for files on Petrel
- Metadata about the files
- A web site for searching for and downloading the files
- Groups to manage access to the files and metadata

See the `User Guide Projects Section <https://github.com/globusonline/pilot1-tools/blob/master/docs/user-guide.rst#id6>`_
for info on listing, setting, and displaying information about projects.

Creating a Project
------------------

Create a project with the following:

.. code-block:: bash

   (pilot1-env) $ pilot project add


You will be brought through an interactive prompt similar to the one below:


.. code-block:: bash

   Pick a title for your new project (My New Project)>
   Pick a short name (my-new-project)>
   Describe your new project (This project is intended to do X for scientists)>
   Set your Globus Group (NCI Users)>
   Summary:
   title               My New Project
   short_name          my-new-project
   description         This project is intended to do X for scientists
   group               NCI Users
   Continue with these values? (y/n)

The interactive prompt will try to choose sensible defaults. If your answer
isn't valid (such as the project name already exists), the prompt will ask you
to choose another. You can also type 'help' for more info, or 'q' to quite the
interactive prompt.

- Project Title: This will be displayed in the portal
- Short Name: This will act as the URL path for your portal
- Description: This will be shown in the portal on the 'projects' page
- Group: This Globus Group determines who can access the data you upload

Making Directories
------------------

You can make directories within your project with the ``mkdir`` command.

.. code-block:: bash

    (pilot1-env) $ pilot mkdir myfolder


Uploading Datasets to a Project
-------------------------------

Prerequisites: Make sure your project is set! You can check this with the ``pilot project`` command.

Upload datasets to your project with the ``upload`` subcommand.

Given the file example.tsv:

.. code-block:: tsv

   Numbers Title
   5       foo
   6       foo

We can upload ``example.tsv`` to our project with:

.. code-block:: bash

   (pilot1-env) $ pilot upload example.tsv /

If you want to place your file inside a folder, such as after running ``pilot mkdir myfolder``,
you can provide the relative path instead:

.. code-block:: bash

   (pilot1-env) $ pilot upload example.tsv myfolder


The above command will upload a file to the root directory of your project.
It will now be visible in the portal, and will show up when doing a ``pilot list``
or ``pilot describe example.tsv``.

You may notice some fields are missing from the metadata. Pilot will attempt to
gather as much metadata as possible about the file you are uploading, but you can
supplement the data by providing a JSON document ``example_metadata.json``:

.. code-block:: json

    {
        "data_type": "Metadata",
        "dataframe_type": "List,
    }

You can add a metadata JSON document with the ``-j`` flag.


.. code-block:: bash

   (pilot1-env) $ pilot upload -j my_metadata.json example.tsv /

You can find more info about what to include in ``my_metadata.json`` in the `Reference Guide
<https://github.com/globusonline/pilot1-tools/blob/master/docs/reference.rst>`_.


Deleting Datasets
-----------------

Deleting datasets removes both the file and the search record. Like the ``describe`` command,
you will refer to the search record by its relative path within the project.

Delete the above example file ``example.tsv`` with the following:

.. code-block:: bash

   (pilot1-env) $ pilot delete myfolder/example.tsv
