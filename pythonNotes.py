from rdio.payment import SubscriptionHistoryEvent, SubscriptionType
from rdio.auth.models import User
from rdio.payment.models import SubscriptionHistory
from rdio.utils.db import chunk_query, chunk_list
import datetime
from rdio.auth.models import UserFollowers
from rdio.analytics.models import ShareActions
from django.conf import settings
from rdio.library.models.playlist import Playlist
import json



for day in range(1,11) :
  print "Starting day %i"%day
  user_ids = []
  user_details = []
  query = User.objects.filter(date_joined__gte=datetime.datetime(2013,10,day),date_joined__lte=datetime.datetime(2013,10,day+1))
  print ' .. chunking user info'
  for user_chunk in chunk_query(query, 1000):
    print '   .... chunk'
    for u in user_chunk:
      if u.country_code == 'US':
        user_ids.append(u.id)
        user_details.append((u.id, u.date_joined, u.birthday, u.location, u.gender))
  subs = SubscriptionHistory.objects.filter(
    event__in=(SubscriptionHistoryEvent.UserSubscribe, SubscriptionHistoryEvent.UserUnsubscribe, SubscriptionHistoryEvent.UserCancelUnsubscribe), 
    user_id__in=user_ids).values_list('user_id', 'old_subscription_type', 'new_subscription_type','date_changed')
  print "  .. chewing on subscription data"
  subs = list(subs)
  print "  .. writing to files"
  filename = 'subscribe_list_%i.csv'%day
  f = open(filename, 'w')
  for z in subs:
    f.write('%i,%i,%i,%s,%s\n'%(z[0],z[1],z[2],z[3].date(),z[3].time()))
  f.close()
  print "  .. chewing on user data"
  filename = 'join_list_%i.csv'%day
  f = open(filename, 'w')
  for u in user_details:
    f.write('%i\t%s\t%s\t%s\t%s\t%s\n'%(u[0], u[1].date(), u[1].time(), u[2].date(), u[3].encode('utf-8'), u[4].encode('utf-8')))
  f.close()




#   0         1          2           3           4      5
#14651364 2013-10-01  00:00:36  1993-10-01  flushing ny m
# 6   0   1 2     3          4
#14652098,0,2,2013-10-24,23:53:21

users = {}
days = {}
odd_user_list = []
odd_sub_count = 0
days['nothing'] = 0
for d in range(0,100):
  days[d] = 0

for day in range(1,11):
  print ' .. starting day %i'%day
  filename_join = 'join_list_%i.csv'%day
  filename_sub = 'subscribe_list_%i.csv'%day
  f_join = open(filename_join, 'r')
  print ' ... parse the join table'
  for l in f_join:
    l = l.split('\t')
    users[l[0]] = {}
    users[l[0]]['details'] = l
    users[l[0]]['sub'] = []
  f_join.close()
  print ' ... parse the sub table'
  f_sub = open(filename_sub, 'r')
  subs_on_that_day = 0
  for l in f_sub:
    l = l.split(',')
    if l[0] in users:
      users[l[0]]['sub'].append(l)
      subs_on_that_day += 1
    else:
      odd_sub_count += 1
  f_sub.close()
  print " .. total subs %i"%subs_on_that_day

print ' .. finding date durations'
for key in users.keys():
  if len(users[key]['sub']) > 1:
    odd_user_list.append(users[key])
  elif len(users[key]['sub']) == 0:
    days['nothing'] += 1
  else:
    sign_up = datetime.datetime.strptime(users[key]['details'][1], '%Y-%m-%d')
    sub_date = datetime.datetime.strptime(users[key]['sub'][0][3], '%Y-%m-%d')
    val = (sub_date - sign_up).days
    users[key]['days_to_sub'] = val
    days[val] += 1



filename = 'days_to_subscribe.csv'
f = open(filename, 'w')
for d in days:
  if days[d] > 0:
    print '%s : %i'%(str(d), days[d])
    f.write('%s,%i\n'%(str(d), days[d]))


for key in users.keys():
  u = users[key]
  age = datetime.datetime.utcnow() - datetime.datetime.strptime(u['details'][3], '%Y-%m-%d')
  age = age.days / 365
  u['age'] = age
  u['loc'] = reduce_location(u['details'][4])

filename = 'awesome_users.csv'
f = open(filename, 'w')
for key in users.keys():
  if len(users[key]['sub']) == 1:
    u = users[key]
    u['details'][5] = u['details'][5].strip()
    details_str = '\t'.join(u['details'])
    u['sub'][0][4] = u['sub'][0][4].strip()
    sub_str = '\t'.join(u['sub'][0][1:])
    f.write('%s\t%s\t%i\t%s\t%i\n'%(details_str, sub_str, u['days_to_sub'], u['loc'], u['age']))


def reduce_location(l):
  val = l.lower(
  val = val.strip()
  val = val.replace('usa','')
  val = val.replace('united state','')
  val = re.sub(r'\d*$','',val)
  m = re.search('([\w ]*)\s*[\s,/]\s*(\w+\s*\w*)(\W*)',val)
  if m:
    val = (m.group(1).strip(), m.group(2).strip())
    #print 'compressing 1 : \'%s\' FROM \'%s\''%(val,l)
  else:
    m = re.search('(.*?)(\W)+(\w+)(\W*)',val)
    if m:
      val = (m.group(1).strip(), m.group(3).strip())
      #print 'compressing 2 : \'%s\' FROM \'%s\''%(val,l)
    else:
      val = ('', val)
  if val[1] in STATES_NORMALIZED:
    val = (val[0], STATES_NORMALIZED[val[1]].lower())
    #print '  compressing 3 : \'%s\' FROM \'%s\''%(val,l)
  test = '%s, %s'%(val[0], val[1])
  if val[1] in STATES_NORMALIZED:
    return val
  if test == 'san, francisco':
    return ('san francisco', 'ca')
  if test == 'bronx, ny':
    return ('new york', 'ny')
  if test == 'new, york':
    return ('', 'ny')
  if test == 'houston, ':
    return ('houston', 'tx')
  if test == 'chicago, ':
    return ('chicago', 'il')
  if test == 'seattle, ':
    return ('seattle', 'wa')
  if test == 'brooklyn, ':
    return ('brooklyn', 'ny')
  if test == 'philadelphia, ':
    return ('philadelphia', 'pa')
  if test == 'dallas, ':
    return ('dallas', 'tx')
  if test == 'arlington, ':
    return ('arlington', 'va')
  if test == 'nashville, ':
    return ('nashville', 'tn')
  if test == 'chicago, ':
    return ('chicago', 'il')
  if test == 'chicago, ':
    return ('chicago', 'il')
  if test == 'washington, district of':
    return ('washington', 'dc')
  if test == 'los, angeles' or test == 'la, ':
    return ('los angeles, ca')
  if test == 'san, diego':
    return ('san diego', 'ca')
  if val[0] in STATES_NORMALIZED and val[1] == '':
    return ('', val[0])
  if val[0] == '':
    return (val[1], '')
  return val

unique_locations = {}
location_results = {}
for key in users.keys():
  u = users[key]
  orig_loc = u['details'][4]
  loc = reduce_location(orig_loc)
  if orig_loc not in unique_locations:
    unique_locations[orig_loc] = loc
  if len(u['sub']) == 1:
    if loc in location_results:
      location_results[loc]['sub'] += 1
    else:
      location_results[loc] = {'sub': 1, 'free': 0}
  else:
    if loc in location_results:
      location_results[loc]['free'] += 1
    else:
      location_results[loc] = {'sub': 0, 'free': 1}

len(unique_locations.keys())
len(location_results.keys())

for l in location_results.keys():
  if  location_results[l]['sub'] > 2:
    print '%i\t%i\t%s'%(location_results[l]['free'], location_results[l]['sub'], l)



filename = 'location_stats.csv'
f = open(filename, 'w')
for l in location_results.keys():
  if location_results[l]['sub'] > 0 or location_results[l]['free'] > 100:
    print('%i\t%i\t%s'%(location_results[l]['free'], location_results[l]['sub'], l))
    f.write('%i\t%i\t%s\n'%(location_results[l]['free'], location_results[l]['sub'], l))

f.close()


# TODO - collect emails of users, see if they were shared to BEFORE their join date
# TODO - collect shares SENT to the users
user_ids = [long(i) for i in users.keys()]
shares = {}
query = ShareActions.objects.filter(user_id__in=user_ids, app=settings.APPS.Rdio).values_list('user_id', 'recipient_id', 'type','method','date_shared')
print ' .. chunking user info'
for share_chunk in chunk_query(query, 500):
  print '   .... chunk'
  for s in share_chunk:
    if s.user_id in shares:
      shares[s.user_id].append(s)
    else:
      shares[s.user_id] = [s]

shared_to = {}
query = ShareActions.objects.filter(recipient_id__in=user_ids, app=settings.APPS.Rdio).values_list('user_id', 'recipient_id', 'type','method','date_shared')
print ' .. chunking user info'
for share_chunk in chunk_query(query, 500):
  print '   .... chunk'
  for s in share_chunk:
    if s.recipient_id in shared_to:
      shared_to[s.recipient_id].append(s)
    else:
      shared_to[s.recipient_id] = [s]


for u in shares.keys():
  users[str(u)]['shared'] = shares[u]

for u in shared_to.keys():
  users[str(u)]['shared_to'] = shared_to[u]

share_summary = {
  'avg_free_shared': [], 
  'avg_free_shared_to': [], 
  'avg_shared_before': [], 
  'avg_shared_after': [], 
  'avg_shared_to_before': [], 
  'avg_shared_to_after': []
  }


filename = 'share_info.csv'
f = open(filename, 'w')
for u in set(shares.keys()).union(set(shared_to.keys())):
  u_sharer = users[str(u)]
  date_joined = '%s %s'%(u_sharer['details'][1],u_sharer['details'][2])
  date_joined = datetime.datetime.strptime(date_joined, '%Y-%m-%d %H:%M:%S')
  if len(u_sharer['sub']) == 1:
    u_sharer['share_summary'] = {'send_before_sub': 0, 'send_after_sub': 0, 'shared_to_before_sub': 0, 'shared_to_after_sub': 0}
    date_subscribed = '%s %s'%(u_sharer['sub'][0][3],u_sharer['sub'][0][4])
    date_subscribed = datetime.datetime.strptime(date_subscribed, '%Y-%m-%d %H:%M:%S')
    if 'shared' in u_sharer:
      for s in u_sharer['shared']:
        recipient = s.recipient_id
        if recipient is None:
          recipient = 'n/a'
        if str(recipient) in users:
          recipient = 'new_user %i'%len(users[str(recipient)]['sub'])
        else:
          recipient = 'other'
        f.write('shared,%i,%s,%s,%s,%s,%i,%s,%s,%i,%i\n'%(
          u, u_sharer['sub'][0][3], u_sharer['sub'][0][4], 
          recipient, s.type, s.method, 
          s.date_shared.date(), s.date_shared.time(),
          (s.date_shared - date_subscribed).days,
          (s.date_shared - date_joined).days
        ))
        if (s.date_shared - date_subscribed).days > 0:
          u_sharer['share_summary']['send_after_sub'] += 1
        else:
          u_sharer['share_summary']['send_before_sub'] += 1
      if u_sharer['share_summary']['send_after_sub']:
        share_summary['avg_shared_after'].append(u_sharer['share_summary']['send_after_sub'])
      if u_sharer['share_summary']['send_before_sub']:
        share_summary['avg_shared_before'].append(u_sharer['share_summary']['send_before_sub'])
    if 'shared_to' in u_sharer:
      for s in u_sharer['shared_to']:
        sender = s.user_id
        if sender is None:
          sender = 'n/a'
        if str(recipient) in users:
          sender = 'new_user %i'%len(users[str(recipient)]['sub'])
        else:
          sender = 'other'
        f.write('shared_to,%i,%s,%s,%s,%s,%i,%s,%s,%i,%i\n'%(
          u, u_sharer['sub'][0][3], u_sharer['sub'][0][4], 
          sender, s.type, s.method, 
          s.date_shared.date(), s.date_shared.time(),
          (s.date_shared - date_subscribed).days,
          (s.date_shared - date_joined).days
        ))
        if (s.date_shared - date_joined).days > 0:
          u_sharer['share_summary']['shared_to_after_sub'] += 1
        else:
          u_sharer['share_summary']['shared_to_before_sub'] += 1
      if u_sharer['share_summary']['shared_to_after_sub']:
        share_summary['avg_shared_to_after'].append(u_sharer['share_summary']['shared_to_after_sub'])
      if u_sharer['share_summary']['shared_to_before_sub']:
        share_summary['avg_shared_to_before'].append(u_sharer['share_summary']['shared_to_before_sub'])
  else:
    u_sharer['share_summary'] = {'shared': 0, 'shared_to': 0}
    if 'shared' in u_sharer:
      u_sharer['share_summary']['shared'] += len(u_sharer['shared'])
      share_summary['avg_free_shared'].append(u_sharer['share_summary']['shared'])
      for s in u_sharer['shared']:
        recipient = s.recipient_id
        if recipient is None:
          recipient = 'n/a'
        if str(recipient) in users:
          recipient = 'new_user %i'%len(users[str(recipient)]['sub'])
        else:
          recipient = 'other'
        f.write('shared,%i,%s,%s,%s,%s,%i,%s,%s,%i,%i\n'%(
          u, '', '', 
          recipient, s.type, s.method, 
          s.date_shared.date(), s.date_shared.time(),
          0,
          (s.date_shared - date_joined).days
        ))
    if 'shared_to' in u_sharer:
      u_sharer['share_summary']['shared_to'] += len(u_sharer['shared_to'])
      share_summary['avg_free_shared_to'].append(u_sharer['share_summary']['shared_to'])
      for s in u_sharer['shared_to']:
        sender = s.user_id
        if sender is None:
          sender = 'n/a'
        if str(recipient) in users:
          sender = 'new_user %i'%len(users[str(recipient)]['sub'])
        else:
          sender = 'other'
        f.write('shared_to,%i,%s,%s,%s,%s,%i,%s,%s,%i,%i\n'%(
          u, '','', 
          sender, s.type, s.method, 
          s.date_shared.date(), s.date_shared.time(),
          0,
          (s.date_shared - date_joined).days
        ))


sub_shared = share_summary['avg_shared_before'] + share_summary['avg_shared_after']
print 'SHARED:\n\tfree: %i (avg %.2f) (mean %i) (pop %.4f)\n\tsub: %i (avg %.2f) (mean %i) (pop %.4f)\n\t\tbefore sub: %i (avg %.2f) (mean %i) (pop %.4f)\n\t\tafter sub:%i (avg %.2f) (mean %i) (pop %.4f)'%(
  sum(share_summary['avg_free_shared']),
  sum(share_summary['avg_free_shared'])/float(len(share_summary['avg_free_shared'])),
  sorted(share_summary['avg_free_shared'])[len(share_summary['avg_free_shared'])/2],
  len(share_summary['avg_free_shared']) / float(stayed_free_user_count),
  sum(sub_shared),
  sum(sub_shared)/float(len(sub_shared)),
  sorted(sub_shared)[len(sub_shared)/2],
  len(sub_shared) / float(subscribed_user_count),
  sum(share_summary['avg_shared_before']),
  sum(share_summary['avg_shared_before'])/float(len(share_summary['avg_shared_before'])),
  sorted(share_summary['avg_shared_before'])[len(share_summary['avg_shared_before'])/2],
  len(share_summary['avg_shared_before']) / float(subscribed_user_count),
  sum(share_summary['avg_shared_after']),
  sum(share_summary['avg_shared_after'])/float(len(share_summary['avg_shared_after'])),
  sorted(share_summary['avg_shared_after'])[len(share_summary['avg_shared_after'])/2],
  len(share_summary['avg_shared_after']) / float(subscribed_user_count)
  )
sub_shared_to = share_summary['avg_shared_to_before'] + share_summary['avg_shared_to_after']
print 'SHARED TO:\n\tfree: %i (avg %.2f) (mean %i) (pop %.4f)\n\tsub: %i (avg %.2f) (mean %i) (pop %.4f)\n\t\tbefore sub: %i (avg %.2f) (mean %i) (pop %.4f)\n\t\tafter sub:%i (avg %.2f) (mean %i) (pop %.4f)'%(
  sum(share_summary['avg_free_shared_to']),
  sum(share_summary['avg_free_shared_to'])/float(len(share_summary['avg_free_shared_to'])),
  sorted(share_summary['avg_free_shared_to'])[len(share_summary['avg_free_shared_to'])/2],
  len(share_summary['avg_free_shared_to']) / float(stayed_free_user_count),
  sum(sub_shared_to),
  sum(sub_shared_to)/float(len(sub_shared_to)),
  sorted(sub_shared_to)[len(sub_shared_to)/2],
  len(sub_shared_to) / float(subscribed_user_count),
  sum(share_summary['avg_shared_to_before']),
  sum(share_summary['avg_shared_to_before'])/float(len(share_summary['avg_shared_to_before'])),
  sorted(share_summary['avg_shared_to_before'])[len(share_summary['avg_shared_to_before'])/2],
  len(share_summary['avg_shared_to_before']) / float(subscribed_user_count),
  sum(share_summary['avg_shared_to_after']),
  sum(share_summary['avg_shared_to_after'])/float(len(share_summary['avg_shared_to_after'])),
  sorted(share_summary['avg_shared_to_after'])[len(share_summary['avg_shared_to_after'])/2],
  len(share_summary['avg_shared_to_after']) / float(subscribed_user_count)
  )

stayed_free_user_count = 0
subscribed_user_count = 0
odd_user_count = 0

for key in users.keys():
  if len(users[key]['sub']) == 0:
    stayed_free_user_count += 1
  elif len(users[key]['sub']) == 1:
    subscribed_user_count += 1
  else:
    odd_user_count += 1




query = UserFollowers.objects.filter(follower__in=user_ids)
print ' .. chunking follower info'
for follow_chunk in chunk_query(query, 5000):
  print '   .... chunk'
  for f in follow_chunk:
    key = str(f.follower.id)
    if 'is_follower' in users[key]:
      users[key]['is_follower'].append({ 'followee': f.followee.id, 'date': f.date_added})
    else:
      users[key]['is_follower'] =  [{ 'followee': f.followee.id, 'date': f.date_added}]


filename = 'is_follower_info.csv'
file = open(filename, 'w')
for key in users.keys():
  if 'is_follower' in users[key]:
    u = users[key]
    date_joined = '%s %s'%(u['details'][1], u['details'][2])
    date_joined = datetime.datetime.strptime(date_joined, '%Y-%m-%d %H:%M:%S')
    date_subscribed = False
    account = 'f'
    if len(u['sub']) == 1:
      account = 's'
      date_subscribed = '%s %s'%(u['sub'][0][3],u['sub'][0][4])
      date_subscribed = datetime.datetime.strptime(date_subscribed, '%Y-%m-%d %H:%M:%S')
    days = {}
    for f in u['is_follower']:
      dayKey = f['date'].date()
      if dayKey in days:
        days[dayKey]['count'] += 1
      else:
        days_since_join = (f['date'] - date_joined).days
        days_since_sub = 0
        if date_subscribed:
          days_since_sub = (f['date'] - date_subscribed).days
        days[dayKey] = { 'count': 1, 'since_sub': days_since_sub, 'date': f['date'].date(),'since_join': days_since_join, 'total': len(u['is_follower']) }
      #print '%s,%s,%s,%s,%i,%i'%(key, followee, f['date'].date(), f['date'].time(), days_since_join, days_since_sub)
      #file.write('%s,%s,%s,%s,%i,%i,%i,%i\n'%(key, followee, f['date'].date(), f['date'].time(), days_since_join, days_since_sub, index, len(u['is_follower'])))
      #index += 1
    for d in days:
      d = days[d]
      file.write('%s,%s,%i,%i,%s,%i,%i\n'%(key, account,d['count'],d['total'],d['date'],d['since_join'],d['since_sub']))


query = UserFollowers.objects.filter(followee__in=user_ids)
print ' .. chunking followee info'
for follow_chunk in chunk_query(query, 5000):
  print '   .... chunk'
  for f in follow_chunk:
    key = str(f.followee.id)
    if 'is_followee' in users[key]:
      users[key]['is_followee'].append({ 'follower': f.follower.id, 'date': f.date_added})
    else:
      users[key]['is_followee'] =  [{ 'follower': f.follower.id, 'date': f.date_added}]


filename = 'is_followee_info.csv'
file = open(filename, 'w')
for key in users.keys():
  if 'is_followee' in users[key]:
    u = users[key]
    date_joined = '%s %s'%(u['details'][1], u['details'][2])
    date_joined = datetime.datetime.strptime(date_joined, '%Y-%m-%d %H:%M:%S')
    date_subscribed = False
    account = 'f'
    if len(u['sub']) == 1:
      account = 's'
      date_subscribed = '%s %s'%(u['sub'][0][3],u['sub'][0][4])
      date_subscribed = datetime.datetime.strptime(date_subscribed, '%Y-%m-%d %H:%M:%S')
    days = {}
    for f in u['is_followee']:
      dayKey = f['date'].date()
      if dayKey in days:
        days[dayKey]['count'] += 1
      else:
        days_since_join = (f['date'] - date_joined).days
        days_since_sub = 0
        if date_subscribed:
          days_since_sub = (f['date'] - date_subscribed).days
        days[dayKey] = { 'count': 1, 'since_sub': days_since_sub, 'date': f['date'].date(),'since_join': days_since_join, 'total': len(u['is_followee']) }
      #print '%s,%s,%s,%s,%i,%i'%(key, followee, f['date'].date(), f['date'].time(), days_since_join, days_since_sub)
      #file.write('%s,%s,%s,%s,%i,%i,%i,%i\n'%(key, followee, f['date'].date(), f['date'].time(), days_since_join, days_since_sub, index, len(u['is_followee'])))
      #index += 1
    for d in days:
      d = days[d]
      file.write('%s,%s,%i,%i,%s,%i,%i\n'%(key, account,d['count'],d['total'],d['date'],d['since_join'],d['since_sub']))


filename = 'user_keys.csv'
file = open(filename, 'w')
for key in users.keys():
  u = users[key]
  if len(u['sub']) == 0:
    file.write('%s,%s\n'%(key,'f'))
  elif len(u['sub']) == 1:
    file.write('%s,%s\n'%(key,'t'))
  else:
    file.write('%s,%s\n'%(key,'x'))


user_ids = [long(i) for i in users.keys()]
more_info_stuff = {}
query = User.objects.filter(id__in=user_ids)
print ' .. chunking misc info'
for misc_info_chunk in chunk_query(query, 5000):
  print '   .... chunk'
  for u in misc_info_chunk:
    key = str(u.id)
    more_info_stuff[key] = {
      'email': u.email,
      'login': u.last_login,
      'join': u.date_joined,
      'reviews': u.review_count,
      'last_update': u.last_updated,
      'device_count': len(u.offlinedevice_set.all())
      }


filename = 'misc_user_info.csv'
file = open(filename, 'w')
for key in more_info_stuff.keys():
  if str(key) not in users:
    print "WHAT THE FUCK %s"%key
  else:
    user = users[key]
    data = more_info_stuff[key]
    email = re.sub(r'.*@(.*)',r'\1',data['email'])
    days_active = (data['last_update'] - data['join']).days
    file.write('%s,%s,%i,%i,%i\n'%(key,email,days_active,data['reviews'],data['device_count']))
    # user['misc'] = {
    #   'email_domain': email,
    #   'reviews': data['reviews'],
    #   'days_active': days_active,
    #   'device_count': data['device_count']
    # }


playlists = {}
query = Playlist.objects.filter(owner__in=user_ids)
print ' .. chunking playlist info'
for playlist_chunk in chunk_query(query, 5000):
  print '   .... chunk'
  for p in playlist_chunk:
    key = str(p.owner.id)
    if key not in playlists:
      playlists[key] = []
    playlists[key].append({ 'created': p.created, 'updates': p.counts_updated, 'size': len(p.playlist_info.entries) })



filename = 'playlists.csv'
file = open(filename, 'w')
for key in playlists:
  u = users[key]
  u['playlists'] = []
  date_joined = '%s %s'%(u['details'][1], u['details'][2])
  date_joined = datetime.datetime.strptime(date_joined, '%Y-%m-%d %H:%M:%S')
  for p in playlists[key]:
    day_made = (p['created'] - date_joined).days
    users[key]['playlists'].append({ 'day_made': day_made, 'size': p['size']})
    file.write('%s,%i,%i,%s,%s\n'%(key, p['size'], day_made, p['created'].date(), p['created'].time()))



#   0     1  2  3      1= device, 2= day, 3 = songs played
#15089702,2,0.0,43
f_plays = open('/Users/rebecca/Work/hackday/novemberHack/plays_october.csv', 'r')
for l in f_plays:
  l = l.split(',')
  key = l[0]
  u = users[key]
  if 'plays' not in u:
    u['plays'] = []
  u['plays'].append({ 'device': l[1], 'day': l[2], 'started_songs': l[3].strip()})

f_plays.close()

f_tracked_plays = open('/Users/rebecca/Work/hackday/novemberHack/plays_tracked_october.csv', 'r')
for l in f_tracked_plays:
  l = l.split(',')
  key = l[0]
  u = users[key]
  if 'plays' not in u:
    print 'WHAT THE HELL!?!? %s'%key
  else:
    for p in u['plays']:
      if p['device'] == l[1] and p['day'] == l[2]:
        p['tracked_songs'] = l[3].strip()
      else: 
        print "\t .. how can I have a tracked count without a play count? %s : %s %s"%(key,l[1],l[2])

f_tracked_plays.close()


plays_summary = {
  'no_plays': 0
}
for day in range(0,11):
  plays_summary['free_players_%s'%day] = 0
  plays_summary['free_ratio_%s'%day] = 0
  plays_summary['free_skips_%s'%day] = 0
  plays_summary['free_plays_%s'%day] = 0
  plays_summary['sub_players_%s'%day] = 0
  plays_summary['sub_ratio_%s'%day] = 0
  plays_summary['sub_skips_%s'%day] = 0
  plays_summary['sub_plays_%s'%day] = 0

for key in users.keys():
  u = users[key]
  sub = len(users[key]['sub']) == 1
  if 'plays' not in u:
    plays_summary['no_plays'] += 1
  elif sub:
    for p in u['plays']:
      i = int(float(p['day']))
      tracked_songs = int(p['tracked_songs']) if 'tracked_songs' in p else 0
      plays_summary['sub_plays_%s'%i] += tracked_songs
      plays_summary['sub_skips_%s'%i] += int(p['started_songs']) - tracked_songs
      plays_summary['sub_ratio_%s'%i] += plays_summary['sub_skips_%i'%i] / float(plays_summary['sub_plays_%i'%i] + plays_summary['sub_skips_%i'%i])
      plays_summary['sub_players_%s'%i] += 1.0
  else:
    for p in u['plays']:
      i = int(float(p['day']))
      tracked_songs = int(p['tracked_songs']) if 'tracked_songs' in p else 0
      plays_summary['free_plays_%s'%i] += tracked_songs
      plays_summary['free_skips_%s'%i] += int(p['started_songs']) - tracked_songs
      plays_summary['free_ratio_%s'%i] += plays_summary['free_skips_%i'%i] / float(plays_summary['free_plays_%i'%i] + plays_summary['free_skips_%i'%i])
      plays_summary['free_players_%s'%i] += 1.0

for day in range(0,10):
  print "DAY %i"%day
  v = plays_summary['free_skips_%i'%day] / float(plays_summary['free_plays_%i'%day] + plays_summary['free_skips_%i'%day])
  print "  free: %.03f ratio\t%.03f avg ratio"%(v,plays_summary['free_ratio_%s'%day]/plays_summary['free_players_%s'%day])
  v = plays_summary['sub_skips_%i'%day] / float(plays_summary['sub_plays_%i'%day] + plays_summary['sub_skips_%i'%day])
  print "  sub: %.03f\t%.03f"%(v,plays_summary['sub_ratio_%s'%day]/plays_summary['sub_players_%s'%day])


filename = 'play_summary.csv'
file = open(filename, 'w')
cut_off_date = datetime.datetime(2013,10,8)
for key in users.keys():
  u = users[key]
  date_joined = '%s %s'%(u['details'][1], u['details'][2])
  date_joined = datetime.datetime.strptime(date_joined, '%Y-%m-%d %H:%M:%S')
  if (date_joined - cut_off_date).days < 0:
    sub = len(users[key]['sub']) == 1
    if 'plays' in u:
      for p in u['plays']:
        day = int(float(p['day']))
        if day < 3:
          tracked_songs = int(p['tracked_songs']) if 'tracked_songs' in p else 0
          file.write('%s,%s,%s,%i,%s,%s,%i\n'%(key,sub,date_joined.date(),day,p['device'],p['started_songs'],tracked_songs))
    else:
      file.write('%s,%s,%s,%i,%s,%s,%i\n'%(key,sub,date_joined.date(),0,-1,0,0))




formal_users = {}
for key in users.keys():
  u = users[key]
  date_joined = '%s %s'%(u['details'][1], u['details'][2])
  date_joined = datetime.datetime.strptime(date_joined, '%Y-%m-%d %H:%M:%S')
  formal_users[key] = {
    'id': key,
    'join_date': u['details'][1],
    'join_time': u['details'][2],
    'sub_date': u['sub'][0][3] if len(u['sub']) == 1 else -99,
    'sub_time': u['sub'][0][4] if len(u['sub']) == 1 else -99,
    'follower_day_0': 0,
    'follower_1_to_sub': 0,
    'follower_post_sub': 0,
    'followee_pre_sub': 0,
    'followee_post_sub': 0,
    'shared_pre_sub': 0,
    'shared_post_sub': 0,
    'shared_to_pre_sub': 0,
    'shared_to_post_sub': 0,
    'playlists_pre_sub': [],
    'playlists_post_sub': [],
    'gender': u['details'][5].strip(),
    'loc_0': u['loc'][0],
    'loc_1': u['loc'][1],
    'age': u['age'],
    'days_to_sub': u['days_to_sub'] if 'days_to_sub' in u else -6,
    'days_active': u['misc']['days_active'],
    'plays': [],
    'email_domain': u['misc']['email_domain'],
    'device_count': u['misc']['device_count'],
    'reviews': u['misc']['reviews']
  }
  if 'playlists' in u:
    for p in u['playlists']:
      if p['day_made'] > formal_users[key]['days_to_sub'] and formal_users[key]['days_to_sub'] >= 0:
        formal_users[key]['playlists_post_sub'].append(p['size'])
      else:
        formal_users[key]['playlists_pre_sub'].append(p['size'])
  if 'is_follower' in u:
    for f in u['is_follower']:
      days_to_follow = (f['date'] - date_joined).days
      if days_to_follow == 0:
        formal_users[key]['follower_day_0'] += 1
      elif days_to_follow > formal_users[key]['days_to_sub'] and formal_users[key]['days_to_sub'] >= 0:
        formal_users[key]['followee_post_sub'] += 1
      else:
        formal_users[key]['followee_pre_sub'] += 1
  if 'is_followee' in u:
    for f in u['is_followee']:
      days_to_follow = (f['date'] - date_joined).days
      if days_to_follow > formal_users[key]['days_to_sub'] and formal_users[key]['days_to_sub'] >= 0:
        formal_users[key]['followee_pre_sub'] += 1
      else:
        formal_users[key]['followee_post_sub'] += 1
  if 'shared' in u:
    for s in u['shared']:
      days_to_share = (s.date_shared - date_joined).days
      if days_to_share > formal_users[key]['days_to_sub'] and formal_users[key]['days_to_sub'] >= 0:
        formal_users[key]['shared_post_sub'] += 1
      else:
        formal_users[key]['shared_pre_sub'] += 1
  if 'shared_to' in u:
    for s in u['shared_to']:
      days_to_share = (s.date_shared - date_joined).days
      if days_to_share > formal_users[key]['days_to_sub'] and formal_users[key]['days_to_sub'] >= 0:
        formal_users[key]['shared_to_post_sub'] += 1
      else:
        formal_users[key]['shared_to_pre_sub'] += 1
  if 'plays' in u:
    if (date_joined - cut_off_date).days < 0:
      sub = len(users[key]['sub']) == 1
      for p in u['plays']:
        day = int(float(p['day']))
        if day < 3:
          tracked_songs = int(p['tracked_songs']) if 'tracked_songs' in p else 0
          formal_users[key]['plays'].append((day,int(p['device']),int(p['started_songs']),tracked_songs))





mylist = [u for u in u['plays'] if isinstance(u,dict)]


filename = 'formal_user_data_3.csv'
file = open(filename, 'w')
json.dump(formal_users, file)


reduced_formal_users = {}
keys = formal_users.keys()[:20]
for key in keys:
  reduced_formal_users[key] = formal_users[key]

filename = 'formal_user_data_short_test.csv'
file = open(filename, 'w')
file.write ("var edges = ");
json.dump(reduced_formal_users, file)
file.close()


for key in users.keys():
  u = users[key]
  if 'playlists' in u:
    print 6/0