import os
import pyodbc
import pandas
import xmltodict
from tqdm import tqdm
from typing import List, Dict, Any
from collections.abc import Iterable
from itertools import chain
import datetime

from db_config import ConnectionString
from data_model import Purchase


def load_terminalid_to_hotspotid_excel(filepath: str) -> Dict[str, str]:
    df = pandas.read_csv(filepath, header=0)
    df.fillna("")
    df["Terminal ID"] = df["Terminal ID"].astype(str)
    df["HotSpot ID"] = df["HotSpot ID"].astype(str)
    terminalid_to_hotspotid = {}

    for i, row in df.iterrows():
        terminalid = row[0].replace(
            "-", "").replace("_", "").replace(" ", "").upper()
        hotspotid = str(row[1]).replace(" ", "")
        if terminalid == "":
            continue
        if terminalid in terminalid_to_hotspotid:
            print("warning: Terminal ID duplicated \"{}\"".format(terminalid))
        terminalid_to_hotspotid[terminalid] = hotspotid

    return terminalid_to_hotspotid


terminalid_to_hotspotid = load_terminalid_to_hotspotid_excel(
    "./data_dump/Terminal ID to HotSpot ID.csv")


def load_flowbird_excel_dump(filepath: str) -> Iterable[str]:
    worksheets = pandas.read_excel(filepath, sheet_name=None)

    unknown_terminalid = set()

    for key in worksheets:
        df = worksheets[key]

        def fill_nan(value): return None if pandas.isna(value) else value
        df = df.applymap(fill_nan)

        for i, row in tqdm(df.iterrows(), total=len(df)):
            purchase = Purchase()
            purchase.set_value("DataSource", "Flowbird Excel Dump")
            purchase.set_value("TerminalID", row[0])
            purchase.set_value("PayUnitName", row[1])

            if type(row[3]) == pandas.Timestamp:
                purchase.set_value("PurchaseDateLocal", row[3].to_pydatetime())
            elif type(row[3]) == datetime.datetime:
                purchase.set_value("PurchaseDateLocal", row[3])
            elif type(row[3]) == str:
                purchase.set_value("PurchaseDateLocal",
                                   pandas.to_datetime(row[3]).to_pydatetime())
            else:
                raise Exception(
                    "can not parse date {} with type {}".format(row[3], type(row[3])))

            purchase.set_value("Amount", row[4])

            if row[0].startswith("HOTSPOT"):
                purchase.set_value("HotspotID", row[0].split(" ")[1])
            else:
                terminalid = row[0].replace(
                    "-", "").replace("_", "").replace(" ", "").upper()
                if terminalid not in terminalid_to_hotspotid:
                    unknown_terminalid.add(row[0])
                purchase.set_value(
                    "HotspotID", terminalid_to_hotspotid.get(terminalid, None))

            yield purchase.get_values()

    if list(unknown_terminalid) != []:
        print("warning: can't find HotspotID for parking lot {}".format(
            str(sorted(list(unknown_terminalid)))))


def load_flowbird_xml_dump(filepath: str) -> Iterable[List[Any]]:
    unknown_terminalid = set()

    data = xmltodict.parse(open(filepath).read())
    for record in tqdm(data["BatchExportRoot"]["Purchases"]["Purchase"]):
        purchase = Purchase()
        purchase.set_value("TerminalID", record["@TerminalID"])
        purchase.set_value("Amount", float(
            record["PurchasePayUnit"]["@Amount"]))
        purchase.set_value("PurchaseDateLocal", pandas.to_datetime(
            record["@PurchaseDateLocal"]).to_pydatetime())
        #purchase.set_value("ArticleName", record["@ArticleName"])
        #purchase.set_value("ArticleID", int(record["@ArticleID"]))
        #purchase.set_value("ExternalID", record["@ExternalID"] if "@ExternalID" in record else None)

        if record["@TerminalID"].startswith("HOTSPOT"):
            purchase.set_value("DataSource", "Flowbird API - HotSpot")
            purchase.set_value("PayUnitName", "HotSpot")
            purchase.set_value(
                "HotspotID", record["@TerminalID"].split(" ")[1])
        else:
            purchase.set_value("DataSource", "Flowbird API - PreciseLink")
            purchase.set_value(
                "PayUnitName", record["PurchasePayUnit"]["@PayUnitName"])
            terminalid = record["@TerminalID"].replace(
                "-", "").replace("_", "").replace(" ", "").upper()
            if terminalid not in terminalid_to_hotspotid:
                unknown_terminalid.add(record["@TerminalID"])
            purchase.set_value(
                "HotspotID", terminalid_to_hotspotid.get(terminalid, None))

        yield purchase.get_values()

    if list(unknown_terminalid) != []:
        print("warning: can't find HotspotID for parking lot {}".format(
            str(sorted(list(unknown_terminalid)))))


def load_hotspot_excel_dump(filepath: str) -> Iterable[List[Any]]:
    worksheets = pandas.read_excel(filepath, sheet_name=None)

    for key in worksheets:
        df = worksheets[key]

        def fill_nan(value): return None if pandas.isna(value) else value
        df = df.applymap(fill_nan)

        for i, row in tqdm(df.iterrows(), total=len(df)):
            if i == 0:
                continue
            purchase = Purchase()
            purchase.set_value("DataSource", "HotSpot Excel Dump")
            purchase.set_value("HotspotID", str(row[0]))
            purchase.set_value("TerminalID", row[1][0:50])
            purchase.set_value("PayUnitName", "HotSpot")
            purchase.set_value("Amount", float(row[6]))

            if type(row[2]) == pandas.Timestamp:
                purchase.set_value("PurchaseDateLocal", row[2].to_pydatetime())
            elif type(row[2]) == datetime.datetime:
                purchase.set_value("PurchaseDateLocal", row[2])
            elif type(row[2]) == str:
                purchase.set_value("PurchaseDateLocal",
                                   pandas.to_datetime(row[2]).to_pydatetime())
            else:
                raise Exception(
                    "can not parse date {} with type {}".format(row[2], type(row[2])))

            yield purchase.get_values()


def load_mackay_excel_dump(filepath: str) -> Iterable[List[Any]]:
    worksheets = pandas.read_excel(filepath, sheet_name=None, header=None)

    postid_to_hotspotid = {}

    mapping_df = worksheets["Mapping"]
    for i, row in mapping_df.iterrows():
        postid_to_hotspotid[str(row[0])] = str(row[5])

    for key in worksheets:
        if key == "Mapping":
            continue

        df = worksheets[key]

        def fill_nan(value): return None if pandas.isna(value) else value
        df = df.applymap(fill_nan)

        for i, row in tqdm(df.iterrows(), total=len(df)):
            if i <= 3:
                continue

            purchase = Purchase()
            purchase.set_value(
                "DataSource", "Mackay Paystation & Beacon Excel Dump")
            purchase.set_value("HotspotID", postid_to_hotspotid[str(row[0])])
            purchase.set_value("TerminalID", str(row[0]))

            if row[10] == "Visa" or row[10] == "Mastercard":
                purchase.set_value("PayUnitName", "Card")
            elif row[10] == "Coin":
                purchase.set_value("PayUnitName", "Coin")
            else:
                print("warning: unknown purchase type: {}".format(row[10]))

            if row[11] is None:
                print("warning: Amount value is None")
                continue
            purchase.set_value("Amount", float(row[11]))

            if type(row[7]) == pandas.Timestamp:
                purchase.set_value("PurchaseDateLocal", row[7].to_pydatetime())
            elif type(row[7]) == datetime.datetime:
                purchase.set_value("PurchaseDateLocal", row[7])
            elif type(row[7]) == str:
                purchase.set_value("PurchaseDateLocal",
                                   pandas.to_datetime(row[7]).to_pydatetime())
            else:
                raise Exception(
                    "can not parse date {} with type {}".format(row[7], type(row[7])))

            yield purchase.get_values()


def load_mackay_coin_meter_data(filepath: str) -> Iterable[List[Any]]:
    df = pandas.read_excel(filepath, sheet_name=0, header=None)

    def fill_nan(value): return None if pandas.isna(value) else value
    df = df.applymap(fill_nan)

    for i, row in tqdm(df.iterrows(), total=len(df)):
        purchase = Purchase()
        purchase.set_value("DataSource", "Mackay Coin Meter Excel Dump")
        purchase.set_value("HotspotID", str(row[1]))
        purchase.set_value("TerminalID", row[2].split("(")[0].strip())
        purchase.set_value("PayUnitName", "Coin")

        if row[3] is None:
            print("warning: Amount value is None")
            continue
        purchase.set_value("Amount", float(row[3]))

        if type(row[0]) == pandas.Timestamp:
            purchase.set_value("PurchaseDateLocal", row[0].to_pydatetime())
        elif type(row[0]) == datetime.datetime:
            purchase.set_value("PurchaseDateLocal", row[0])
        elif type(row[0]) == str:
            purchase.set_value("PurchaseDateLocal",
                               pandas.to_datetime(row[0]).to_pydatetime())
        else:
            raise Exception(
                "can not parse date {} with type {}".format(row[0], type(row[0])))

        yield purchase.get_values()


def bulk_insert(records: List[Any], bulk_size=10000):
    conn = pyodbc.connect(ConnectionString)
    cursor = conn.cursor()
    cursor.fast_executemany = True
    sql_cmd_temp = "insert into Purchases values ({})".format(
        ",".join(["?"]*len(Purchase.fields)))

    print("inserting records...")
    pbar = tqdm(total=len(records))

    for i in range(0, len(records), bulk_size):
        bulk_data = records[i:i+bulk_size]
        cursor.executemany(sql_cmd_temp, bulk_data)
        pbar.update(len(bulk_data))

    pbar.close()

    print("commiting...")
    cursor.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":

    # load flowbird data
    # """
    records = list(load_flowbird_excel_dump(
        "./data_dump/FlowBird Parking Data 2018 - 2021.xlsx"))
    bulk_insert(records)
    # """

    # """
    filepaths = list(map(lambda path: os.path.join(
        "./data_dump", path), os.listdir("./data_dump")))
    filepaths = list(filter(lambda x: os.path.splitext(x)
                     [-1] == ".xml", filepaths))
    records = list(chain(
        *list(map(lambda x: list(load_flowbird_xml_dump(x)), filepaths))
    ))
    bulk_insert(records)
    # """

    # load hotspot data
    # """
    records = list(load_hotspot_excel_dump(
        "./data_dump/HotSpot Data 2021.xlsx"))
    bulk_insert(records)
    # """

    # load mackay data
    # """
    records = list(load_mackay_excel_dump(
        "./data_dump/Mackay Data 2018-2021.xlsx"))
    bulk_insert(records)
    # """

    # load mackay coin meter data
    # """
    records = list(load_mackay_coin_meter_data(
        "./data_dump/Mackay Coin Meter Data 2018-2021.xlsx"))
    bulk_insert(records)
    # """
