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

TODO

.. code-block:: bash

   pilot project update
   removed
   added
   changed


.. code-block:: bash

   pilot project 
   Set project with "pilot project set <myproject>"
     ncipilot1
     ncipilot1-test

   
Setting Your Current Project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO

.. code-block:: bash

   pilot project set ncipilot1-test
   Current project set to ncipilot1-test


.. code-block:: bash

   pilot project 
   Set project with "pilot project set <myproject>"
     ncipilot1
     * ncipilot1-test


Changing Your Current Project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   pilot project set ncipilot1
   Current project set to ncipilot1


.. code-block:: bash

   pilot project 
   Set project with "pilot project set <myproject>"
     * ncipilot1
     ncipilot1-test


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

