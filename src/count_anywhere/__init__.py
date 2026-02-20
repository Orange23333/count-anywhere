#module_name = 'count_anywhere'  # how to set this module name as 'count_anywhere' not 'src'?
#                                # Or, should we move 'src' as 'count_anywhere'?

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent))

import globals_

import i18n

tr = i18n.tr
