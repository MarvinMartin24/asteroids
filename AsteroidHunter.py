import requests
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError
from tqdm.contrib.concurrent import thread_map
import datetime
import json


class AsteroidHunter:
    def __init__(self, API_KEY):
        self.API_KEY = API_KEY
        self.nasa_api = {
            'browse': f'https://api.nasa.gov/neo/rest/v1/neo/browse?api_key={API_KEY}',
            'feed': f'https://api.nasa.gov/neo/rest/v1/feed?start_date=2021-01-01&end_date=2021-01-08&api_key={API_KEY}'
        }

    def access_url(self, url):
        '''
        '''
        r = {}
        try:
            r = requests.get(url).json()
        except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError) as e:
            print(f"Requests exception at {url}")
        return r


    def asteroid_closest_approach(self):
        '''
        '''
        final_result = []
        urls = [f'https://www.neowsapp.com/rest/v1/neo/browse?page={page}&size=20&api_key={self.API_KEY}'
                    for page in range(requests.get(self.nasa_api['browse']).json()['page']['total_pages'])]
        
        for page_res in thread_map(self.access_url, urls):
            if page_res:
                for near_earth_object in page_res['near_earth_objects']:
                    min_dist, closest_index = float('inf'), None
                    for i, close_approach_data in enumerate(near_earth_object['close_approach_data']):
                        dist = float(close_approach_data['miss_distance']['astronomical'])
                        if dist < min_dist:
                            min_dist, closest_index = dist, i
                    if closest_index:
                        near_earth_object['close_approach_data'] = [near_earth_object['close_approach_data'][closest_index]]
                    final_result.append(near_earth_object)
        return json.dumps(final_result)

    def month_closest_approaches(self):
        '''
        '''
        pass

    def nearest_misses(self):
        '''
        '''
        pass



if __name__ == '__main__':

    API_KEY = 'FLN4wMmOKumyqyoHmENFH9qL9Aq82TPiDmrA2MQd'
    hunter = AsteroidHunter(API_KEY)
    print(hunter.asteroid_closest_approach())
