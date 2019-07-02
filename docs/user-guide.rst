pilot1-tools User Guide
=======================

.. contents:: Table of Contents

Introduction
------------

NCI Pilot Tools are a suite of command line utilities for quickly uploading data
and publicizing it on Globus Search for easy accessibility and discovery. You can
view the current list of projects by going to `petreldata.net<https://petreldata.net/nci-pilot1/>`_.

By following the guide below, you will be able to use the NCI Pilot tools to discover,
and access files from the projects you can see on the portal above.

Installation
------------

These tools are available on Conda for Python 3.6, you can install them with the following:

.. code-block:: bash

    conda create -n pilot1-env -c conda-forge -c nickolaussaint pilot1-tools


You can see the `Developer Guide Installation
<https://github.com/globusonline/pilot1-tools/blob/master/docs/developer-guide.rst>`_ for more options.

Uninstall
---------


.. code-block:: bash

    conda uninstall pilot1-tools


Updates
-------

Updating uses the same command as installation. Conda will ask if you would
like to upgrade to the latest version.

.. code-block:: bash

    conda install -c conda-forge -c nickolaussaint pilot1-tools


The Pilot Client
----------------

The Pilot Client installs a new command called ``pilot``. Enter ``pilot``
to list all of the available commands:

.. code-block:: bash

    (pilot1-env) $ pilot
    Usage: pilot [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      delete    Delete a search entry
      describe  Output info about a dataset
      download  Download a file to your local directory.
      list      List known records in Globus Search
      login     Login with Globus
      logout    Revoke local tokens
      mkdir     The new path to create
      profile   Output Globus Identity used to login
      project   Set or display project information
      status    Check status of transfers
      upload    Upload dataframe to location on Globus and categorize it in...
      version   Show version and exit
      whoami    Output Globus Identity used to login

All commands support the ``--help`` argument for more information. Some commands,
such as ``status``, can be run without arguments. Other commands, such as ``project``
support additional subcommands. Each subcommand also supports help, these are all
valid commands:

- ``pilot --help``
- ``pilot login --help``
- ``pilot project set --help``

Listing Version
---------------

List the current version with:


.. code-block:: bash

   (pilot1-env) $ pilot version


Logging In
----------

Login with the following command:

.. code-block:: bash

   (pilot1-env) $ pilot login
   You have been logged in.
   Your personal info has been saved as:
   Name:          Rick Wagner
   Organization:  Globus


   You can update these with "pilot profile -i"

The Pilot Client expects you to login from a secure location, and has an indefinite
session time. If you would like additional security, or you are logging in at a
public location, you can use the following:

.. code-block:: bash

   (pilot1-env) $ pilot login --no-refresh-tokens

These credentials will expire in 48 hours.

Logging Out
-----------

Use the ``logout`` command to revoke your Globus Tokens. This is imperative on
public systems.

.. code-block:: bash

   (pilot1-env) $ pilot logout
   You have been logged out.

This will keep all other settings and profile information for the next time
you login. If you would like to clear that too, you can use the ``--purge``
option.

.. code-block:: bash

   (pilot1-env) $ pilot logout --purge
   You have been logged out.
   All local user info and logs have been deleted.


List Your Information
---------------------

List your information with the following

.. code-block:: bash

   (pilot1-env) $ pilot profile
   You have been logged in.
   Your personal info has been saved as:
   Name:          Rick Wagner
   Organization:  Globus


   You can update these with "pilot profile -i"



Configuring Your Profile
------------------------

The command ``pilot profile -i`` will walk you through the settings for your
profile. Your profile is used to create default information about the dataset
you create or update. For this example, I need to change my organization,
since this work is part of Argonne. We'll see a note about projects that we'll
cover next.

.. code-block:: bash

   (pilot1-env) $ pilot profile -i
   Projects have updated. Use "pilot project update" to get the newest changes.
   No project set, use "pilot project set <myproject>" to set your project
   Name (Rick Wagner)> 
   Organization (Globus)> Argonne National Laboratory
   Your information has been updated


Setting Your Local Endpoint
---------------------------

If you are sshed into a remote system, you may want to use a GCS endpoint instead
of a GCP client. You can set this with the ``--local-endpoint`` option.

.. code-block:: bash

    (pilot1-env) $ pilot profile --local-endpoint ddb59af0-6d04-11e5-ba46-22000b92c6ec
    Your local endpoint has been set!
    Your Profile:
    Name:           Nickolaus Saint
    Organization:   Globus
    Local Endpoint: My GCS Endpoint
    Local Path:     None

The local path on the endpoint will default to the settings on the endpoint, but
can also be explicitly stated. You can add a colon separated by your path:

.. code-block:: bash

    (pilot1-env) $ pilot profile --local-endpoint ddb59af0-6d04-11e5-ba46-22000b92c6ec:~/my-subfolder

Please note: You should only use this if your session is local to the endpoint. You may
encounter strange behavior with the ``upload`` and ``download`` commands placing files
in unexpected locations if your endpoint is remote to where you're actually working.

Working with Projects
---------------------

   
List Update & Projects
^^^^^^^^^^^^^^^^^^^^^^

Use ``pilot project`` to list available projects. An asterisk (*) marks
your currently selected project. Other commands, such as ``pilot list``, will
automatically use the project you select.

.. code-block:: bash

   (pilot1-env) $ pilot project
   Set project with "pilot project set <myproject>"
     project1
     project2
     * project3
     pilot-tutorial


Projects may be updated at any time. The Pilot CLI will check for updates every 24 hours,
but you can check any time with the following:

.. code-block:: bash

   (pilot1-env) $ pilot project update
   Added:
      > monty-python-discussions

Fetch Info on a Project
^^^^^^^^^^^^^^^^^^^^^^^

Use the ``info`` subcommand for more detailed info.

.. code-block:: bash

    (pilot1-env) $ pilot project info
    Project 3
    Endpoint                 petrel#ncipilot
    Group                    Project 3 Group
    Base Path                /projects/project3

    This is an example project.

You can also query other projects:

.. code-block:: bash

    (pilot1-env) $ pilot project info pilot-tutorial
    Pilot Tutorial
    Endpoint                 petrel#ncipilot
    Group                    public
    Base Path                /projects/pilot_tutorial

    Guide to using the pilot CLI for managing and accessing data.

   
Setting Your Current Project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Change your project with the ``project set`` subcommand:

.. code-block:: bash

   (pilot1-env) $ pilot project set pilot-tutorial
   Current project set to pilot-tutorial


.. code-block:: bash

   (pilot1-env) $ pilot project
   Set project with "pilot project set <myproject>"
     project1
     project2
     project3
     * pilot-tutorial


Working with Datasets
---------------------

Each Dataset represents a file on Petrel and a corresponding search entry in
Globus Search. You can discover datasets with the  ``list`` and ``describe``
commands, and fetch data using the ``download`` command.

Each of these commands will only act on datasets within your selected _project_.

Listing Datasets
^^^^^^^^^^^^^^^^

Use the list command to see all of the datasets for this project:

.. code-block:: bash

   (pilot1-env) $ pilot list
   Title                Data       Dataframe Rows   Column Size   Path
   example.tsv                               95     2      674    myfolder/example.tsv

This will list high level general info about datasets in this project, in addition to
a **path** we can use to refer to a specific dataset. For this example, we would refer
to the dataset "example.tsv" above using ``myfolder/example.tsv``


Describing Datasets
^^^^^^^^^^^^^^^^^^^

Use ``pilot describe <dataset>`` to get detailed info about a dataset.

In the ``pilot list`` example above, we saw there was one record with the path
"myfolder/example.tsv". Running the following command gives us the following
output:

.. code-block:: bash

   (pilot1-env) $ pilot describe myfolder/example.tsv
   Title                example.tsv
   Authors              Curie, Marie
   Publisher            University of Paris
   Subjects             radium
                        physics
   Dates                Created:  Thursday, Jun 27, 1910
   Data
   Dataframe
   Rows                 95
   Columns              2
   Formats              text/tab-separated-values
   Version              1
   Size                 674
   Description


   Column Name          Type    Count  Freq Top         Unique Min    Max    Mean   Std    25-PCTL 50-PCTL 75-PCTL
   Numbers              float64 95                             5.0    99.0   52.0   27.568 28.5    52.0    75.5
   Title                string  95     50   baz         3

   Other Data
   Subject              globus://ebf55996-33bf-11e9-9fa4-0a06afd4a22e/projects/pilot_tutorial_5/simple.tsv
   Portal               https://petreldata.net/nci-pilot1/detail/globus%253A%252F%252Febf55996-33bf-11e9-9fa4-0a06afd4a22e%252Fprojects%252Fpilot_tutorial_5%252Fsimple.tsv



Downloading Datasets
^^^^^^^^^^^^^^^^^^^^

Use ``pilot download <dataset>`` to download a dataset. Using the example above, where
"myfolder/example.tsv" is a dataset we discovered from the ``pilot list`` command:


.. code-block:: bash

   pilot describe myfolder/example.tsv
   Saved example.tsv


Checking Status of Transfers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have transferred data using Globus, you can check the status of the transfer
with the ``pilot status`` command.

(pilot1-env) $ pilot status
ID  Dataframe                     Status    Start Time        Task ID
0   /simple.tsv                   SUCCEEDED 2019-07-01 09:04  da1ffbdc-9c19-11e9-8219-02b7a92d8e58
