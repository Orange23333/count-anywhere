from pathlib import Path

from count_anywhere.path_dict import PathDict

#region Initialize modules
import resources

import count_anywhere.globals_

count_anywhere.globals_.set_app_path(Path(__file__).resolve().parent)

import count_anywhere.i18n
count_anywhere.i18n._init_global(locale = 'en-US')  # TODO: Auto detect locale.

from count_anywhere.config import load_config
load_config()
del load_config
#endregion

#region Aliases
import count_anywhere
import count_anywhere.config

globals_ = count_anywhere.globals_
i18n = count_anywhere.i18n
config = count_anywhere.config

g: PathDict = count_anywhere.globals_.get_global()
tr = count_anywhere.i18n.tr
#endregion
