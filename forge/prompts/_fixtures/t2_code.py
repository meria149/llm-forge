import json

def proc(d, t=None, f=False):
    r = []
    for i in range(len(d)):
        x = d[i]
        if x['status'] == 'paid' or x['status'] == 'PAID' or x['status'] == 'Paid':
            if t != None:
                if x['date'][:7] == t:
                    amt = float(x['amount'])
                    if f == True:
                        amt = amt * 1.2
                    r.append({'id': x['id'], 'client': x['client'].strip().title(), 'amt': round(amt, 2)})
            else:
                amt = float(x['amount'])
                if f == True:
                    amt = amt * 1.2
                r.append({'id': x['id'], 'client': x['client'].strip().title(), 'amt': round(amt, 2)})
    tot = 0
    for y in r:
        tot = tot + y['amt']
    return json.dumps({'rows': r, 'total': round(tot, 2), 'n': len(r)})
