import pytest
from pytest import fixture

from hunter.AsteroidHunter import AsteroidHunter


def pytest_addoption(parser):
    parser.addoption("--key", action="store")

@fixture
def hunter1(request):
    return AsteroidHunter(API_KEY = request.config.getoption("--key")) # Might need to regenerate one or use DEMO_KEY

@fixture
def hunter2():
    return AsteroidHunter(API_KEY = 'thisisnotavalidkey') # BAD KEY
