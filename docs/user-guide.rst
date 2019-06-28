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

Logging In
----------

TODO: Cover logging in

.. code-block:: bash

   pilot login
   You have been logged in.
   Your personal info has been saved as:
   Name:          Rick Wagner
   Organization:  Globus


   You can update these with "pilot profile -i"


Configuring Your Profile
------------------------

The command ``pilot profile -i`` will walk you through the settings for your profile. Your profile is used to create default information about the dataset you create or update. For this example, I need to change my organization, since this work is part of Argonne. We'll see a note about projects that we'll cover next.

.. code-block:: bash

   pilot profile -i
   Projects have updated. Use "pilot project update" to get the newest changes.
   No project set, use "pilot project set <myproject>" to set your project
   Name (Rick Wagner)> 
   Organization (Globus)> Argonne National Laboratory
   Your information has been updated

Working with Projects
---------------------

   
Update & List Projects
^^^^^^^^^^^^^^^^^^^^^^

Use ``pilot project`` to list available projects. An asterisk (*) marks
your currently selected project. Other commands, such as ``pilot list``, will
automatically use the project you select.

.. code-block:: bash

   pilot project
   Set project with "pilot project set <myproject>"
     * monty-python-discussions
     pilot-tutorial


Projects may be updated at any time. The Pilot CLI will check for updates every 24 hours,
but you can check any time with the following:

.. code-block:: bash

   pilot project update
   Added:
      > monty-python-and-the-holy-grail

   
Setting Your Current Project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Change your project with the ``project set`` subcommand:

.. code-block:: bash

   pilot project set pilot-tutorial
   Current project set to pilot-tutorial


.. code-block:: bash

   pilot project 
   Set project with "pilot project set <myproject>"
     ncipilot1
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

   pilot list
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

   pilot describe myfolder/example.tsv
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
