pilot1-tools Developer Guide
============================

.. contents:: Table of Contents

Introduction
------------

This guide includes general instructions for more advanced users that may not
be necessary for users or admins.

Installation
------------

There are a couple of different options. You can either install the latest stable
version on Conda, or the latest development changes from github.


Conda
~~~~~

These tools are available on Conda for Python 3.6, you can install them with the following:

.. code-block:: bash

    conda create -n pilot1-env -c conda-forge -c nickolaussaint pilot1-tools


Github
~~~~~~

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