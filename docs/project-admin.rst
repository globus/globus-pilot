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

  4 items to set. Type "help" for more information or "q" to quit.
  Pick a title for your new project (My New Project)> Pilot Tutorial
  Pick a short name (pilot-tutorial)>
  Describe your new project (This project is intended to do X for scientists)> Guide to using the pilot CLI for managing and accessing data.
  Available Groups: NCI Admins, NCI Users, Public
  Set your group (NCI Users)> Public
  Summary:
  title               Pilot Tutorial
  short_name          pilot-tutorial
  description         Guide to using the pilot CLI for managing and accessing data.
  group               Public
  Continue with these values? (y/n)y
  Updating global project list... Success
  Switched to project pilot-tutorial
  Your new project "Pilot Tutorial" has been added! Users will be notified within 24 hours next time they use this tool.

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

    (pilot1-env) $ pilot mkdir tabular


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
