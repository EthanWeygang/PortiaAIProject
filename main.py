# Didnt speciify the path to the interpreter
from dotenv import load_dotenv
from portia import Portia, DefaultToolRegistry, default_config

load_dotenv(override=True)

config = default_config()
portia = Portia(config=config, tools=DefaultToolRegistry(config=config))