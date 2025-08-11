SSICRM_MAIN_URL = "https://ssiapi.com/api"
#******** project import

#******** external import
import requests, json

#******** schemas import

class SSICRMService():
    def __init__(self,):

        print("Init SSICRM ")
    
    # ********************************************************************************************************
    # EnrollmentDict
    # ********************************************************************************************************
    def _getLoginSession(self, user_name: str , password: str):
        AUTH_URL = f"{SSICRM_MAIN_URL}/User/auth"
        data = {"userName":user_name,"password":password,"returnUrl":""}
        headers = {"Content-type":"application/json"} 
        
        self.r = requests.Session()
        res = self.r.post(AUTH_URL, data = json.dumps(data) , headers= headers)

        if res.status_code == 200 :
            self.token = res.json()['data']['token']
            self.refresh_token =  res.json()['data']['refreshToken']
            return True
        else:
            raise Exception("Can't log in to SSICRM")

    def search_unmapped_documents(self):
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.token}"
        }
        data = {"start":0,"length":50,"columns":[{"columnName":"status","search":{"value":1,"operator":0}}],"order":[{"columnName":"status","direction":0,"directionName":"asc"},{"columnName":"createdAt","direction":0,"directionName":"asc"}]}
        url = f"{SSICRM_MAIN_URL}/UnMappedDocument/search"
        res = self.r.post(url, data = json.dumps(data) , headers=headers)
        return res.json()

    def preview_document(self, document_id: str):
       
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.token}"
        }
        
        # Construct the URL with the liability ID
        url = f"{SSICRM_MAIN_URL}/UnMappedDocument/{document_id}/preview"
        
        data = {"URL":True}


        # Make the POST request with files and data
        res = self.r.post(url, data = json.dumps(data) , headers= headers)
        
        if res.status_code != 200:
            # raise Exception("Failed to preview recording to SSICRM")
            return None
        return res.json()



def download_file_from_url(url: str, destination_path: str = None):

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        if destination_path is None:
            # Return bytes
            return response.content
        else:
            # Save to file
            with open(destination_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    else:
        raise Exception(f"Failed to download file from {url}. Status code: {response.status_code}")



service_crm = SSICRMService()
service_crm._getLoginSession(user_name="docorganizer@citizendebtservices.com", password="gZ7!mT@rV9qXb#P2LwE$uKd6NcAo1")

unmapped_documents = service_crm.search_unmapped_documents()

for document in unmapped_documents['data']['data']:
    document_id = document["documentId"]

    preview_document = service_crm.preview_document(document_id=document_id)
    if preview_document is None:
        continue
    url = preview_document['data']['url']

    file_bytes = download_file_from_url(url, destination_path=f"documents/{document_id}.pdf")
