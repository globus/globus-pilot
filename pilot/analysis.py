import pandas
import numpy
import tableschema


FOREIGN_KEYS = {
    'DRUG_ID': {
        'fields': ['DRUG_ID'],
        'reference': {
            'filename': 'drugs',
            'resource': 'globus://ebf55996-33bf-11e9-9fa4-0a06afd4a22e:'
                        '/restricted/dataframes/metadata/drugs',
            'fields': 'ID'
            }
        },
    'CELLNAME': {
        'fields': ['CELLNAME'],
        'reference': {
            'filename': 'celllines',
            'resource': 'globus://ebf55996-33bf-11e9-9fa4-0a06afd4a22e:'
                        '/restricted/dataframes/metadata/celllines',
            'fields': 'sample_name'
            }
        },
    'Sample': {
        'fields': ['Sample'],
        'reference': {
            'filename': 'celllines',
            'resource': 'globus://ebf55996-33bf-11e9-9fa4-0a06afd4a22e:'
                        '/restricted/dataframes/metadata/celllines',
            'fields': 'sample_name'
            }
        }
    }


def get_preview_byte_count(filename, num_rows=11):
    """Count and return number of bytes for the first 11 rows in the given
    filename. Useful for preview."""
    with open(filename) as fp:
        return sum([len(fp.readline()) for x in range(num_rows)])


def get_pandas_field_metadata(pandas_col_metadata, field_name):
    """
    Fetch information for a given column. The column statistics returned
    will be a bit different depending on if the types in the column are a
    number or a string. 'NAN' values are stripped from statistics and don't
    even show up in output.
    """
    pmeta = pandas_col_metadata.get(field_name)
    metadata = {
        'name': field_name,
        'type': 'string' if str(pmeta.dtype) == 'object' else str(pmeta.dtype),

        # numerical statistics
        '25': pmeta['25%'],
        '50': pmeta['50%'],
        '75': pmeta['75%'],
        'mean': pmeta['mean'],
        'std': pmeta['std'],
        'min': pmeta['min'],
        'max': pmeta['max'],

        # string/object  statistics
        'count': int(pmeta['count']),
        'unique': pmeta['unique'],
        'top': pmeta['top'],
        'frequency': pmeta['freq'],
    }
    # Remove all NAN values
    cleaned_metadata = {k: v for k, v in metadata.items()
                        if isinstance(v, str) or not numpy.isnan(v)}
    return cleaned_metadata


def get_foreign_key(column):
    ref = FOREIGN_KEYS.get(column['name'], {}).get('reference') or None
    return {'reference': ref}


def analyze_dataframe(filename):
    # Pandas analysis
    df = pandas.read_csv(filename, sep='\t')
    pandas_info = df.describe(include='all')
    # Tableschema analysis
    ts_info = tableschema.Schema(tableschema.infer(filename)).descriptor

    column_metadata = []
    for column in ts_info['fields']:
        df_metadata = column.copy()
        col_name = column['name']
        df_metadata.update(get_pandas_field_metadata(pandas_info, col_name))
        df_metadata.update(get_foreign_key(column))
        column_metadata.append(df_metadata)

    dataframe_metadata = {
        'name': 'Data Dictionary',
        # df.shape[0] seems to have issues determining rows
        'numrows': len(df.index),
        'numcols': df.shape[1],
        'previewbytes': get_preview_byte_count(filename),
        'field_definitions': column_metadata,
        'labels': {
            'name': 'Column Name',
            'type': 'Data Type',
            'format': 'Format',
            'count': 'Number of non-null entries',
            '25': '25th Percentile',
            '50': '50th Percentile',
            '75': '75th Percentile',
            'std': 'Standard Deviation',
            'mean': 'Mean Value',
            'min': 'Minimum Value',
            'max': 'Maximum Value',
            'unique': 'Unique Values',
            'top': 'Top Common',
            'frequency': 'Frequency of Top Common Value',
            'reference': 'Link to resource definition'
        }
    }
    return dataframe_metadata
