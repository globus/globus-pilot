from tests.unit.mocks import GlobusTransferTaskResponse
from pilot.transfer_log import TransferLog


def test_add_transfer_log(mock_config):
    tl = TransferLog(mock_config)
    cfg = tl.config.load()
    assert cfg['transfer_log'] == {}
    assert tl.get_log() == []
    gccr = GlobusTransferTaskResponse()
    tl.add_log(gccr, 'foo/bar')
    assert cfg['transfer_log'] != {}
    assert list(cfg['transfer_log'].keys()) == ['0']
    assert cfg['transfer_log']['0'] is not None


def test_get_transfer_log(mock_config):
    tl = TransferLog(mock_config)
    gccr = GlobusTransferTaskResponse()
    tl.add_log(gccr, 'foo/bar')

    tlog = tl.get_log()
    assert len(tlog) == 1
    mylog = tlog[0]
    assert set(mylog.keys()) == {'dataframe', 'id', 'task_id',
                                 'start_time', 'status'}


def test_update_transfer_log(mock_config):
    tl = TransferLog(mock_config)
    gccr = GlobusTransferTaskResponse()
    tl.add_log(gccr, 'foo/bar')
    tl.update_log(gccr.data['task_id'], 'complete')
    tlog = tl.get_log_by_task(gccr.data['task_id'])
    assert tlog['status'] == 'complete'
