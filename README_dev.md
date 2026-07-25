## ⚙️ Local Usage

Please, follow these steps to get this code running.

### Dependencies

To install the dependencies using [conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html), just run

```shell
conda env create -f environment.yml
```

and then activate the environment


```shell
conda activate ivie
```

Also, you can use python standard virtual environments, installing the dependencies via `requirements.txt`.

### Credentials

The `.env` file stores private keys to access APIs. You must edit the placeholder values and write there your private credentials.

### Scenario configuration

The `config.ini` file is used to load the configuration options for the game. 

In the current version, the system can be used both in English ('en') and Spanish ('es').

### Web application
To start the web app, just run 
```
python main.py
```
and the Streamlit web app will be accessible at localhost (the terminal output will show the link).
