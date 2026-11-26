# ********** GCP Secret Manager **********
class GCP_SECRET:
    # format: user:password
    class SSICRM_LOGIN:
        GCP_SECRET_NAME = "ssicrm-login-cred-docorganizer"
        GCP_SECRET_VALUE = None

    # format: user:password
    class CDS_LOGIN:
        GCP_SECRET_NAME = "cdszone2-auth-api-cred"
        GCP_SECRET_VALUE = None


# ********** App Settings (not secret) **********
class APP_SETTING:
    SSICRM_URL = "https://ssiapi.com/api"
    CDS_URL = "https://api.cdszone2.com/api/organizer/process"
