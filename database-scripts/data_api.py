import xmltodict
import requests
from requests.auth import HTTPBasicAuth

import time
from datetime import datetime, timedelta
import os
import pytz


def get_dates(delta_weeks=0):
    today = datetime.utcnow()
    today += timedelta(weeks=delta_weeks)
    this_monday = today - timedelta(days=today.weekday())
    last_monday = this_monday - timedelta(days=7)

    return last_monday.strftime('%Y-%m-%d'), this_monday.strftime('%Y-%m-%d')


def precise_parklink_fetch_data(start_date: str, end_date: str):
    # Precise ParkLink
    # request to export
    request_export_url = "https://webservice.mdc.dmz.caleaccess.com/cwo2exportservice/BatchDataExport/3/BatchDataExport.svc/purchase/ticket/{}/{}".format(
        start_date, end_date)
    response = requests.get(
        request_export_url, auth=HTTPBasicAuth('username', 'password'))

    assert(response.ok)

    export_status_url = xmltodict.parse(
        response.text)["BatchDataExportResponse"]["Url"]
    export_guid = None
    export_file_url = None

    # exporting
    while True:
        response = requests.get(
            export_status_url, auth=HTTPBasicAuth('username', 'password'))
        assert(response.ok)

        response_data = xmltodict.parse(response.text)
        export_status = response_data["BatchDataExportFileResponse"]["ExportStatus"]

        if export_status == "Requested":
            time.sleep(2)
        elif export_status == "Processed":
            export_guid = response_data["BatchDataExportFileResponse"]["DataExportGuid"]
            export_file_url = response_data["BatchDataExportFileResponse"]["Url"]
            break
        else:
            raise Exception(export_status)

    # download data
    response = requests.get(
        export_file_url, auth=HTTPBasicAuth('username', 'password'))

    open(os.path.join("./data_dump", export_guid+".zip"),
         'wb').write(response.content)

    # unzip file
    dump_dir = "./data_dump"
    dump_filepath = os.path.join(dump_dir, export_guid+".zip")
    status = os.system("unzip {} -d {}".format(dump_filepath, dump_dir))

    assert(status == 0)

    time.sleep(0.5)

    os.remove(dump_filepath)

    return os.path.splitext(dump_filepath)[0] + ".xml"


if __name__ == "__main__":
    #print(*get_dates(delta_weeks=1))
    #precise_parklink_fetch_data(*get_dates(delta_weeks=1))
    pass