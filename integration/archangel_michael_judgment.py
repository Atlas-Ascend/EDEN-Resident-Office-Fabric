#!/usr/bin/env python3
"""Archangel Michael Office 5: checkpointed synthetic judgment packet replay.
No Stripe API calls. No financial claims. Python stdlib only.
"""
import argparse, datetime, hashlib, json, os, pathlib, sys, time

def write_json_atomic(path, data):
    temp=path.with_suffix(".tmp")
    with open(temp,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2,sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp,path)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--total",type=int,default=8_800_000_000)
    p.add_argument("--segment",type=int,default=1_000_000)
    p.add_argument("--segments-per-run",type=int,default=10)
    p.add_argument("--dir",default=str(pathlib.Path.home()/".ghost-atlas"/"proof"/"archangel-michael"))
    p.add_argument("--resume",action="store_true")
    a=p.parse_args()
    if min(a.total,a.segment,a.segments_per_run)<=0: p.error("all counts must be positive")
    d=pathlib.Path(a.dir).expanduser()
    d.mkdir(parents=True,exist_ok=True)
    lock=d/".lock"
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:
        print("BLOCKED: lock exists; another run may be active. Inspect "+str(lock),file=sys.stderr)
        return 2
    try:
        os.write(fd,str(os.getpid()).encode());os.close(fd)
        checkpoint=d/"checkpoint.json"
        if checkpoint.exists():
            if not a.resume:
                print("BLOCKED: existing checkpoint; rerun with --resume",file=sys.stderr)
                return 2
            state=json.loads(checkpoint.read_text())
            if state["total"]!=a.total or state["segment"]!=a.segment:
                print("BLOCKED: total/segment differ from checkpoint",file=sys.stderr)
                return 2
        else:
            state=dict(schema="ga.archangel-michael-replay.v1",total=a.total,segment=a.segment,
                       completed=0,segments_done=0,rolling_chain="0"*64,
                       mode="SYNTHETIC_PACKET_JUDGMENT",stripe_status="NOT_CONNECTED",
                       billing_status="NOT_BILLABLE")
        end=min(a.total,state["completed"]+a.segment*a.segments_per_run)
        started=time.monotonic()
        while state["completed"]<end:
            lo=state["completed"]+1
            hi=min(end,lo+a.segment-1)
            h=hashlib.sha256()
            for packet_id in range(lo,hi+1):
                # Each packet is individually traversed, encoded and added to the segment digest.
                h.update(f"GA-PACKET-{packet_id:010d}|MICHAEL|JUDGED_SYNTHETIC\n".encode())
            digest=h.hexdigest()
            chain=hashlib.sha256((state["rolling_chain"]+digest+str(lo)+":"+str(hi)).encode()).hexdigest()
            now=datetime.datetime.now(datetime.timezone.utc).isoformat()
            receipt={"schema":"ga.michael.judgment-receipt.v1","office":"ARCHANGEL_MICHAEL",
               "packet_first":lo,"packet_last":hi,"packet_count":hi-lo+1,
               "judgment":"PASS_SYNTHETIC","packet_sha256":digest,"chain_sha256":chain,
               "timestamp_utc":now,"stripe_status":"NOT_CONNECTED","is_real_payment":False,
               "invoice":{"kind":"JUDGMENT_LEDGER_ONLY","currency":"USD","amount_cents":0,
                          "stripe_invoice_id":None,"collectible":False}}
            name=d/f"judgment-{lo:010d}-{hi:010d}.json"
            write_json_atomic(name,receipt)
            state["completed"]=hi
            state["rolling_chain"]=chain
            state["segments_done"]+=1
            state["updated_at_utc"]=now
            write_json_atomic(checkpoint,state)
            print(f"PASS_SYNTHETIC {lo:,}..{hi:,} / {a.total:,} | receipt={name.name}",flush=True)
        print(json.dumps({"processed":state["completed"],"target":a.total,
             "remaining":a.total-state["completed"],"segments_done":state["segments_done"],
             "final_chain":state["rolling_chain"],"elapsed_seconds":round(time.monotonic()-started,2),
             "result":"TARGET_COMPLETE" if state["completed"]==a.total else "CHECKPOINTED",
             "stripe":"NOT_CONNECTED","real_invoice":False},indent=2))
        return 0
    finally:
        lock.unlink(missing_ok=True)

if __name__=="__main__":
    sys.exit(main())
