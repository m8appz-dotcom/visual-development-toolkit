import argparse,json
from install_ledger import apply_install,list_plans,plan_install,rollback_install

def main():
 parser=argparse.ArgumentParser(description='Scoped mod installation journal and rollback')
 sub=parser.add_subparsers(dest='action',required=True)
 p=sub.add_parser('plan');p.add_argument('source');p.add_argument('target');p.add_argument('files',nargs='+')
 p=sub.add_parser('apply');p.add_argument('plan_id');p.add_argument('plan_sha256')
 p=sub.add_parser('rollback');p.add_argument('plan_id')
 sub.add_parser('list');args=parser.parse_args()
 if args.action=='plan':result=plan_install(args.source,args.target,args.files)
 elif args.action=='apply':result=apply_install(args.plan_id,args.plan_sha256)
 elif args.action=='rollback':result=rollback_install(args.plan_id)
 else:result=list_plans()
 print(json.dumps(result,ensure_ascii=False));return 0

if __name__=='__main__':raise SystemExit(main())
