import pyodbc
from typing import List, Dict, Any, Optional, Callable

from src.services.config_loader_services import config_loader

# SQL Connection 
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

# Profile Finder Class
# Flow: Initialize MSSQL Connect --> Initialize MSSQLProfileFinder --> find_best_match: querry by account number --> filter by last name and first name 
#  --> resolve by priority --> return profile and liability information --> if not found, find_ssn --> query by last 4 ssn --> filter by last name and first name 
# --> resolve by priority --> return profile and liability information --> Close connection
class MSSQLProfileFinder:
    def __init__(self, db: MSSQLConnect):
        self.db = db
        self.db.init()

    # Resolve by priority based on Profile status
    def resolve_by_priority(self, matches: List[Any], data: Dict) -> Dict[str, Any]:
        PRIORITY_1 = {1, 2, 3, 4, 6, 7, 10}
        PRIORITY_2 = {0, 9}
        PRIORITY_3 = {5, 8}

        def priority_group(status):
            if status in PRIORITY_1:
                return 1
            elif status in PRIORITY_2:
                return 2
            else:
                return 3

        grouped = sorted(matches, key=lambda r: priority_group(r.Status))
        top_group = [r for r in grouped if priority_group(r.Status) == priority_group(grouped[0].Status)]

        if len(top_group) == 1:
            r = top_group[0]
            return {"Status": 2, "ProfileId": r.ProfileId, "LiabilityId": getattr(r, "LiabilityId", None)}

        profile_ids = set(r.ProfileId for r in top_group)
        if len(profile_ids) == 1:
            enrolled_match = next((r for r in top_group if r.Status == 2), None)
            if enrolled_match:
                return {"Status": 2, "ProfileId": enrolled_match.ProfileId, "LiabilityId": getattr(enrolled_match, "LiabilityId", None)}
            else:
                same_statuses = set (r.Status for r in top_group)
                if len(same_statuses) == 1:
                    return {"Status":2, "ProfileId": top_group[0].ProfileId, "LiabilityId": None}

        return {"Status": 1, "ProfileId": None, "LiabilityId": None}

    # Filter by last name and first name then resolve by priority
    def filter_and_resolve(self, records: List[Any], field_filters: List[tuple], fallback: Callable) -> Dict[str, Any]:
        print(f"[DEBUG] Found {len(records)} row(s)")
        for r in records:
            print(f"  - ProfileId: {getattr(r, 'ProfileId', None)}, FirstName: {getattr(r, 'FirstName', '')}, LastName: {getattr(r, 'LastName', '')}, Status: {getattr(r, 'Status', None)}")

        if not records:
            return fallback()
        if len(records) == 1:
            r = records[0]
            return {"Status": 2, "ProfileId": r.ProfileId, "LiabilityId": getattr(r, "LiabilityId", None)}

        filtered = records
        for field_name, expected_value in field_filters:
            expected_value_lower = (expected_value or "").lower()
            filtered = [
                r for r in filtered
                if (getattr(r, field_name, '') or '').lower() == expected_value_lower
            ]
            print(f"[DEBUG] After filtering by {field_name}, {len(filtered)} row(s) remain")
            for r in filtered:
                print(f"  - ProfileId: {r.ProfileId}, {field_name}: {getattr(r, field_name, '')}, Profile Status: {getattr(r, 'Status', '')}")
            if len(filtered) == 1:
                r = filtered[0]
                return {"Status": 2, "ProfileId": r.ProfileId, "LiabilityId": getattr(r, "LiabilityId", None)}

        ssns = {getattr(r, "SSN", None) for r in filtered}
        if len(filtered) >= 2 and len(ssns) == 1:
            return self.resolve_by_priority(filtered, {})

        return fallback()

    def find_best_match(self, data: Dict) -> Dict[str, Any]:
        return self.find_reference_number(data)

    def find_reference_number(self, data: Dict) -> Dict[str, Any]:
        reference_number = data.get("ReferenceNumber", "")
        lastname = data.get("LastName", "")
        firstname = data.get("FirstName", "")

        if not reference_number.strip():
            return self.find_file_number(data)

        SQL = """
            SELECT
                p.ProfileId,
                l.LiabilityId,
                p.FirstName,
                p.LastName,
                p.SSN,
                p.Status,
                l.Enrolled
            FROM Profiles p
            LEFT JOIN Liabilities l ON p.ProfileId = l.ProfileId
            WHERE l.Active = 1
                AND (l.AccountNumber = ? OR l.CurrentAccountNumber = ?)
        """

        params = [reference_number, reference_number]

        results = self.db.fetchall(SQL, params)

        return self.filter_and_resolve(
            results,
            field_filters=[("LastName", lastname), ("FirstName", firstname)],
            fallback=lambda: self.find_file_number(data)
        )

    def find_file_number(self, data: Dict) -> Dict[str, Any]:
        file_number = data.get("FileNumber", "")
        lastname = data.get("LastName", "")
        firstname = data.get("FirstName", "")

        if not file_number.strip():
            return self.find_full_account_numbers(data)
        
        SQL = """
            SELECT
                p.ProfileId,
                l.LiabilityId,
                p.FirstName,
                p.LastName,
                p.SSN,
                p.Status,
                l.Enrolled
            FROM Profiles p
            LEFT JOIN Liabilities l ON p.ProfileId = l.ProfileId
            WHERE l.Active = 1
                AND (l.AccountNumber = ? OR l.CurrentAccountNumber = ?)
        """

        params = [file_number, file_number]

        results = self.db.fetchall(SQL, params)

        return self.filter_and_resolve(
            results,
            field_filters=[("LastName", lastname), ("FirstName", firstname)],
            fallback=lambda: self.find_full_account_numbers(data)
        )

    
    def find_full_account_numbers(self, data: Dict) -> Dict[str, Any]:
        full_account_number = data.get("FullAccountNumber", "")
        lastname = data.get("LastName", "")
        firstname = data.get("FirstName", "")

        if not full_account_number.strip():
            return self.find_last4_account_number(data)
        
        SQL = """
            SELECT
                p.ProfileId,
                l.LiabilityId,
                p.FirstName,
                p.LastName,
                p.SSN,
                p.Status,
                l.Enrolled
            FROM Profiles p
            LEFT JOIN Liabilities l ON p.ProfileId = l.ProfileId
            WHERE l.Active = 1
                AND (l.AccountNumber = ? OR l.CurrentAccountNumber = ?)
        """

        params = [full_account_number, full_account_number]

        results = self.db.fetchall(SQL, params)

        return self.filter_and_resolve(
            results,
            field_filters=[("LastName", lastname), ("FirstName", firstname)],
            fallback=lambda: self.find_last4_account_number(data)
        )

    def find_last4_account_number(self, data: Dict) -> Dict[str, Any]:
        last4_account_number = data.get("Last4AccountNumber", "")
        lastname = data.get("LastName", "")
        firstname = data.get("FirstName", "")

        if not last4_account_number.strip():
            return self.find_first12_account_number(data)

        SQL = """
            SELECT
                p.ProfileId,
                l.LiabilityId,
                p.FirstName,
                p.LastName,
                p.SSN,
                p.Status,
                l.Enrolled
            FROM Profiles p
            LEFT JOIN Liabilities l ON p.ProfileId = l.ProfileId
            WHERE l.Active = 1
                AND (RIGHT(l.AccountNumber, 4) = ? OR RIGHT(l.CurrentAccountNumber, 4) = ?)
        """

        params = [last4_account_number, last4_account_number]

        results = self.db.fetchall(SQL, params)

        return self.filter_and_resolve(
            results,
            field_filters=[("LastName", lastname), ("FirstName", firstname)],
            fallback=lambda: self.find_first12_account_number(data)
        )

    def find_first12_account_number(self, data: Dict) -> Dict[str, Any]:
        first12_account_number = data.get("First12AccountNumber", "")
        lastname = data.get("LastName", "")
        firstname = data.get("FirstName", "")

        if not first12_account_number.strip():
            return self.find_first8_account_number(data)

        SQL = """
            SELECT
                p.ProfileId,
                l.LiabilityId,
                p.FirstName,
                p.LastName,
                p.SSN,
                p.Status,
                l.Enrolled
            FROM Profiles p
            LEFT JOIN Liabilities l ON p.ProfileId = l.ProfileId
            WHERE l.Active = 1
                AND (LEFT(l.AccountNumber, 12) = ? OR LEFT(l.CurrentAccountNumber, 12) = ?)
        """

        params = [first12_account_number, first12_account_number]

        results = self.db.fetchall(SQL, params)

        return self.filter_and_resolve(
            results,
            field_filters=[("LastName", lastname), ("FirstName", firstname)],
            fallback=lambda: self.find_first8_account_number(data)
        )
    
    def find_first8_account_number(self, data: Dict) -> Dict[str, Any]:
        first8_account_number = data.get("First8AccountNumber", "")
        lastname = data.get("LastName", "")
        firstname = data.get("FirstName", "")

        if not first8_account_number.strip():
            return self.find_email(data)

        SQL = """
            SELECT
                p.ProfileId,
                l.LiabilityId,
                p.FirstName,
                p.LastName,
                p.SSN,
                p.Status,
                l.Enrolled
            FROM Profiles p
            LEFT JOIN Liabilities l ON p.ProfileId = l.ProfileId
            WHERE l.Active = 1
                AND (LEFT(l.AccountNumber, 8) = ? OR LEFT(l.CurrentAccountNumber, 8) = ?)
        """

        params = [first8_account_number, first8_account_number]

        results = self.db.fetchall(SQL, params)

        return self.filter_and_resolve(
            results,
            field_filters=[("LastName", lastname), ("FirstName", firstname)],
            fallback=lambda: self.find_email(data)
        )   
    
    def find_email(self, data: Dict) -> Dict[str, Any]:
        email = data.get("Email", "")
        lastname = data.get("LastName", "")
        firstname = data.get("FirstName", "")

        if not email.strip():
            return self.find_ssn(data)

        SQL = """
            SELECT
                p.ProfileId,
                p.FirstName,
                p.LastName,
                p.LAST4SSN,
                p.SSN,
                p.Status
            FROM Profiles p
            LEFT JOIN ProfileContacts pc on p.ProfileId = pc.ProfileId
                AND pc.ContactId = 'E956B381-E501-4CF0-9C9E-CB32DAF52940'
            WHERE (pc.Email like ?)
        """

        params = [f"%{email}%"]

        results = self.db.fetchall(SQL, params)

        return self.filter_and_resolve(
            results,
            field_filters=[("LastName", lastname), ("FirstName", firstname)],
            fallback=lambda: self.find_ssn(data)
        )

    def find_ssn(self, data: Dict) -> Dict[str, Any]:
        last4ssn = data.get("Last4SSN", "")
        lastname = data.get("LastName", "")
        firstname = data.get("FirstName", "")

        SQL = """
            SELECT
                p.ProfileId,
                p.FirstName,
                p.LastName,
                p.LAST4SSN,
                p.SSN,
                p.Status
            FROM Profiles p
            WHERE p.LAST4SSN = ? OR p.LAST4SSN = ?
        """
        params = [last4ssn, last4ssn]

        results = self.db.fetchall(SQL, params)

        return self.filter_and_resolve(
            results,
            field_filters=[("LastName", lastname), ("FirstName", firstname)],
            fallback=lambda: {"Status": 1, "ProfileId": None, "LiabilityId": None}
        )

    def close(self):
        self.db.close()

# class MSSQLConnect:
#     def __init__(self):
#         self.server = config_loader.get("SQL", "SERVER")
#         self.database = config_loader.get("SQL", "DATABASE")
#         self.user = config_loader.get("SQL", "UID")
#         self.password = config_loader.get("SQL", "PWD")
#         self.driver = "ODBC Driver 17 for SQL Server"
#         self.conn: Optional[pyodbc.Connection] = None
#         self.cursor: Optional[pyodbc.Cursor] = None

#     def init(self):
#         connection_string = (
#             f"DRIVER={self.driver};"
#             f"SERVER={self.server};"
#             f"DATABASE={self.database};"
#             f"UID={self.user};"
#             f"PWD={self.password};"
#             f"TrustServerCertificate=yes"
#         )
#         self.conn = pyodbc.connect(connection_string)
#         self.cursor = self.conn.cursor()

#     def fetchall(self, SQL: str, params: Optional[List[Any]] = None):
#         self.cursor.execute(SQL, params or [])
#         return self.cursor.fetchall()

#     def close(self):
#         try:
#             if self.cursor:
#                 self.cursor.close()
#             if self.conn:
#                 self.conn.close()
#         except Exception as e:
#             print(f"Error closing connection: {e}")

# class MSSQLProfileFinder:
#     def __init__(self, db: MSSQLConnect):
#         self.db = db
#         self.db.init()

#     def _resolve_by_priority(self, matches: List[Any], data: Dict) -> Dict[str, Any]:
#         PRIORITY_1 = {1, 2, 3, 4, 6, 7, 10}
#         PRIORITY_2 = {0, 9}
#         PRIORITY_3 = {5, 8}

#         def priority_group(status):
#             if status in PRIORITY_1:
#                 return 1
#             elif status in PRIORITY_2:
#                 return 2
#             else:
#                 return 3

#         # Sort matches into priority tiers
#         grouped = sorted(matches, key=lambda r: priority_group(r.Status))

#         top_group = [r for r in grouped if priority_group(r.Status) == priority_group(grouped[0].Status)]

#         if len(top_group) == 1:
#             r = top_group[0]
#             return {"Status": 2, "ProfileId": r.ProfileId, "LiabilityId": r.LiabilityId}

#         # Check if all top group entries share the same ProfileId
#         profile_ids = set(r.ProfileId for r in top_group)
#         if len(profile_ids) == 1:
#             enrolled_match = next((r for r in top_group if r.Status == 2), None)
#             if enrolled_match:
#                 return {"Status": 2, "ProfileId": enrolled_match.ProfileId, "LiabilityId": enrolled_match.LiabilityId}
#             else:
#                 return {"Status": 2, "ProfileId": top_group[0].ProfileId, "LiabilityId": None}

#         return self.find_ssn(data)

#     def find_ssn(self, data: Dict) -> Dict[str, Any]:
#         last4ssn = data.get("Last4SSN", "")
#         lastname = data.get("LastName", "")
#         firstname = data.get("FirstName", "")
#         email = data.get("Email", "")

#         SQL = """
#             SELECT
#                 p.ProfileId,
#                 p.FirstName,
#                 p.LastName,
#                 p.LAST4SSN,
#                 p.SSN,
#                 p.Status
#             FROM Profiles p
#             WHERE p.LAST4SSN = ? OR p.LAST4SSN = ?
#         """
#         params = [last4ssn, last4ssn]

#         print("\n[DEBUG] Executing SQL with params:")
#         print("  Last4SSN:", last4ssn)
#         print("  LastName (filter after):", lastname)
#         print("  FirstName (filter after):", firstname)

#         results = self.db.fetchall(SQL, params)

#         print(f"[DEBUG] Found {len(results)} row(s)")
#         for r in results:
#             print(f"  - ProfileId: {r.ProfileId}, LastName: {r.LastName}, FirstName: {r.FirstName}, Status: {r.Status}")

#         if not results:
#             return {"Status": 1, "ProfileId": None, "LiabilityId": None}
#         elif len(results) == 1:
#             row = results[0]
#             return {"Status": 2, "ProfileId": row.ProfileId, "LiabilityId": None}

#         filteredln = [r for r in results if (r.LastName or '').lower() == lastname.lower()]
#         print(f"[DEBUG] After filtering by LastName, {len(filteredln)} row(s) remain")
#         for r in filteredln:
#             print(f"  - ProfileId: {r.ProfileId}, LastName: {r.LastName}, FirstName: {r.FirstName}, Status: {r.Status}")

#         if len(filteredln) == 1:
#             row = filteredln[0]
#             return {"Status": 2, "ProfileId": row.ProfileId, "LiabilityId": None}

#         filteredfn = [r for r in filteredln if (r.FirstName or '').lower() == firstname.lower()]
#         print(f"[DEBUG] After filtering by FirstName, {len(filteredfn)} row(s) remain")
#         for r in filteredfn:
#             print(f"  - ProfileId: {r.ProfileId}, LastName: {r.LastName}, FirstName: {r.FirstName}, Status: {r.Status}")

#         if len(filteredfn) == 1:
#             row = filteredfn[0]
#             return {"Status": 2, "ProfileId": row.ProfileId, "LiabilityId": None}
        
#         if len(filteredfn) == 2 and filteredfn[0].SSN == filteredfn[1].SSN:
#             return self._resolve_by_priority(filteredfn, data)

#         return {"Status": 1, "ProfileId": None, "LiabilityId": None}


#     def find_best_match(self, data: Dict) -> Dict[str, Any]:
#         account = data.get("AccountNumber", "")
#         lastname = data.get("LastName", "")
#         firstname = data.get("FirstName", "")

#         SQL = """
#             SELECT
#                 p.ProfileId,
#                 l.LiabilityId,
#                 p.FirstName,
#                 p.LastName,
#                 p.SSN,
#                 p.Status,
#                 l.Enrolled
#             FROM Profiles p
#             LEFT JOIN Liabilities l ON p.ProfileId = l.ProfileId
#             WHERE l.Active = 1
#                 AND (RIGHT(l.AccountNumber, 4) = ? OR RIGHT(l.CurrentAccountNumber, 4) = ?)
#         """

#         params = [account, account]

#         print("\n[DEBUG] Executing SQL with params:")
#         print("  Account:", account)
#         print("  LastName (filter after):", lastname)
#         print("  FirstName (filter after):", firstname)

#         results = self.db.fetchall(SQL, params)

#         print(f"[DEBUG] Found {len(results)} row(s)")
#         for r in results:
#             print(f"  - ProfileId: {r.ProfileId}, LastName: {r.LastName}, FirstName: {r.FirstName}, LiabilityId: {r.LiabilityId}, Status: {r.Status}, Enrolled: {r.Enrolled}")

#         if not results:
#             return self.find_ssn(data)
#         elif len(results) == 1:
#             row = results[0]
#             return {"Status": 2, "ProfileId": row.ProfileId, "LiabilityId": row.LiabilityId}

#         filteredln = [r for r in results if (r.LastName or '').lower() == lastname.lower() or (r.FirstName or '').lower() == lastname.lower()]
#         print(f"[DEBUG] After filtering by LastName, {len(filteredln)} row(s) remain")

#         if len(filteredln) == 1:
#             row = filteredln[0]
#             return {"Status": 2, "ProfileId": row.ProfileId, "LiabilityId": row.LiabilityId}

#         filteredfn = [r for r in filteredln if (r.FirstName or '').lower() == firstname.lower() or (r.FirstName or '').lower() == lastname.lower()]
#         print(f"[DEBUG] After filtering by FirstName, {len(filteredfn)} row(s) remain")

#         if len(filteredfn) == 1:
#             row = filteredfn[0]
#             return {"Status": 2, "ProfileId": row.ProfileId, "LiabilityId": row.LiabilityId}
#         if len(filteredfn) == 2 and filteredfn[0].SSN == filteredfn[1].SSN:
#             return self._resolve_by_priority(filteredfn, data)
        
#         return self.find_ssn(data)

#     def close(self):
#         self.db.close()

# class FindProfileandLiabilityPOA:
#     def __init__(self, db: MSSQLConnect):
#         self.db = db
#         self.db.init()

#     def find_best_match(self, data: Dict) -> Dict[str, Any]:
#         last4ssn = data.get("Last4SSN", "")
#         lastname = data.get("LastName", "")
#         firstname = data.get("FirstName", "")

#         SQL = """
#             SELECT
#                 p.ProfileId,
#                 p.FirstName,
#                 p.LastName,
#                 p.LAST4SSN,
#                 p.SSN,
#                 p.Status
#             FROM Profiles p
#             WHERE p.LAST4SSN = ? OR p.LAST4SSN = ?
#         """

#         # params = [account, account, f"%{creditor}%", f"%{creditor}%"]
#         params = [last4ssn, last4ssn]

#         print("\n[DEBUG] Executing SQL with params:")
#         print("  Last4SSN:", last4ssn)
#         print("  LastName (filter after):", lastname)
#         print("  FirstName (filter after):", firstname)

#         results = self.db.fetchall(SQL, params)

#         print(f"[DEBUG] Found {len(results)} row(s)")
#         for r in results:
#             print(f"  - ProfileId: {r.ProfileId}, LastName: {r.LastName}, FirstName: {r.FirstName}")

#         if not results:
#             return {"Status": 1, "ProfileId": None, "LiabilityId": None}
#         elif len(results) == 1:
#             row = results[0]
#             return {"Status": 2, "ProfileId": row.ProfileId, "LiabilityId": row.LiabilityId}

#         filtered = [r for r in results if (r.LastName or '').lower() == lastname.lower()]
#         print(f"[DEBUG] After filtering by LastName, {len(filtered)} row(s) remain")
#         print("  Filtered results:")
#         for r in filtered:
#             print(f"  - ProfileId: {r.ProfileId}, LastName: {r.LastName}, FirstName: {r.FirstName}, LiabilityId: {r.LiabilityId}", "Status:", r.Status)
#         if len(filtered) == 1:
#             row = filtered[0]
#             return {"Status": 2, "ProfileId": row.ProfileId, "LiabilityId": row.LiabilityId}

#         else:
#             filteredfn = [r for r in results if (r.FirstName or '').lower() == firstname.lower()]
#             print(f"[DEBUG] After filtering by FirstName, {len(filteredfn)} row(s) remain")
#             print("  Filtered results:")
#             for r in filteredfn:
#                 print(f"  - ProfileId: {r.ProfileId}, LastName: {r.LastName}, FirstName: {r.FirstName}, LiabilityId: {r.LiabilityId}", "Status:", r.Status)
#             if len(filteredfn) == 1:
#                 row = filteredfn[0]
#                 return {"Status": 2, "ProfileId": row.ProfileId, "LiabilityId": row.LiabilityId}
#             if len(filteredfn) == 2:
#                 if filteredfn[0].SSN == filteredfn[1].SSN:
#                     for r in filteredfn:
#                         if r.Status != 11 and r.Status != 5:
#                             row = r
#                             print(f"Account Status: {row.Status}")
#                             return {"Status": 2, "ProfileId": row.ProfileId, "LiabilityId": row.LiabilityId}
#                 return {"Status": 1, "ProfileId": None, "LiabilityId": None}        
#             return {"Status": 1, "ProfileId": None, "LiabilityId": None}
#     def close(self):
#         self.db.close()

# class MSSQLCreditorFinder:
#     def __init__(self, db: MSSQLConnect):
#         self.db = db
#         self.db.init()

#     def get_all_active_creditor_names(self) -> List[str]:
#         SQL = """
#             SELECT Name
#             FROM CreditorMasters
#             WHERE Active = '1'
#         """
#         results = self.db.fetchall(SQL)
#         return [results]

#     def close(self):
#         self.db.close()