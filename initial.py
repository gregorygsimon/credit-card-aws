import pandas as pd
import json, requests, logging

logging.basicConfig(filename='log.txt',level=logging.INFO)

# getting Google Search Credentials from local file or add your own
try:
    with open('/home/greg/.ssh/google_cse_credentials.txt','r') as f:
        creds = json.load(f)
    API_KEY = creds['API_KEY']
    cx = creds['cx']
except:
    print('Define your own Custom Search Engine to get API_KEY and cx (custom search id)')
    API_KEY = 'your key here'
    cx = 'your cx here'

sample_query_string = 'at CATRINAS_1               BLOOMFIELD HIMI'

def google_search(query_string):
    #query_string = " ".join(query_string.split()) # replaces multiple spaces with single space
    query_string = query_string.replace(' ','+')

    url = 'https://www.googleapis.com/customsearch/v1?key={0}&cx={1}&q={2}'.format(API_KEY,cx,query_string)

    resp = requests.get(url)

    try:
        dic = resp.json()
        dic['status_code'] = resp.status_code
        return dic

    except:
        return dict(staus_code=resp.status_code)
    
def try_twice_search(query_string):
    output = google_search(query_string)

    if (    'spelling' in output.keys()
        and type(output['spelling']) == dict
        and 'correctedQuery' in output['spelling'].keys()
        ):
        # this condition means google only responded with a spelling correction
        # so we need to research with the cleaned up spelling
        output = google_search(output['spelling']['correctedQuery'])

    return output

#if __name__ == "__main__":
label_df = pd.read_csv('label_dictionary.csv')

# due to Google Search limits/throttling, this code may need be
# rerun spaced over several days/hours 
# so we either load previous result to continue or create blank dataframe
try:
    old_train_df = pd.read_csv('training_df.csv')
except FileNotFoundError:
    old_train_df = pd.DataFrame(columns=['category','search_string','search_ranking','text'])

dicts = []

for i,row in label_df.iterrows():
    print('row',i)

    old_search_terms = set(old_train_df.search_string.to_list())

    if row['where'] not in old_search_terms:
        try:
            results = try_twice_search(row['where'])
            search_texts = [item['title']+' '+item['snippet'] for item in results['items'][:5]]

            for i,text in enumerate(search_texts):
                d = dict(category       = row['category'],
                         search_string  = row['where'],
                         search_ranking = i,
                         text           = text
                         )
                dicts.append(d)

        except Exception as e:
            # OK if some searches fail, but we should see why
            print(repr(e))

updated_training_df = pd.DataFrame(dicts)

assert old_train_df.columns == updated_training_df.columns

training_df = old_train_df.join()

training_df = pd.concat([old_train_df,updated_training_df],ignore_index=True).drop_duplicates()
training_df.to_csv('training_df.csv')

#training_df = pd.DataFrame(columns=['label','search string','search ranking','text'])
#df = pd.read_csv('creditcard.csv')

for i,row in training_df.sample(1).iterrows():
        print(row['category'])
        print(row['text'])
