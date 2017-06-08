#!/usr/bin/python
#
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Gets the status of all products on the specified account."""

import sys
import csv
import codecs
import os
import json
import pprint
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time

from oauth2client import client
import shopping_common
from operator import itemgetter

# The maximum number of results to be returned in a page.
MAX_PAGE_SIZE = 250


def main(argv):
  with open('feedstats.csv', 'r') as file:
    reader = csv.reader(file)
    prev_count = list(list(rec) for rec in reader)
  with open('feedIDs.csv', 'r') as file:
    reader = csv.reader(file)
    rsm_list = list(list(rec) for rec in reader)
  cwd = os.getcwd()
  gmc_stats = []
  alerts = []
  for client in os.listdir(cwd):
    if '.' not in client:
      print(client)
      os.chdir(cwd + "\\" + client)
      os.system('oauth2.py')
      start = time.time()
      counts = approvals(argv) 
      print("Runtime: %s seconds ---" % (time.time() - start))
      threshold_index = [ind for ind in xrange(len(rsm_list)) if client in rsm_list[ind]]
      prev_index = [ind for ind in xrange(len(prev_count)) if client in prev_count[ind]]
      rsm = rsm_list[threshold_index[0]][2]
      row = [client, rsm, counts[0], counts[1]]
      if len(prev_index) > 0 and float(prev_count[prev_index[0]][2]) != 0:  
        prev_approved = prev_count[prev_index[0]][2]
        change = float(row[2])/float(prev_approved) - 1
        threshold = rsm_list[threshold_index[0]][3]
        if change < float(threshold):
          alert = [rsm_list[threshold_index[0]][0], rsm, prev_approved, counts[0], counts[1], change, threshold]
          alerts.append(alert)
      gmc_stats.append(row)
      os.chdir('../')

  names = [item[2] for item in rsm_list]
  names.pop(0)
  names = list(set(names))
  
  for name in names:
    filtered = [feed for feed in alerts if name in feed]  
    if len(filtered) > 0:
      sendEmail(name, filtered)

  with open('feedstats.csv', 'w') as f:
    filewriter = csv.writer(f, dialect='excel')
    filewriter.writerow(['Client', 'Products Approved', 'Total Products'])
    filewriter.writerows(gmc_stats)    


def approvals(argv):
  # Authenticate and construct service.
  service, config, _ = shopping_common.init(argv, __doc__)
  merchant_id = config['merchantId']
  shopping_common.check_mca(config, False)
  approvals = 0
  total = 0
  first_call = True
  
  try:
    while True:
      if first_call:
        request = service.productstatuses().list(
        merchantId=merchant_id, maxResults=MAX_PAGE_SIZE)
        first_call = False
      else:
        request = service.productstatuses().list(
        merchantId=merchant_id, maxResults=MAX_PAGE_SIZE, pageToken=result['nextPageToken'])
      while request is not None:
        result = request.execute()
        if shopping_common.json_absent_or_false(result, 'resources'):
          print 'No products were found.'
          return [0,0]
        else:
          products = result['resources']
          for product in products:
            total += 1
            for status in product['destinationStatuses']:
              if 'Shopping' in status['destination'] and 'disapproved' not in status['approvalStatus']:
                approvals += 1
          request = service.productstatuses().list_next(request, result)
          break
      if 'nextPageToken' not in result:
        break
    return [approvals, total]
  except client.AccessTokenRefreshError:
    print ('The credentials have been revoked or expired, please re-run the '
           'application to re-authorize')

def sendEmail(rsm, filtered):
  email = find_email(rsm)
  msg = MIMEMultipart('alternative')
  msg['Subject'] = "URGENT: GMC Feed Status Alert"
  msg['From'] = "Feed Monitor"
  msg['To'] = email
  html = build_email(filtered)
  part1 = MIMEText(html, 'html')
  msg.attach(part1)
  server = smtplib.SMTP('smtp.gmail.com', 587)
  server.ehlo()
  server.starttls()
  server.login("cpcstrategy99@gmail.com", "cpcdiego87")
  server.sendmail('cpcstrategy99@gmail.com', ['cmah@cpcstrategy.com'], msg.as_string())
  server.quit()

def build_email(filtered):
  html = ''
  html = html +'<h2 style=\'margin-bottom:0px;font-family:arial\'><u>Feed Statuses - %s</u></h2>' % filtered[0][1]
  html = html + '<table style=\'border-spacing:10px;font-family:arial\'><tr style=\'font-weight:bold\'> <td>Client</td> <td>Previous # Valid</td> <td>Current # Valid</td> <td>Current Total Items</td> <td>% Change</td> <td>Threshold</td></tr>'
  for client in filtered:
    percent = str(int(round(client[5] * 100))) + '%'
    threshold = int(float(client[6]) * 100)
    threshold = str(threshold) + '%'
    html = html + '<tr><td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td></tr>' % (client[0], client[2], client[3], client[4], percent, threshold)
  html = html + '</table>'
  return html

def find_email(name):

  if name == "Adam":
    return "adam@cpcstrategy.com"
  elif name == "Stephen K":
    return "stephen@cpcstrategy.com"
  # elif name == "Stephen M":
  #   return "smessana@cpcstrategy.com"
  elif name == "Will":
    return "william@cpcstrategy.com"
  # elif name == "Jason":
  #   return "jason@cpcstrategy.com"
  # elif name == "Jostin":
  #   return "Jostin@cpcstrategy.com"
  # elif name == "Chris":
  #   return "chris@cpcstrategy.com"
  # elif name == "Josh":
  #   return "josh@cpcstrategy.com"
  elif name == "Roman":
    return "roman@cpcstrategy.com"
  # elif name == "Anthony":
  #   return "anthony@cpcstrategy.com"
  # elif name == "Lewis":
  #   return "lewis@cpcstrategy.com"
  elif name == "La Broi":
    return "labroi@cpcstrategy.com"
  # elif name == "Erick":
  #   return "erick@cpcstrategy.com"
  # elif name == "Meghan":
  #   return "meghan@cpcstrategy.com"
  # elif name == "Caroline":
  #   return "caroline@cpcstrategy.com"
  # elif name == "Ben":
  #   return "ben@cpcstrategy.com"
  # elif name == "Michael":
  #   return "michael@cpcstrategy.com"
  # elif name == "Dean":
  #   return "dean@cpcstrategy.com"
  # elif name == "Nick":
  #   return "nmanessis@cpcstrategy.com"
  # elif name == "Emiri":
  #   return "emiri@cpcstrategy.com"
  # elif name == "Dianne":
  #   return "dianne@cpcstrategy.com"
  # elif name == "Helen":
  #   return "helen@cpcstrategy.com"
  elif name == "Keith":
    return "keith@cpcstrategy.com"
  # elif name == "Sam":
  #   return "sam@cpcstrategy.com"
  # elif name == "Melissa":
  #   return "melissa@cpcstrategy.com"
  elif name == "Eliza":
    return "eliza@cpcstrategy.com"
  elif name == "Alia":
    return "alia@cpcstrategy.com"  
  else:
    return "sb@cpcstrategy.com"

if __name__ == '__main__':
  main(sys.argv)
