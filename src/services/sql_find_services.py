import pyodbc
from typing import List, Dict, Any, Optional

from src.services.config_loader_services import config_loader


class MSSQLConnect:
    def __init__(self):
        self.server = config_loader.get("SQL", "SERVER")
        self.database = config_loader.get("SQL", "DATABASE")
        self.user = config_loader.get("SQL", "UID")
        self.password = config_loader.get("SQL", "PWD")
        self.driver = "ODBC Driver 17 for SQL Server"
        self.conn: Optional[pyodbc.Connection] = None
        self.cursor: Optional[pyodbc.Cursor] = None

    def init(self):
        connection_string = (
            f"DRIVER={self.driver};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.user};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes"
        )
        self.conn = pyodbc.connect(connection_string)
        self.cursor = self.conn.cursor()

    def fetchall(self, SQL: str, params: Optional[List[Any]] = None):
        self.cursor.execute(SQL, params or [])
        return self.cursor.fetchall()

    def close(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
        except Exception as e:
            print(f"Error closing connection: {e}")




class MSSQLProfileFinder:
    def __init__(self, db: MSSQLConnect):
        self.db = db
        self.db.init()

    def find_best_match(self, data: Dict) -> Dict[str, Any]:
        creditor = data.get("Creditor", "")
        account = data.get("AccountNumber", "")
        lastname = data.get("LastName", "")

        SQL = """
            SELECT
                p.ProfileId,
                p.FirstName,
                p.LastName,
                p.Status,
                l.LiabilityId,
                l.AccountNumber,
                l.CurrentAccountNumber,
                orc.Name AS OriginalCreditor,
                crc.Name AS CurrentCreditor
            FROM Profiles p
            LEFT JOIN Liabilities l ON p.ProfileId = l.ProfileId
            LEFT JOIN CreditorMasters orc ON l.OriginalCreditor = orc.CreditorMasterId
            LEFT JOIN CreditorMasters crc ON l.CurrentCreditor = crc.CreditorMasterId
            LEFT JOIN dbo.LiabilityAdditionalStatuses las ON l.LiabilityId = las.LiabilityId
                AND las.AdditionalStatusId = '51DFE423-13EC-42C5-AD77-41BCF7A96CA6'
            WHERE p.Status = 2
                AND las.Value = 'True'
                AND (RIGHT(l.AccountNumber, 4) = ? OR RIGHT(l.CurrentAccountNumber, 4) = ?)
                AND (orc.Name = ? OR crc.Name = ?)
        """

        params = [account, account, creditor, creditor]

        print("\n[DEBUG] Executing SQL with params:")
        print("  Account:", account)
        print("  Creditor:", creditor)
        print("  LastName (filter after):", lastname)

        results = self.db.fetchall(SQL, params)

        print(f"[DEBUG] Found {len(results)} row(s)")
        for r in results:
            print(f"  - ProfileId: {r.ProfileId}, LastName: {r.LastName}, LiabilityId: {r.LiabilityId}")

        if not results:
            return {"Status": 1, "ProfileId": None, "LiabilityId": None}
        elif len(results) == 1:
            row = results[0]
            return {"Status": 2, "ProfileId": row.ProfileId, "LiabilityId": row.LiabilityId}

        filtered = [r for r in results if (r.LastName or '').lower() == lastname.lower()]
        if len(filtered) == 1:
            row = filtered[0]
            return {"Status": 2, "ProfileId": row.ProfileId, "LiabilityId": row.LiabilityId}

        return {"Status": 1, "ProfileId": None, "LiabilityId": None}

    def close(self):
        self.db.close()


def Test():
    # 🔧 Replace these with your test/staging credentials

    print("Initializing DB connection...")
    db = MSSQLConnect()
    finder = MSSQLProfileFinder(db)

    try:
        print("Testing Profile Finder with sample input...\n")
        test_data = {
            "Creditor": "CITIBANK, N.A.",
            "AccountNumber": "3539",
            "LastName": "DOAN"
        }
        result = finder.find_best_match(test_data)
        print("\n✅ Final Result:", result)

    except Exception as e:
        print("❌ Error:", str(e))
    finally:
        finder.close()
        print("Connection closed.")
