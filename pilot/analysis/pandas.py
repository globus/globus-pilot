import logging
import pandas as pd
import numpy
import tableschema
import tabulator.exceptions


log = logging.getLogger(__name__)


TSV_LABELS = {
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


def analyze_tsv(filename):
    metadata = analyze(pd.read_csv(filename, sep='\t'))
    metadata = add_extended_metadata(filename, metadata)
    return metadata


def analyze_csv(filename):
    metadata = analyze(pd.read_csv(filename))
    metadata = add_extended_metadata(filename, metadata)
    return metadata


def analyze_parquet(filename):
    return analyze(pd.read_parquet(filename))


def analyze_feather(filename):
    return analyze(pd.read_feather(filename))


def analyze_hdf(filename):
    log.debug('Analyzing hdf5!')
    store = pd.HDFStore(filename, 'r')
    analyses = []
    for key in store.keys():
        try:
            if len(key.lstrip('/').split('/')) > 1:
                # Ignore any nested items in the store
                log.debug('Skipping {}'.format(key))
                continue
            log.info('Analyzing HDF key: {}'.format(key))
            dataframe = store.get(key)
            if isinstance(dataframe, pd.Series):
                dataframe = pd.DataFrame({key.lstrip('/'): dataframe})
            analysis = analyze(dataframe)
            analysis['store_key'] = key
            analyses.append(analysis)
        except Exception as e:
            log.exception(e)
            log.error('Error processing key {}'.format(key))
    store.close()
    return analyses


def analyze(pd_dataframe):
    pandas_info = pd_dataframe.describe(include='all')

    column_metadata = []
    for column in pd_dataframe.columns.tolist()[:10]:
        # df_metadata = column.copy()
        # col_name = column['name']
        df_metadata = {'name': column}
        df_metadata.update(get_pandas_field_metadata(pandas_info, column))
        column_metadata.append(df_metadata)

    dataframe_metadata = {
        'name': 'Data Dictionary',
        # df.shape[0] seems to have issues determining rows
        'numrows': len(pd_dataframe.index),
        'numcols': pd_dataframe.shape[1],
        'field_definitions': column_metadata,
        'labels': TSV_LABELS
    }
    return dataframe_metadata


def add_extended_metadata(filename, metadata):
    """Update the given metadata dict with additional tableschema metadata.
    This is only available for files that can be read by tableschema, which are
    only tsvs and csvs. Tableschema doesn't add much, but it could be handy
    if it can detect extended types like locations."""
    metadata['previewbytes'] = get_preview_byte_count(filename)
    try:
        ts_info = tableschema.Schema(tableschema.infer(filename)).descriptor

        new_field_definitions = []
        for m, ts in zip(metadata['field_definitions'], ts_info['fields']):
            m['format'] = ts['format']
            new_field_definitions.append(m)
        metadata['field_definitions'] = new_field_definitions
    except tabulator.exceptions.FormatError:
        pass
    return metadata


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
    # Pandas may return numpy.nan for statistics below, or nothing at all.
    # ALL possibly missing values are treated as NAN values and stripped at
    # the end.
    metadata = {
        'name': field_name,
        'type': 'string' if str(pmeta.dtype) == 'object' else str(pmeta.dtype),
        'count': int(pmeta['count']),
        'top': pmeta.get('top', numpy.nan),

        # string statistics
        'unique': pmeta.get('unique', numpy.nan),
        'frequency': pmeta.get('freq', numpy.nan),

        # numerical statistics
        '25': pmeta.get('25%', numpy.nan),
        '50': pmeta.get('50%', numpy.nan),
        '75': pmeta.get('75%', numpy.nan),
        'mean': pmeta.get('mean', numpy.nan),
        'std': pmeta.get('std', numpy.nan),
        'min': pmeta.get('min', numpy.nan),
        'max': pmeta.get('max', numpy.nan),
    }

    # Remove all NAN values
    cleaned_metadata = {k: v for k, v in metadata.items()
                        if isinstance(v, str) or not numpy.isnan(v)}

    # Pandas has special types for things. Coerce them to be regular
    # ints and floats
    for name in ['25', '50', '75', 'mean', 'std', 'min', 'max']:
        if name in cleaned_metadata:
            cleaned_metadata[name] = float(cleaned_metadata[name])
    for name in ['count', 'unique', 'frequency']:
        if name in cleaned_metadata:
            cleaned_metadata[name] = int(cleaned_metadata[name])
    return cleaned_metadata
