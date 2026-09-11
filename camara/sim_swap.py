def check_sim_swap(reporter_msisdn_hash: str) -> str:
    if not reporter_msisdn_hash:
        return "UNVERIFIED"
    
    if reporter_msisdn_hash.endswith("9") or "flag" in reporter_msisdn_hash.lower():
        return "FLAGGED_SIM_SWAP"
    
    return "TRUSTED"
