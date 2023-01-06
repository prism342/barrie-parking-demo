import re
from typing import Optional, Any, List
import datetime 
import pandas

class Purchase:
    fields = [
        "HotspotID",
        "TerminalID",
        "PurchaseDateLocal",
        "Amount",
        "PayUnitName",
        "DataSource"
        ]

    dtypes = {
        "PurchaseGuid": "char(36)",
        "TerminalGuid": "char(36)",
        "TerminalID": "char(50)",
        "PurchaseDateLocal": "DATETIME",
        "PurchaseDateUtc": "DATETIME",
        "StartDateLocal": "DATETIME",
        "StartDateUtc": "DATETIME",
        "PayIntervalStartLocal": "DATETIME",
        "PayIntervalStartUtc": "DATETIME",
        "PayIntervalEndLocal": "DATETIME",
        "PayIntervalEndUtc": "DATETIME",
        "EndDateLocal": "DATETIME",
        "EndDateUtc": "DATETIME",
        "TicketNumber": "int",
        "Units": "int",
        "Amount": "float",
        "VAT": "float",
        "CurrencyCode": "char(3)",
        "TariffPackageID": "int",
        "ArticleID": "int",
        "ArticleName": "char(50)",
        "ExternalID": "char(50)",
        "DateCreatedUtc": "DATETIME",
        "PurchaseStateName": "char(50)",
        "PaymentServiceType": "char(50)",
        "PurchaseTriggerTypeName": "char(50)",
        "PurchaseTypeName": "char(50)",
        "PayUnitID": "int",
        "PayUnitName": "char(59)",
        "TotalAmount": "float",
        "HotspotID":"char(8)",
        "DataSource":"char(50)"
    }

    @staticmethod
    def build_create_table_cmd():
        cmd = "CREATE TABLE Purchases({});".format(
            ", ".join(list(map(lambda name:"{} {}".format(name, Purchase.dtypes[name]), Purchase.fields))))
        return cmd

    def __init__(self):
        self.data = dict(zip(self.fields, [None for i in self.fields]))

    def check_type(self, fieldname: str, value: Any):
        fieldtype = self.dtypes[fieldname]

        string_type_pattern = re.compile(r"^char\(\d+\)$")

        if fieldtype == "int":
            return type(value) is int
        elif fieldtype == "float":
            return type(value) is float
        elif fieldtype == "DATETIME":
            return type(value) is datetime.datetime
        elif string_type_pattern.match(fieldtype) is not None:
            string_size = int(fieldtype[5:-1])
            return type(value) is str and len(value) <= string_size
        else:
            print("checking fieldtype {} is not implemented".format(fieldtype))
            raise NotImplementedError()

    def build_insert_cmd(self):
        cmd = "INSERT INTO Purchases ({}) VALUES ({});"
        fields_str = ",".join(self.fields)
        values_list = list(map(lambda value: "'{}'".format(
            value) if type(value) is str else "NULL", self.data.values()))
        values_str = ",".join(values_list)
        return cmd.format(fields_str, values_str)

    def set_value(self, field: str, value: Optional[str]):
        assert(field in self.data)

        if value is None:
            return

        assert(self.check_type(field, value))
        self.data[field] = value

    def get_values(self) -> List[Any]:
        return list(map(lambda item:item[1], sorted(self.data.items(), key=lambda x:self.fields.index(x[0]))))
