from tests.unit.mocks import GlobusTransferTaskResponse


def test_add_transfer_log(mock_config):
    assert mock_config.get_transfer_log() == []
    gccr = GlobusTransferTaskResponse()
    mock_config.add_transfer_log(gccr, 'foo/bar')
    assert mock_config.data['transfer_log'] != {}
    assert list(mock_config.data['transfer_log'].keys()) == ['0']
    assert mock_config.data['transfer_log']['0'] is not None


def test_get_transfer_log(mock_config):
    gccr = GlobusTransferTaskResponse()
    mock_config.add_transfer_log(gccr, 'foo/bar')

    tlog = mock_config.get_transfer_log()
    assert len(tlog) == 1
    mylog = tlog[0]
    assert set(mylog.keys()) == {'dataframe', 'id', 'task_id',
                                 'start_time', 'status'}


def test_update_transfer_log(mock_config):
    gccr = GlobusTransferTaskResponse()
    mock_config.add_transfer_log(gccr, 'foo/bar')
    mock_config.update_transfer_log(gccr.data['task_id'], 'complete')
    tlog = mock_config.get_transfer_log_by_task(gccr.data['task_id'])
    assert tlog['status'] == 'complete'
