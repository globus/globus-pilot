pilot1-tools Reference
======================

.. contents:: Table of Contents


Metadata
--------

Datacite Metadata
~~~~~~~~~~~~~~~~~

Here is a list of supported Datacite fields you can modify for your file.

.. code-block:: json

    {
      "description":
        "This is tabular skewt data showing air above Chicago on July 12th, from ground level to 100,000 feet.",
      "creators": [{"creatorName": "NOAA"}],
      "publisher": "NOAA",
      "title": "Raw tabular data for skewt plot of air above Chicago",
      "subjects": [{"subject": "skewt"}, {"subject": "chicago"}],
      "publicationYear": "2019",
      "resourceType": {
        "resourceType": "Dataset",
        "resourceTypeGeneral": "Dataset"
      }
    }

Example my_metadata.json:

.. code-block:: json

    {
        "description": "This is tabular data for a skewt plot.",
        "creators": [{"creatorName": "NOAA"}]
    }

``pilot upload -j my_metadata.json myfile.csv /``

This will upload myfile.csv with a description and custom creator.


Project Metadata
~~~~~~~~~~~~~~~~

Project Metadata can be added when uploading to enrich your search results and make them
more discoverable to users of your project.

Here are an example of supported fields which can be added to your project:

.. code-block:: json

    "data_type": {
        "type": "string",
        "description" : "Data category, such as 'Metadata' or 'Physics Experiment'"
                    },
    "dataframe_type": {
        "type": "string",
        "enum": ["List", "Matrix"],
        "description" : "Dataframe structure, matrix or list"
    },
    "x-label": {
        "type": "string",
        "description": "X-label, if the dataframe_type is Matrix"
    },
    "y-label": {
        "type": "string",
        "description": "Y-label, if the dataframe_type is Matrix"
    },
    "units": {
        "type": "integer",
        "description": "Units or scale (e.g., log, log10) of the data."
    },
    "source": {
        "type": "array",
        "description": "The source data repositories.",
        "items": {
            "type": "string",
            "description": "One repository."
        }
    }

Example my_metadata.json:

.. code-block:: json

    {
        "data_type": "Metadata",
        "dataframe_type": "List,
    }

``pilot upload -j my_metadata.json myfile.txt /``

This will upload myfile.txt with additional metadata.