from google.cloud import secretmanager


class GoogleCloudServices:

    @staticmethod
    def get_secret(secret_name: str, project_id: str) -> str:
        client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": secret_path})
        return response.payload.data.decode("UTF-8").strip()
