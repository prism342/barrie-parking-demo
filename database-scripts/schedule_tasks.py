import time
from data_api import get_dates, precise_parklink_fetch_data
from bulk_insert_data_dump import load_flowbird_xml_dump, bulk_insert
import schedule


def task():
    data_filepath = precise_parklink_fetch_data(*get_dates())
    records = list(load_flowbird_xml_dump(data_filepath))
    bulk_insert(records)


schedule.every().monday.at("02:00").do(task)

while True:
    schedule.run_pending()
    time.sleep(1)
