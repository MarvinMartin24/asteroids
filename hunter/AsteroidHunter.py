import json
import requests
import click
import datetime, calendar
from collections import defaultdict
from typing import Optional, List, Dict, Tuple
from tqdm.contrib.concurrent import thread_map
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError


class AsteroidHunter:
    def __init__(self, API_KEY):
        # Generated Key from https://api.nasa.gov/
        self.API_KEY = API_KEY
        # BASE API to use
        self.NASA_BASE_URL = {
            'browse' : f'https://api.nasa.gov/neo/rest/v1/neo/browse?api_key={API_KEY}',
            'feed' : f'https://api.nasa.gov/neo/rest/v1/feed?api_key={API_KEY}'
        }

    def _is_valid(self, code: int) -> bool:
        '''
        _is_valid checks if an http code is equal to 200.

        :param code (int) : integer corresponding to the http status of a given request
        :return (bool): True if code is 200 else False
        '''
        return code == 200

    def _get(self, url: str, retry: int = 3) -> Dict:
        '''
        _get executes and return the http request from url with a safety (3 tries).

        :param url (str) : string corresponding to the url from which we want to retreive a json
        :param rety (int) : int corresponding to the maximum number of time a request is re-runned in case of exceptions
        :return (json): return the json if the resquest is a success, otherwise return None
        '''
        # if all retry failed then return None
        if retry < 0:
            return None

        try:
            # request url
            r = requests.get(url)

            # if request is valid (200)
            if self._is_valid(r.status_code):
                return r.json() # get json of the page
            else:
                return None
        except (HTTPError, ConnectTimeout, ReadTimeout, Timeout, ConnectionError) as _:
            # in case of exception retry (up to 3 times by default)
            self._get(url, retry - 1)

    def _get_all(self, limit: int = None) -> List[Dict]:
        '''
        _get_all allows to request all the pages (1364) of the NASA "browse" API to retreive all the json of all the asteroids.

        :param limit (int) : limit allows to request only a limited number of pages from the NASA API (useful for debugging)

        :return (json array): return all the asteroids json in a list (if the resquest is a success, otherwise return None)
        '''

        # Argument checks
        if limit and not isinstance(limit, int):
            return None

        # Get base url
        url: str = self.NASA_BASE_URL['browse']

        # Request Base url to retreive inital page
        r: List[Dict] = self._get(url)
        if not r: return r

        # find total number of pages
        total_pages: int = limit if limit else r["page"]["total_pages"]

        # Generate all the url to visit
        urls: List[str] = [f"{url}&page={page}&size=20" for page in range(total_pages)]

        # Multi-Threading requests over all the urls
        return thread_map(self._get, urls)

    def _get_all_between(self, start_date: str, end_date: str) -> Dict:
        '''
        _get_all_between retrieve of Asteroids data based on their closest approach date to Earth within a range of time (up to 7 days).

        :param start_date (str) : Starting date for asteroid search (YEAR-MONTH-DAY)
        :param end_date (str) : Ending date for asteroid search (YEAR-MONTH-DAY) (must be maximum 7 days after start_date)
        :return (json): return the json if the resquest is a success, otherwise return None
        '''
        url: str = f"{self.NASA_BASE_URL['feed']}&start_date={start_date}&end_date={end_date}"
        return self._get(url)

    def asteroid_closest_approach(self, limit: int = None) -> List[Dict]:
        '''
        asteroid_closest_approach return JSON array data that includes each asteroid and its closest approach to Earth.
        (It removes all the approches that are not the closest to Earth)

        :param limit (int) : limit allows to request only a limited number of pages from the NASA API (useful for debugging)

        :return (json array): return the list of json if the resquest is a success, otherwise return None
        '''

        # Argument checks
        if limit and limit < 1:
            return None

        # Output is a list of json of each asteroid (where each one have only the closest approach to earth)
        final_result: List[dict()] = []

        # Retreive all the pages
        pages: List[Dict] = self._get_all(limit)
        # Error in Retreiving pages return None
        if not pages: return pages

        # for each page
        for page in pages:
            if page:
                # for each asteroid
                for asteroid in page.get("near_earth_objects", []):
                    # temp variable that store minimum distance and the corresponding approach index
                    min_dist: Tuple  = (float('inf'), None) # tuple(minimum_astronomical_distance, index_close_approach)
                    # for each approach
                    for i, approach in enumerate(asteroid.get("close_approach_data", [])):
                        # if orbit Earth
                        if approach.get("orbiting_body", dict()) == "Earth":
                            # Get astronomical distance
                            astronomical: float = float(approach['miss_distance']['astronomical'])

                            # if distance smaller than the current min distance than replace it (save i too)
                            if astronomical < min_dist[0]:
                                min_dist = (astronomical, i) # new minimum
                    # if index with minimum approach
                    if min_dist[1]:
                        # keep only the index_close_approach where minimum_astronomical_distance
                        asteroid['close_approach_data'] = [asteroid['close_approach_data'][min_dist[1]]]
                    else:
                        asteroid['close_approach_data'] = []
                    # Store asteroid json in final result
                    final_result.append(asteroid)
        return final_result

    def month_closest_approaches(self, date_str: str) -> Dict:
        '''
        month_closest_approaches return JSON data that includes all the closest asteroid approaches
        in a given calendar month (provided as an argument), including a total element_count for the month.

        :param date_str (str) : Provide year and month on which we want to retreive asteroid's data (YEAR-MONTH)

        :return (json): return the json if the resquest is a success, otherwise return None
        '''

        # Argument checks
        if not isinstance(date_str, str):
            return None
        try:
            datetime.datetime.strptime(date_str, '%Y-%m')
        except:
            return None

        # lambda functions to retreive month and year
        get_month = lambda str : str.split('-')[1]
        get_year = lambda str : str.split('-')[0]

        # empty results dictionnary
        final_result: Dict = {"element_count": 0, "near_earth_objects": {}}

        # extract year, month
        year: str = get_year(date_str)
        month: str = get_month(date_str)

        # check if month in range [1, 12]
        if int(month) > 12 or int(month) < 1: return None

        # find the last day of this given month
        num_days: int = calendar.monthrange(int(year), int(month))[1]

        # Request from the day 1 to 1+7 of the month as a starting point
        start_date: str = f"{year}-{month}-01"
        end_date: str = f"{year}-{month}-08"
        # Run request
        r:List[Dict]  = self._get_all_between(start_date, end_date)
        # check if request worked else return None
        if not r: return r

        # while start_date is the right month and that start_date is different from end_date
        while get_month(start_date) == month and start_date != end_date:

            # update with the data of the week
            final_result["element_count"] += int(r["element_count"])
            final_result["near_earth_objects"] = {**final_result["near_earth_objects"], **r["near_earth_objects"]}

            # move to next page within the month (if end_date overlap next month then clip it with num_days)
            next_end_date: str = r['links']['next'].split('end_date=')[1][:10]
            if get_month(next_end_date) != month:
                r['links']['next'] = r['links']['next'].replace(next_end_date, f"{year}-{month}-{num_days}")

            # Request the next page for the next while loop iteration
            r:List[Dict] = self._get(r['links']['next'])
            if not r: return r

            # new start_date and end_date
            start_date: str = r['links']['self'].split('start_date=')[1][:10]
            end_date: str = r['links']['self'].split('end_date=')[1][:10]

        return final_result

    def nearest_misses(self, threshold: int = 10, limit: int = None) -> List[Dict]:
        '''
        nearest_misses return JSON data that includes the threshold (10) nearest misses, historical or expected, of asteroids impacting Earth.
        A given asteroid can have multiple approaches that belongs to the top/minimum (threshold) distances

        :param threshold (int) : Provide the number of nearest misses to return.
        :param limit (int) : limit allows to request only a limited number of pages from the NASA API (useful for debugging)

        :return (json array): return the list of json if the resquest is a success, otherwise return None
        '''
        # Argument checks
        if threshold < 1:
            return None

        if limit and limit < 1:
            return None

        # Output is a list of json of the asteroids that have the one or several close_approach_data belonging to the 10 nearest.
        final_result: List[dict()] = []

        # memory to keep the small distance, (the page index, the asteroid index, the approach index)
        min_dist: List[Tuple] = [(float('inf'), (None, None, None))]

        # Retreive all the pages
        pages: List[Dict] = self._get_all(limit)
        # Error in Retreiving return None
        if not pages: return pages

        # for each page
        for i, page in enumerate(pages):
            if page:
                # for each asteroid
                for j, asteroid in enumerate(page.get("near_earth_objects", [])):
                    # for each approach
                    for k, approach in enumerate(asteroid.get("close_approach_data", [])):
                        # if orbit Earth
                        if approach.get("orbiting_body", dict()) == "Earth":
                            # Get astronomical distance
                            astronomical_dist: float = float(approach['miss_distance']['astronomical'])

                            # if distance smaller than the highest min distance than add it (save i,j,k too)
                            if astronomical_dist < min_dist[-1][0]:
                                min_dist.append((astronomical_dist, (i, j, k)))
                                min_dist.sort(key=lambda tup: tup[0]) # sort list of distance to keep only the top ones

                                # if list of distance larger than threshold, pop largest element
                                if len(min_dist) > threshold:
                                    min_dist.pop()

        # once we have the smallest distance, we create a dictionnary like this {page_index: { asteroid_index: [list of approches indices]}}
        d = defaultdict(lambda: defaultdict(list))
        for dist, (i, j, k) in min_dist:
            d[i][j].append(k)

        # Go over all the asteroids again and keep the one that are saved in the dictionnary d based on the index
        for i, page in enumerate(pages):
            if i in d:
                for j, asteroid in enumerate(page.get("near_earth_objects", [])):
                    if j in d[i]:
                        approach_index_to_keep = d[i][j]
                        asteroid['close_approach_data'] = [asteroid['close_approach_data'][index] for index in approach_index_to_keep]
                        final_result.append(asteroid)

        return final_result

@click.command()
@click.option('--key', type=str, default='McAj1JEZ69spd2gMBNlr9xMqdvfkhfA3v6O7m5QH', help='API KEY to download at https://api.nasa.gov/.')
@click.option('--limit', type=int, default=None, help='Limit allows to reduce the request number and only request a limited number of pages')
@click.option('--date', type=click.DateTime(formats=["%Y-%m"]), default="2021-10" , help='(Year-Month) to select for month_closest_approaches, to get all asteroids within this period of time')
@click.option('--threshold', type=int, default=10 , help='threshold is the number of nearest_misses to extract.')
def run(key, limit, date, threshold):
    hunter = AsteroidHunter(API_KEY = key) # Might need to regenerate one or use DEMO_KEY
    print(hunter.asteroid_closest_approach(limit=limit), '\n\n')
    print("---------------------------------------------------")
    date = datetime.datetime.strftime(date, '%Y-%m')
    print(hunter.month_closest_approaches(date), '\n\n')
    print("---------------------------------------------------")
    print(hunter.nearest_misses(threshold=threshold, limit=limit))
    print("---------------------------------------------------")

if __name__ == '__main__':
    run()
