#!/usr/bin/env python3
import json
import debugpy

from constant import GCP_SECRET
from services import SSICRMService, CDSZone2Service, DocumentProcessingFlow
from start_up import register_startup_event, split_user_pass

# Debug
# import debugpy
# debugpy.listen(("0.0.0.0", 5679))

def main():
    ssicrm_user, ssicrm_pass = split_user_pass(GCP_SECRET.SSICRM_LOGIN)
    cds_user, cds_pass = split_user_pass(GCP_SECRET.CDS_LOGIN)

    # Services
    crm = SSICRMService()
    crm.login(ssicrm_user, ssicrm_pass)

    cds = CDSZone2Service(username=cds_user, password=cds_pass)
    flow = DocumentProcessingFlow(crm, cds)

    # Single flow only: process ALL unmapped and save back to SSICRM
    results = flow.process_all_unmapped(save_to_ssicrm=True, limit=None)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    # debugpy.listen(("0.0.0.0", 5679))
    # debugpy.wait_for_client()
    # breakpoint()
    register_startup_event()
    main()
