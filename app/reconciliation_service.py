"""Provider-vs-source comparison snapshots."""
from decimal import Decimal


class ReconciliationService:
 def __init__(self,service,provider):self.db,self.provider=service._db,provider
 def verify(self,actor,item,source):
  try:remote=self.provider.get_purchase(item['provider_id'])
  except KeyError:return {'status':'missing_remote','differences':['remote']}
  diffs=[]
  for field in ('date','currency'):
   if str(remote.get(field))!=str(source.get(field)):diffs.append(field)
  if abs(Decimal(str(remote.get('total')))-Decimal(str(source.get('total'))))>Decimal('.01'):diffs.append('total')
  return {'status':'needs_reconciliation' if diffs else 'verified','differences':diffs,'provider_id':item['provider_id']}
