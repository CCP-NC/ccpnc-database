# Welcome to the CCP-NC Magres Database Repository

Welcome to the CCP-NC Magres Database repository. This repository contains the codebase for the CCP-NC database, where more functionalities and features for the database can be developed.

## Setup Instructions

### Step 1: Clone the repository

Clone the repository.
```sh
git clone https://github.com/CCP-NC/ccpnc-database
cd ccpnc-database
```

### Step 2: Create a development branch

The best practice is to commit changes to a development branch and not directly onto the 'master' branch. Create a new development branch.
```sh
git checkout -b <your-branch-name>
```

### Step 3: Setup the Virtual Environment

First, set up and activate the virtual environment. Setting up the vitual environment needs to be performed only the first time.

```sh
python -m venv .venv
source .venv/bin/activate
```

### Step 4: Install Dependencies

Install the required dependencies for the project.

```sh
pip install .
```

Optionally, you can freeze your development requirements.

```sh
pip freeze > requirements.txt
```

### Step 5: Setting Up Config Files

From the main directory of the repository, set up the necessary configuration files as follows for the Flask app.

```sh
cd config/
ln -s config.ultron.json config.json
ln -s smtpconfig.mailcatcher.json smtpconfig.json
cd ../static/js
ln -s config.ultron.js config.js
cd ../..
```

### Step 6: Setting Up Secrets

Create a secret folder and add the following files:
- `orcid_details.json`: Contains ORCID authentication details for the CCP-NC app.
- `secret.key`: Contains the secret key to start the Flask app locally.

These files must be obtained from the administrators.

### Step 7: Starting The Flask App

The flask application can be started for development using the command

```sh
python main.py
```

> [!NOTE]
> The above command assumes that `python` is a recognised command on your system that will directly call python. If you have to specify the entire python path every time, you may have to add the python path to your environmental variables.

Upon successful startup, you may view messages similar to the below ones on your terminal:
```sh
 * Serving Flask app 'ccpnc-database'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://localhost:8000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 102-939-356
```

The `localhost` test website can be accessed on a browser on `http://localhost:8000/`. Opening an incognito browser session is recommended for testing in order to avoid having to clear your cache memory repeatedly for some `.js` script changes to take effect during development.

### Step 8: Testing Your Changes Before Creating a Pull Request

Run the necessary tests to ensure your changes do not break existing functionality. The tests are located in the tests folder. You can run all tests using:

```sh
pytest -rs -vvv tests/
```

To run a specific test script, use:

```sh
pytest -rs -vvv tests/py/mdb_test.py
```

It is highly recommended to run the test scripts before committing changes to the development branch to save time during pull requests.