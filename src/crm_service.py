from constants import PRIMARY_ADDRESS_ID
from error_code import ErrorCode
from sqlconnect import SqlConnect
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

    #### get profileds for text search   #####
    def get_profiles_for_text_search(self):
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
                    and p.FirstName LIKE '%Khai%' AND p.LastName LIKE '%Yong%'
                    and p.Status in (1,2);

            """
            fetches = self.sql.fetchall(SQL, [])

            texts_last4 = []
            texts_last12 = []
            texts_last16 = []
            metadata = []

            for item in fetches:
                base_text = f"{item[3]} {item[4]} lives at {item[1]}, {item[6]}, {item[5]} {item[7]} and has Last4SSN: {item[2]}."

                texts_last4.append(
                    f"{base_text} Last4AccountNumbers: {item[9][-4:]} and {item[10][-4:]}."
                )
                texts_last12.append(
                    f"{base_text} Last12AccountNumbers: {item[9][-12:]} and {item[10][-12:]}."
                )
                texts_last16.append(
                    f"{base_text} Last16AccountNumbers: {item[9][-16:]} and {item[10][-16:]}."
                )

                metadata_last4 = []
                metadata_last12 = []
                metadata_last16 = []
                for item in fetches:
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

                    metadata_last4.append(
                        {
                            **base_metadata,
                            "AccountNumbers": [str(item[9])[-4:], str(item[10])[-4:]],
                        }
                    )

                    metadata_last12.append(
                        {
                            **base_metadata,
                            "AccountNumbers": [str(item[9])[-12:], str(item[10])[-12:]],
                        }
                    )

                    metadata_last16.append(
                        {
                            **base_metadata,
                            "AccountNumbers": [str(item[9])[-16:], str(item[10])[-16:]],
                        }
                    )

            return (
                texts_last4,
                texts_last12,
                texts_last16,
                metadata_last4,
                metadata_last12,
                metadata_last16,
            )

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
            # case account number
            # todo: thieu state 
            if query["AccountNumber"] != "null" and query["AccountNumber"] != None:
                SQL += f" and (RIGHT(l.AccountNumber,  {len(query["AccountNumber"])}) = '{query['AccountNumber']}' or RIGHT(l.CurrentAccountNumber,  {len(query["AccountNumber"])}) = '{query['AccountNumber']}')"
                SQL += f" ORDER BY CASE WHEN RIGHT(l.CurrentAccountNumber, {len(query['AccountNumber'])}) = '{query['AccountNumber']}' THEN 0 ELSE 1 END"
            # print(SQL)
            fetches = self.sql.fetchall(SQL, [])

            return fetches

        except Exception as e:
            print(f"Error fetching recordings: {str(e)}")
            raise Exception(ErrorCode.GET_PROFILES_ERROR)

    def close(self):
        self.sql.close()
