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
import subprocess
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
  client = cwd.split('\\')[-1]
  alerts = []
  gmc_stats = []
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


  names = [item[2] for item in rsm_list]
  names.pop(0)
  names = list(set(names))
  
  for name in names:
    filtered = [feed for feed in alerts if name in feed]  
    if len(filtered) > 0:
      sendEmail(name, filtered)

  with open('./feedstats.csv', 'w') as f:
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
          return [approvals, total]
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
