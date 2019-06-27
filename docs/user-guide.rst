pilot1-tools User Guide
=======================

.. contents:: Table of Contents

Installation
------------

TODO: Link to or copy README

Uninstall
---------

TODO: Link to or copy README

.. code-block:: bash

    pip uninstall pilot1-tools


Updates
-------

TODO: Link to or copy README

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

   pilot project set ncipilot1-test
   Current project set to ncipilot1-test


.. code-block:: bash

   pilot project 
   Set project with "pilot project set <myproject>"
     ncipilot1
     * ncipilot1-test


Working with Datasets
---------------------

TODO

Listing Datasets
^^^^^^^^^^^^^^^^

Searching for Datasets
^^^^^^^^^^^^^^^^^^^^^^

Downloading Datasets
^^^^^^^^^^^^^^^^^^^^

TODO

- Describe Globus vs. HTTPS
- Add ``set endpoint <endpoint>:<path>`` to override GCP
