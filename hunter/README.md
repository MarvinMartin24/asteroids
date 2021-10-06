## USAGE

## Clone
Please use this command to clone the repository and enter the folder `asteroids`.
```unix
git clone https://github.com/MarvinMartin24/asteroids.git
cd asteroids
```

## Install Package

To install all the dependencies, please use `poetry`.
```unix
poetry install
```

## Run Experiment

Here is the way to run my code:
```unix
# Help to see cli
poetry run python hunter/AsteroidHunter.py --help

# Example
poetry run python hunter/AsteroidHunter.py --limit 100 --date 2021-09 --threshold 3 --key DEMO_KEY
# please generare key from  https://api.nasa.gov/
# it means to query the 100 pages only for asteroid_closest_approach() and nearest_misses()
# it means look at 2021-09 for month_closest_approaches()
# it means take the 3 nearest for nearest_misses()
```


## Run TEST
Here is the way to test my code using `PyTest`:
```unix
poetry run pytest --key DEMO_KEY
```
Note that you can also to generate a key at https://api.nasa.gov/, because even DEMO_KEY can be limited.

## Contributor
Marvin Martin for Mashey
