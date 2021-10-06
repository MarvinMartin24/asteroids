import pytest

################# API KEYS Success #################

def test_asteroid_closest_approach_good_key(hunter1):
    res = hunter1.asteroid_closest_approach(limit = 2)
    assert type(res) == list ## json of asteroid should be store in list
    assert len(res) == 40 ## Since we have 20 asteroids per pages with 2 pages, we should have 40 asteroids
    for asteroid in res:
        assert type(asteroid) == dict ## asteroid data should be json like
        assert len(asteroid['close_approach_data']) <=  1 ## since we keep only closest approach we should have max 1 element

def test_month_closest_approaches_good_key(hunter1):
    res = hunter1.month_closest_approaches('2021-10')
    assert type(res) == dict ## result should be json like
    assert len(list(res['near_earth_objects'].keys())) == 31 # there must be 31 days in October 2021
    for date, asteroid in res['near_earth_objects'].items():
        assert len(asteroid[0]['close_approach_data']) <= 1 ## since we keep only closest approach we should have max 1 element

def test_nearest_misses_good_key(hunter1):
    res = hunter1.nearest_misses(threshold=10, limit = 100)
    assert type(res) == list ## json of asteroid should be store in list
    ctr = 0 # count the close_approach_data
    for asteroid in res:
        ctr += len(asteroid['close_approach_data'])
        assert type(asteroid) == dict ## asteroid data should be json like
    assert ctr == 10 ## There should be 10 close_approach_data

################# API KEYS Fail #################

def test_asteroid_closest_approach_bad_key(hunter2):
    assert hunter2.asteroid_closest_approach() == None # BAD KEY

def test_month_closest_approaches_bad_key(hunter2):
    assert hunter2.month_closest_approaches('2021-10') == None # BAD KEY

def test_nearest_misses_bad_key(hunter2):
    assert hunter2.nearest_misses() == None # BAD KEY

############## Test Args #################

def test_month_closest_approaches_wrong_date(hunter1):
    assert hunter1.month_closest_approaches('2021-21') == None # BAD DATE
    assert hunter1.month_closest_approaches('test') == None # BAD DATE
    assert hunter1.month_closest_approaches(404) == None # BAD DATE

def test_nearest_misses_wrong_arg(hunter1):
    assert hunter1.nearest_misses(threshold=0, limit = 10) == None # BAD threshold (should be more then 0)
