
Projects
--------

This is guide to using ``pilot`` to create and manage projects and the datasets associated with them.

Prerequisites
^^^^^^^^^^^^^

You should review the `User Guide
<https://github.com/globusonline/pilot1-tools/blob/master/docs/user-guide.rst>`_ for:

- installing and configuring ``pilot``
- listing and downloading files

What is a Project?
^^^^^^^^^^^^^^^^^^

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