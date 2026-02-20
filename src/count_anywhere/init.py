from path_dict import PathDict

# Initialize Qt

# Initialize modules
import globals_
import i18n

# Load config
from config import load_config
load_config()
del load_config

globals_ = globals_
i18n = i18n

g: PathDict = globals_.get_global()
tr = i18n.tr