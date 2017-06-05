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


from oauth2client import client
import shopping_common
from operator import itemgetter

# The maximum number of results to be returned in a page.
MAX_PAGE_SIZE = 250


def main(argv):
  with open('feedIDs.csv', 'r') as file:
    reader = csv.reader(file)
    rsm_list = list(list(rec) for rec in reader)
  cwd = os.getcwd()
  gmc_stats = []
  for client in os.listdir(cwd):
    if '.' not in client:
      os.chdir(cwd + "\\" + client)
      os.system('oauth2.py')
      counts = approvals(argv) 
      row = [client, counts[0], counts[1]]
      gmc_stats.append(row)
      os.chdir('../')

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

if __name__ == '__main__':
  main(sys.argv)
