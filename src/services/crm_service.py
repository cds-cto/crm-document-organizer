from common.constants import FUZZY_SEARCH_TOLERANCE, PRIMARY_ADDRESS_ID
from common.error_code import ErrorCode
from services.sqlconnect import SqlConnect
from langchain_core.documents import Document


class CrmService:
    def __init__(self, config_file, config_name):
        self.sql = SqlConnect(config_file, config_name)
        self.sql.init()

    #### get profileds for redis vector store   #####
    def get_profiles_for_vector_store(self):
        """Get profiles
        status: 1,2: submited,enrolled
        AddressId ='5BA9CF57-608F-424D-9385-F543A2708BAF' : primary address
        """

        try:
            SQL = f"""
                    select p.ProfileId,pa.Address1,p.Last4SSN,p.FirstName,p.LastName,pa.State, pa.City, pa.ZipCode,l.LiabilityId, l.AccountNumber,l.CurrentAccountNumber from Profiles p 
                    join ProfileAddresses pa on p.ProfileId = pa.ProfileId
                    join Liabilities l on p.ProfileId  = l.ProfileId 
                    WHERE pa.AddressId ='{PRIMARY_ADDRESS_ID}'
                    and p.Status in (1,2);

            """
            fetches = self.sql.fetchall(SQL, [])

            documents_last4 = []
            documents_last12 = []
            documents_last16 = []

            for item in fetches:
                base_content = f"{item[3]} {item[4]} lives at {item[1]}, {item[6]}, {item[5]} {item[7]} and has Last4SSN: {item[2]}."
                base_metadata = {
                    "ProfileId": str(item[0]),
                    "Name": f"{item[3]} {item[4]}",
                    "Street": str(item[1]),
                    "City": str(item[6]),
                    "State": str(item[5]),
                    "ZipCode": str(item[7]),
                    "Last4SSN": str(item[2]),
                    "LiabilityId": str(item[8]),
                }

                documents_last4.append(
                    Document(
                        page_content=f"{base_content} Last4AccountNumbers: {item[9][-4:]}. Last4CurrentAccountNumbers: {item[10][-4:]}.",
                        metadata=base_metadata,
                    )
                )

                documents_last12.append(
                    Document(
                        page_content=f"{base_content} Last12AccountNumbers: {item[9][-12:]}. Last12CurrentAccountNumbers: {item[10][-12:]}.",
                        metadata=base_metadata,
                    )
                )

                documents_last16.append(
                    Document(
                        page_content=f"{base_content} Last16AccountNumbers: {item[9][-16:]}. Last16CurrentAccountNumbers: {item[10][-16:]}.",
                        metadata=base_metadata,
                    )
                )

            return documents_last4, documents_last12, documents_last16

        except Exception as e:
            print(f"Error fetching recordings: {str(e)}")
            raise Exception(ErrorCode.GET_PROFILES_ERROR)

    #### get profileds from db   #####
    #### query: {FirstName, LastName, Last4Ssn, ZipCode, AccountNumber} #####
    def find_profiles_from_db(self, query):
        """Get profiles
        status: 1,2: submited,enrolled
        AddressId ='5BA9CF57-608F-424D-9385-F543A2708BAF' : primary address
        """
        if query["AccountNumber"] == "null" or query["AccountNumber"] == None:
            return None
        try:
            SQL = f"""
                select p.ProfileId,pa.Address1,p.Last4SSN,p.FirstName,p.LastName,pa.State, pa.City, pa.ZipCode,l.LiabilityId, l.AccountNumber,l.CurrentAccountNumber from Profiles p 
                join ProfileAddresses pa on p.ProfileId = pa.ProfileId
                join Liabilities l on p.ProfileId  = l.ProfileId 
                and pa.AddressId ='{PRIMARY_ADDRESS_ID}'
                and p.Status in (1,2)
                and p.FirstName LIKE '{query['FirstName']}%' and p.LastName LIKE '{query['LastName']}'

            """
            if query["City"] != "null" and query["City"] != None:
                SQL += f" and pa.City = '{query['City']}'"
            if query["Last4Ssn"] != "null" and query["Last4Ssn"] != None:
                SQL += f" and p.Last4Ssn = '{query['Last4Ssn']}'"
            if query["ZipCode"] != "null" and query["ZipCode"] != None:
                SQL += f" and pa.ZipCode = '{query['ZipCode']}'"
            # case account number
            if query["AccountNumber"] != "null" and query["AccountNumber"] != None:
                SQL += f" and (RIGHT(l.AccountNumber,  {len(query["AccountNumber"])}) = '{query['AccountNumber']}' or RIGHT(l.CurrentAccountNumber,  {len(query["AccountNumber"])}) = '{query['AccountNumber']}')"
                SQL += f" ORDER BY CASE WHEN RIGHT(l.CurrentAccountNumber, {len(query['AccountNumber'])}) = '{query['AccountNumber']}' THEN 0 ELSE 1 END"

            # print(SQL)
            fetches = self.sql.fetchall(SQL, [])
            if fetches == None or len(fetches) == 0:
                fetches = self.find_profiles_by_ssn_account_number(query)
            if fetches == None or len(fetches) == 0:
                fetches = self.find_profiles_by_name_account_number(query)

            if fetches == None or len(fetches) == 0:
                profiles_by_name_and_state = self.find_profiles_by_name_and_state(query)
                fetches = self.find_profiles_by_fuzzy_search(
                    query, profiles_by_name_and_state
                )

            if fetches == None:
                return None

            documents = [
                {
                    "ProfileId": item[0],
                    "Address1": item[1],
                    "Last4SSN": item[2],
                    "FirstName": item[3],
                    "LastName": item[4],
                    "State": item[5],
                    "City": item[6],
                    "ZipCode": item[7],
                    "LiabilityId": item[8],
                    "AccountNumber": item[9],
                    "CurrentAccountNumber": item[10],
                }
                for item in fetches
            ]
            # todo: return first item
            if len(documents) > 0:
                return documents[0]
            else:
                return None

        except Exception as e:
            print(f"Error fetching recordings: {str(e)}")
            raise Exception(ErrorCode.GET_PROFILES_ERROR)

    def find_profiles_by_ssn_account_number(self, query):
        """Get profiles
        status: 1,2: submited,enrolled
        AddressId ='5BA9CF57-608F-424D-9385-F543A2708BAF' : primary address
        """
        try:
            if query["Last4Ssn"] == "null" or query["Last4Ssn"] == None:
                return None
            if query["AccountNumber"] == "null" or query["AccountNumber"] == None:
                return None

            SQL = f"""
                select p.ProfileId,pa.Address1,p.Last4SSN,p.FirstName,p.LastName,pa.State, pa.City, pa.ZipCode,l.LiabilityId, l.AccountNumber,l.CurrentAccountNumber from Profiles p 
                join ProfileAddresses pa on p.ProfileId = pa.ProfileId
                join Liabilities l on p.ProfileId  = l.ProfileId 
                and pa.AddressId ='{PRIMARY_ADDRESS_ID}'
                and p.Status in (1,2)

            """
            SQL += f" and p.Last4Ssn = '{query['Last4Ssn']}'"
            # case account number
            if query["AccountNumber"] != "null" and query["AccountNumber"] != None:
                SQL += f" and (RIGHT(l.AccountNumber,  {len(query["AccountNumber"])}) = '{query['AccountNumber']}' or RIGHT(l.CurrentAccountNumber,  {len(query["AccountNumber"])}) = '{query['AccountNumber']}')"
                SQL += f" ORDER BY CASE WHEN RIGHT(l.CurrentAccountNumber, {len(query['AccountNumber'])}) = '{query['AccountNumber']}' THEN 0 ELSE 1 END"
            # print(SQL)
            fetches = self.sql.fetchall(SQL, [])

            return fetches

        except Exception as e:
            print(f"Error fetching recordings: {str(e)}")
            raise Exception(ErrorCode.GET_PROFILES_ERROR)

    def find_profiles_by_name_account_number(self, query):
        """Get profiles
        status: 1,2: submited,enrolled
        AddressId ='5BA9CF57-608F-424D-9385-F543A2708BAF' : primary address
        """
        try:
            if query["FirstName"] == "null" or query["FirstName"] == None:
                return None
            if query["LastName"] == "null" or query["LastName"] == None:
                return None
            if query["AccountNumber"] == "null" or query["AccountNumber"] == None:
                return None

            SQL = f"""
                select p.ProfileId,pa.Address1,p.Last4SSN,p.FirstName,p.LastName,pa.State, pa.City, pa.ZipCode,l.LiabilityId, l.AccountNumber,l.CurrentAccountNumber from Profiles p 
                join ProfileAddresses pa on p.ProfileId = pa.ProfileId
                join Liabilities l on p.ProfileId  = l.ProfileId 
                and pa.AddressId ='{PRIMARY_ADDRESS_ID}'
                and p.Status in (1,2)
                and p.FirstName LIKE '{query['FirstName']}%' and p.LastName LIKE '{query['LastName']}'


            """
            # state
            if query["State"] != "null" and query["State"] != None:
                SQL += f" and pa.State = '{query['State']}'"
            # case account number
            if query["AccountNumber"] != "null" and query["AccountNumber"] != None:
                SQL += f" and (RIGHT(l.AccountNumber,  {len(query["AccountNumber"])}) = '{query['AccountNumber']}' or RIGHT(l.CurrentAccountNumber,  {len(query["AccountNumber"])}) = '{query['AccountNumber']}')"
                SQL += f" ORDER BY CASE WHEN RIGHT(l.CurrentAccountNumber, {len(query['AccountNumber'])}) = '{query['AccountNumber']}' THEN 0 ELSE 1 END"
            # print(SQL)
            fetches = self.sql.fetchall(SQL, [])

            return fetches

        except Exception as e:
            print(f"Error fetching recordings: {str(e)}")
            raise Exception(ErrorCode.GET_PROFILES_ERROR)

    def find_profiles_by_name_and_state(self, query):
        """Get profiles
        status: 1,2: submited,enrolled
        AddressId ='5BA9CF57-608F-424D-9385-F543A2708BAF' : primary address
        """
        try:
            if query["FirstName"] == "null" or query["FirstName"] == None:
                return None
            if query["LastName"] == "null" or query["LastName"] == None:
                return None

            SQL = f"""
                select p.ProfileId,pa.Address1,p.Last4SSN,p.FirstName,p.LastName,pa.State, pa.City, pa.ZipCode,l.LiabilityId, l.AccountNumber,l.CurrentAccountNumber from Profiles p 
                join ProfileAddresses pa on p.ProfileId = pa.ProfileId
                join Liabilities l on p.ProfileId  = l.ProfileId 
                and pa.AddressId ='{PRIMARY_ADDRESS_ID}'
                and p.Status in (1,2)
                and p.FirstName LIKE '{query['FirstName']}%' and p.LastName LIKE '{query['LastName']}'


            """
            # state
            if query["State"] != "null" and query["State"] != None:
                SQL += f" and pa.State = '{query['State']}'"

            fetches = self.sql.fetchall(SQL, [])

            return fetches

        except Exception as e:
            print(f"Error fetching recordings: {str(e)}")
            raise Exception(ErrorCode.GET_PROFILES_ERROR)

    def find_profiles_by_fuzzy_search(self, query, profiles):
        """
        Fuzzy search for account numbers with allowed error tolerance
        Args:
            query: search criteria including AccountNumber
            profiles: list of profile records to search through
            k: error tolerance (default=1) - number of allowed mismatches
        Returns:
            List of matching profile records
        """
        try:
            if (
                not profiles
                or query["AccountNumber"] == "null"
                or query["AccountNumber"] is None
            ):
                return None

            search_number = query["AccountNumber"]
            matching_profiles = []

            for profile in profiles:
                # Get last N digits of both account numbers where N = length of search number
                acc_last_digits = profile[9][-len(search_number) :]  # AccountNumber
                current_acc_last_digits = profile[10][
                    -len(search_number) :
                ]  # CurrentAccountNumber

                # Check both account numbers for matches
                if self._is_fuzzy_match(
                    search_number, acc_last_digits, FUZZY_SEARCH_TOLERANCE
                ) or self._is_fuzzy_match(
                    search_number, current_acc_last_digits, FUZZY_SEARCH_TOLERANCE
                ):
                    matching_profiles.append(profile)

            # Sort matches - exact matches first, then fuzzy matches
            matching_profiles.sort(
                key=lambda x: (
                    self._count_differences(
                        search_number, x[10][-len(search_number) :]
                    ),  # CurrentAccountNumber first
                    self._count_differences(
                        search_number, x[9][-len(search_number) :]
                    ),  # Then AccountNumber
                )
            )

            return matching_profiles

        except Exception as e:
            print(f"Error in fuzzy search: {str(e)}")
            raise Exception(ErrorCode.GET_PROFILES_ERROR)

    def _is_fuzzy_match(self, search_number, target_number, k):
        """
        Check if two numbers match within allowed error tolerance
        """
        if len(search_number) != len(target_number):
            return False

        differences = self._count_differences(search_number, target_number)
        return differences <= k

    def _count_differences(self, num1, num2):
        """
        Count number of different digits between two numbers
        """
        try:
            return sum(1 for a, b in zip(str(num1), str(num2)) if a != b)
        except:
            return float("inf")  # Return infinity if comparison fails

    def close(self):
        self.sql.close()
