#!/usr/bin/env python3
"""Office 5 fail-closed commercial promotion gate. Offline, no Stripe side effects."""
import argparse,json,sys
from pathlib import Path
REQUIRED=("accepted_customer_scope","approved_nonzero_invoice_amount","documented_customer_identity",
"devos_seca_receipts","proofgrid_digest","medusa_release_classification",
"stripe_invoice_id_matches_customer_and_currency","stripe_authoritative_payment_confirmation",
"idempotent_event_reconciliation")
def judge(r):
    if r.get("mode")!="LIVE": return False,["NON_LIVE_MODE"]
    if r.get("packet_origin")=="SYNTHETIC" or r.get("is_simulation"): return False,["SYNTHETIC_PACKET_NOT_BILLABLE"]
    missing=[k for k in REQUIRED if r.get(k) is not True]
    if not r.get("stripe_invoice_id"): missing.append("STRIPE_INVOICE_ID_ABSENT")
    if not r.get("stripe_event_id"): missing.append("STRIPE_EVENT_ID_ABSENT")
    if not r.get("verified_by_stripe_adapter"): missing.append("STRIPE_ADAPTER_NOT_VERIFIED")
    if not isinstance(r.get("amount_cents"),int) or r.get("amount_cents")<=0: missing.append("INVALID_AMOUNT")
    return not missing,missing
def main():
    a=argparse.ArgumentParser()
    a.add_argument("receipt",help="Existing authoritative payment evidence JSON, never arbitrary operator assertions")
    args=a.parse_args()
    try: receipt=json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    except (OSError,ValueError) as e: print("DENY: "+str(e));return 2
    allow,failures=judge(receipt)
    print(json.dumps({"office":"ARCHANGEL_MICHAEL","gate":"AM-OFFICE5-SETTLEMENT",
    "decision":"PROMOTION_ELIGIBLE_PENDING_INDEPENDENT_REVIEW" if allow else "DENY_FAIL_CLOSED",
    "unmet":failures},indent=2))
    return 0 if allow else 2
if __name__=="__main__": sys.exit(main())
