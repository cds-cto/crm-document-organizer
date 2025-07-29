import os
import configparser

# Get the current directory of the __init__.py script
current_folder = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the config.ini file
config_file_path = os.path.join(current_folder, "config.ini")

# Read the config.ini file
config = configparser.ConfigParser()
config.read(config_file_path)
# --- GCP / Document AI -------------------------------------------------
gcp_project_id   = config["GCP"]["project_id"]
gcp_location     = config["GCP"]["location"]
gcp_processor_id = config["GCP"]["processor_id"]
gcp_processor_id_info_grab = config["GCP"]["processor_id_info_grab"]
gcp_bucket_name  = config["GCP"]["bucket_name"]

# --- OpenAI -----------------------------------------------------------
openai_api_key = config["OPENAI"]["api_key"]

# --- SQL --------------------------------------------------------------
sql_server = config["SQL"]["SERVER"]
sql_database = config["SQL"]["DATABASE"]
sql_uid = config["SQL"]["UID"]
sql_pwd = config["SQL"]["PWD"]
sql_port = config["SQL"].get("PORT", "5432")
