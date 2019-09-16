import time
import datetime
import logging

from pilot import config

log = logging.getLogger(__name__)


class TransferLog(config.ConfigSection):

    SECTION = 'transfer_log'
    TRANSFER_LOG_FIELDS = ['dataframe', 'status', 'task_id', 'start_time']

    def _save_log(self, log_id, log_dict):
        if isinstance(log_dict['start_time'], datetime.datetime):
            timestamp = log_dict['start_time'].timestamp()
            log_dict['start_time'] = str(int(timestamp))
        field_list = [log_dict.get(f) for f in self.TRANSFER_LOG_FIELDS]
        log_data = ','.join(field_list)
        self.save_option(str(log_id), log_data)

    def add_log(self, transfer_result, datapath):
        cfg = self.config.load()
        last_id = max([int(i) for i in cfg['transfer_log'].keys()] or [-1])
        log_id = str(last_id + 1)
        log_data = [
            datapath,
            transfer_result.data['code'],
            transfer_result.data['task_id'],
            str(int(time.time()))
        ]
        self._save_log(log_id, dict(zip(self.TRANSFER_LOG_FIELDS, log_data)))
        log.debug('Log saved successfully.')

    def get_log(self):
        cfg = self.config.load()
        if 'transfer_log' not in cfg:
            return []

        logs = []
        for log_id, data in dict(cfg['transfer_log']).items():
            tlog = dict(zip(self.TRANSFER_LOG_FIELDS, data.split(',')))
            tlog['id'] = int(log_id)
            timestamp = int(tlog['start_time'])
            tlog['start_time'] = datetime.datetime.fromtimestamp(timestamp)
            logs.append(tlog)
        logs.sort(key=lambda l: l['id'], reverse=True)
        return logs

    def get_log_by_task(self, task_id):
        for tlog in self.get_log():
            if tlog['task_id'] == task_id:
                return tlog

    def update_log(self, task_id, new_status):
        tlog = self.get_log_by_task(task_id)
        tlog['status'] = new_status
        self._save_log(tlog['id'], tlog)
