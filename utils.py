#  -*- coding: utf-8 -*-
"""
Play with facebook API
reference: 

Date: Aug 09, 2017
@author: Thuong Tran
Description: create general function for sending different of messages that fb support
"""

# PageName, PostId, PostContent, NumLike, NumShare, NumComments, NumReact, Datetime
# PostId, CommentId, CommentContent, NumLike, NumReply, NumReact, Datetime
# CommentId, ReplyId, ReplyContent, NumLike, NumReply, NumReact, Datetime
# results = {
#   "PostId": {
#     "PostContent": "content",
#     "NumLike": 123,
#     "NumComments": 456,
#     "NumShare": 789,
#     "NumReact": 12,
#     "CreatedTime": "09 Aug 2017",
#     "AdditionalInfo": "This is about s.th",
#     "Page": "afanpage",
#     "Comments":
#     [
#     "CommentId": {
#       "CommentContent": "This product is good or bad",
#       "NumLike": 123,
#       "NumReply": 23,
#       "NumReact": 24,
#       "CreatedTime": "09 Aug 2017",
#       "IsRelatedToPost": 1,
#       "IsPositive": 1,
#       "UserName": "Username"
#       "ReplyId": {
#         "ReplyContent": "me too",
#         "NumLike": 48,
#         "NumReact": 68,
#         "CreatedTime": "09 Aug 2017",
#         "IsRelatedToPost": 1,
#         "IsPositive": 1
#       }
#     }]
#   }
# }

# https://www.facebook.com/lebaostore79/

import requests
import json
import os
import re
from pymongo import MongoClient

ACCESS_TOKEN = "452502528468709|3TGCZK9l7Droo-lUuff8fzPqVik"
RGX_PHONE = r"\d{9,15}" #r"^([0-9\(\)\/\+ \-]*)$"
RGX_EMAIL = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"

client = MongoClient('localhost', 27017)
db = client.fanpages
posts_collection = db.posts


def get_posts(page_name, num_post):
  results = []
  # params = {
  #     "access_token": os.environ["PAGE_ACCESS_TOKEN"]
  # }
  # headers = {
  #     "Content-Type": "application/json"
  # }
  # r = requests.get("https://graph.facebook.com/v2.6/", params=params, headers=headers, data=data)
  r = requests.get("https://graph.facebook.com/v2.10/" + page_name + "/posts?limit=" + str(num_post) + 
                        "&access_token=" + ACCESS_TOKEN)
  posts = json.loads(r.text)['data']
  # Step 1: Get all postId and its contents
  print(posts)
  for p in posts:
    # Step 2: Get comments
    response = requests.get("https://graph.facebook.com/v2.10/" + p['id'] + 
                      "?fields=shares,likes.summary(true),comments.summary(true)&access_token=" + 
                      ACCESS_TOKEN)
    response = json.loads(response.text)
    post_info = {}
    post_info['PostId'] = p['id']
    post_info['PostContent'] = p['message'] if 'message' in p else ""
    post_info['NumLike'] = response['likes']['summary']['total_count'] if 'likes' in response else 0
    post_info['NumComments'] = response['comments']['summary']['total_count'] if 'comments' in response else 0
    post_info['NumShare'] = response['shares']['count'] if 'shares' in response else 0
    post_info['NumReact'] = 12345
    post_info['CreatedTime'] = p['created_time'] if 'created_time' in p else ""
    post_info['AdditionalInfo'] = "This is about something, for example"
    post_info['Page'] = page_name

    comments_list = response['comments']['data'] # array list of json
    comments = []
    comments = get_comments(p['id'], comments, 1)
    # Search for 2nd level comments (comments of comments)
    all_comments = list(comments)

    for comment in comments:
      temp_comments = []
      cm_id = list(comment.keys())[0]
      temp_comments = get_comments(cm_id, temp_comments, 2)
      if (temp_comments):
        all_comments.extend(temp_comments)

    post_info["Comments"] = all_comments
    post_info["NumComments"] = len(all_comments)
    # print("All comments:")
    # print(json.dumps(results, indent=4))
    results.append(post_info)
  return results


def get_comments(object_id, comments, level):
  if level == 1:
    response = requests.get("https://graph.facebook.com/v2.10/" + object_id + 
                        "?fields=shares,likes.summary(true),comments.summary(true)&access_token=" + 
                        ACCESS_TOKEN)
  else:
    response = requests.get("https://graph.facebook.com/v2.10/" + object_id + 
                        "?fields=likes.summary(true),comments.summary(true)&access_token=" + 
                        ACCESS_TOKEN)

  response = json.loads(response.text)
  comments_list = response['comments']['data'] if 'comments' in response else None # array list of json
  
  if (comments_list):
    for cmt in comments_list:
      cmt_info = {
        "CommentId": cmt['id'],
        "CommentContent": cmt['message'],
        "NumLike": 12345, # response['likes']['summary']['total_count'],
        "NumReply": 12345, # response['comments']['summary']['total_count'],
        "NumReact": 12345,
        "CreatedTime": cmt['created_time'],
        "IsRelatedToPost": "Related",
        "IsPositive": "Positive",
        "UserName": cmt['from']['name'],
        "UID": cmt['from']['id']
        }
      comments.append(cmt_info)
  return comments


def log(log):
  print("log: %s" % log)

# bulk insert
def insert_todb(results):
  insert_ids = posts_collection.insert_many(results) if len(results) > 0 else None
  return insert_ids


def get_comments_fromdb():
  posts = posts_collection.find()
  comments = []
  for post in posts:
    comments.extend([comment['CommentContent'] for comment in post['Comments']])
  return comments


def get_phone_email(comments):
  emails = []
  phones = []
  for comment in comments:
    print(comment)
    email = re.findall(RGX_EMAIL, comment)
    phone = re.findall(RGX_PHONE, comment)
    if email:
      emails.extend(email)
    if phone:
      phones.extend(phone)
  return emails, phones

if __name__ == "__main__":
  # results = get_posts("bigbbplus", 5)
  # insert_ids = insert_todb(results)
  # print(insert_ids)
  comments = get_comments_fromdb()
  emails, phones = get_phone_email(comments)
  print(emails)
  print(phones)