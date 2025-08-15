#!/usr/bin/env python3
import json

# from src.services.config_loader_services import config_loader
from services import SSICRMService, CDSZone2Service, DocumentProcessingFlow, config_loader

# Debug
# import debugpy
# debugpy.listen(("0.0.0.0", 5679))

def main():
    # Credentials (config.ini → env → default)
    ssicrm_user = config_loader.get("ssicrm", "username", env="SSICRM_USER", default="")
    ssicrm_pass = config_loader.get("ssicrm", "password", env="SSICRM_PASS", default="")
    cds_user = config_loader.get("cdszone2", "username", env="CDS_USER", default="")
    cds_pass = config_loader.get("cdszone2", "password", env="CDS_PASS", default="")

    # Services
    crm = SSICRMService()
    crm.login(ssicrm_user, ssicrm_pass)

    cds = CDSZone2Service(username=cds_user, password=cds_pass)
    flow = DocumentProcessingFlow(crm, cds)

    # Single flow only: process ALL unmapped and save back to SSICRM
    results = flow.process_all_unmapped(save_to_ssicrm=True, limit=None)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
