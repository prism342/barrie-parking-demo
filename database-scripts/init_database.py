from db_config import ConnectionString
import pyodbc
import data_model

cnxn = pyodbc.connect(ConnectionString)

cursor = cnxn.cursor()

# print all tables exists
result = cursor.execute(
    "SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'").fetchall()

print(result)

# drop table
cursor.execute(
    """IF OBJECT_ID('dbo.Purchases', 'U') IS NOT NULL 
    DROP TABLE dbo.Purchases; 
    """)

# unified schema
cursor.execute(data_model.Purchase.build_create_table_cmd())

# print all tables exists
result = cursor.execute(
    "SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'").fetchall()

print(result)

cnxn.commit()
