# Squirdle Solver

A Selenium-based Python script for automating playing the Pokemon puzzle game [Squirdle](https://squirdle.fireblend.com/) optimally.

## Installation

Clone the repository to your folder of choice.

```bash
git clone https://github.com/nek0d3r/squirdle-solver
cd squirdle-solver
```

Use the Python package and virtual environment manager [pipenv](https://pipenv.pypa.io/en/latest/) to install dependencies.

```bash
pip install pipenv
python -m pipenv install
```

## Usage

To run the solver, simply run the `solve.py` script. It will automatically run the updater.

```bash
py .\solve.py
```

The updater will create `PokeDB.db` if it does not exist, and populate it with Pokemon data based on the `Fireblend/squirdle` repository's Pokedex data. The solver will then open a Selenium driver to Squirdle and automatically start making guesses based on a weight system.

### Selenium

The script and provided drivers for Selenium specifically use Firefox. If you don't have Firefox or would prefer to use another browser, you must supply the proper client [driver](https://www.selenium.dev/selenium/docs/api/py/index.html#drivers) and change the driver called in `solve.py`.

```python
# Provide Gecko driver for Firefox
driver = webdriver.Firefox()

# Provide Chromium driver for Chrome
driver = webdriver.Chrome()

# Microsoft Edge
driver = webdriver.Edge()

# Provide WebKit driver for Safari
driver = webdriver.Safari()
```

## Contributing
Pull requests are welcome. Feel free to suggest changes or improvements, or report any bugs you find.

## License
[MIT](https://choosealicense.com/licenses/mit/)