import os
import pickle
import pandas as pd
from pandas.io import gbq

import numpy as np
import gensim

import json, requests, re
from pprint import pprint

from django.views import generic
from django.http.response import HttpResponse

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from time import time

import logging
from gcloud import storage

#### 로컬에서 ON 클라우드 환경에서 OFF
cur_dir = os.path.dirname(__file__) + '/model/gensim_word2vec.model'
####

def load_csv_gbq(project_id, gbq_db_name, gbq_table_name, save_local, 
                 chunk=False, chunk_size=None, chunk_start=None, order_rule=""):
    
    configuration = {
                     'query': {'useQueryCache': False,
                               'allowLargeResults': True,
                               'destinationTable': {'projectId': project_id,
                                         'datasetId': gbq_db_name,
                                         'tableId': 'bc_{}'.format(gbq_table_name)},
                               'createDisposition': 'CREATE_IF_NEEDED',
                               'writeDisposition': 'WRITE_TRUNCATE'}
                    }
    if chunk==True:
        print('=================|query|=================\n')
        query = 'select * from {0}.{1} order by {2} limit {3} offset {4};'.format(gbq_db_name, 
                                                                        gbq_table_name,
                                                                        order_rule,
                                                                        chunk_size,
                                                                        chunk_start)
        print(query + '\n')
        print('===========================================')
        csv = gbq.read_gbq(query, project_id=project_id, configuration=configuration)        
        
        if save_local==True:
            csv.to_csv('../data/{0}_{1}.csv'.format(gbq_table_name,chunk_start),
                   encoding='utf-8', index=False)
    
    else :
        query = 'select * from {0}.{1}'.format(gbq_db_name, gbq_table_name)
        print('=================|query|=================\n')
        print(query + '\n')
        print('===========================================')
        
        
        csv = gbq.read_gbq(query, project_id=project_id, configuration=configuration)
        
        if save_local==True:
            csv.to_csv('../data/{0}.csv'.format(gbq_table_name),encoding='utf-8', index=False)
    
    return csv

products = load_csv_gbq(project_id='jjw-web-hub', 
                        gbq_db_name='kaggle_instacart', 
                        gbq_table_name='product_django',
                        save_local=False)
products.product_id = products.product_id.apply(lambda x : str(x))

# 구글 클라우드 환경에서 패스 설정
#storage_client = storage.Client("jjw-web-db")
#bucket = storage_client.get_bucket('jjw-django-bucket')
#blob = bucket.blob("static/item2vec_model/gensim_word2vec.model")
#blob.download_to_filename('./gc_word2vec_1.model')
#clf = gensim.models.Word2Vec.load("./gc_word2vec_1.model")

#### 로컬 경로
clf = gensim.models.Word2Vec.load(cur_dir)
print(clf)

# -- 정상--

#  ------------------------ Fill this with your page access token! -------------------------------
PAGE_ACCESS_TOKEN = "EAAP8SZBhc82sBAMZBJK7MZBxOipRQ3TNYiXZBtwNh0ZB7v8vyZAYLv1IZCPHcMvACZA24adU2OrVZB7wf9tgOT1fhn5NQP3vCjjaNih2NA2DZA3KmTdZBGrrbLbBBd9w7ZCGmAxpS8mXq3adiFRDE8kjbZC9huI73ZBTyXxkFU1KFaZC5O814VDxDWcjj8k"
VERIFY_TOKEN = "12345678901"

jokes = dict(zip(products.product_id, products.product_name))

# Helper function
def post_facebook_message(fbid, recevied_message):
    # Remove all punctuations, lower case the text and split it based on space
    tokens = re.sub(r"[^a-zA-Z0-9\s]",' ',recevied_message).split()
    joke_text = ''
    #print(tokens)
    print('==============1==========')
    for token in tokens:
        #print(token)
        if token in jokes:
            joke_text = jokes[token]
            #print(joke_text)
            print('==============2-1==========')
            break
    if not joke_text:
        joke_text = 'error!'
        #print(joke_text)
        print('==============2-2==========')

    if joke_text != 'error!':
        #print(joke_text)
        print('joke_first_ok')
        #item2vec
        suggest = clf.most_similar(positive=[token], topn=3)
    
        #print(suggest)
        print('suggest_ok')

        recomm_item = []
        for item_id in suggest:
            recomm_item.append(products.product_name.loc[products.product_id == item_id[0]].values[0])
    
        #print(recomm_item)
        #print(recomm_item[0])
        print('recomm_item_ok')

        pd_name = products.loc[products.product_id==token, 'product_name'].values[0]
        #print(pd_name)
        print('pd_name_ok')
        #print(joke_text)

        joke_text = '안녕하세요 주문하신 `{0}` 과 비슷한 {1} \n, {2} \n, {3} 는 어떠세요?'.format(pd_name,recomm_item[0],recomm_item[1],recomm_item[2])
        print('==============4-3={0}========='.format(joke_text))


    else:
        joke_text = 'error!' + '뭔가 에러가 났다 하지만 출력되는거보니 신텍스문제는 아니야'
        print('==============3-2==========')

    user_details_url = "https://graph.facebook.com/v2.6/%s"%fbid 
    print('==============4-1={0}========='.format(user_details_url))

    user_details_params = {'fields':'first_name,last_name,profile_pic', 'access_token':PAGE_ACCESS_TOKEN} 
    user_details = requests.get(user_details_url, user_details_params).json() 
    print('==============4-2={0}========='.format(user_details))

    post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=%s'%PAGE_ACCESS_TOKEN
    response_msg = json.dumps({"recipient":{"id":fbid}, "message":{"text":joke_text}})
    status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
    pprint(status.json())

# Create your views here.
class recommBotView(generic.View):
    def get(self, request, *args, **kwargs):
        if self.request.GET['hub.verify_token'] == VERIFY_TOKEN:
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse('Error, invalid token')
        
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    # Post function to handle Facebook messages
    def post(self, request, *args, **kwargs):
        # Converts the text payload into a python dictionary
        incoming_message = json.loads(self.request.body.decode('utf-8'))
        # Facebook recommends going through every entry since they might send
        # multiple messages in a single call during high load
        for entry in incoming_message['entry']:
            for message in entry['messaging']:
                # Check to make sure the received call is a message call
                # This might be delivery, optin, postback for other events 
                if 'message' in message:
                    # Print the message to the terminal
                    pprint(message)    
                    # Assuming the sender only sends text. Non-text messages like stickers, audio, pictures
                    # are sent as attachments and must be handled accordingly. 
                    post_facebook_message(message['sender']['id'], message['message']['text'])    
        return HttpResponse() 
