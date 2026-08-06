# 项目配置

* pyproject：已完成，需要时可添加代码。
* pytest：*暂不考虑。*
* coverae：*暂不考虑。*
* ruff：*暂不考虑。*

# 代码

* `installer/*`：*暂不考虑。*
* `tests/*`：*暂不考虑。*
* `tools/*`：*暂不考虑。*
* `src/count_anywhere/`：
  * `config.yml`：默认配置，需要时可添加代码。
  * `main.py`：雏形已完成，需要时可添加代码。
  * `rc_resources.py`：**由pyside的rcc工具自动生成，不要动！**
  * `sgt_dns`： 需要时可添加代码。
  * `libs/`：
    * `collections.py`：已完成。
    * `configs.py`：已完成。
    * `data_bindings.py`：*暂不考虑。*
    * `hotkeys.py`：*暂不考虑。*
    * `i18n.py`：已完成。
    * `io.py`：已完成。
    * `markers.py`：已完成。
    * `qt_ext.py`：*暂不考虑。*
    * `utils.py`：已完成。
    * `win32.py`：*已完成，但暂时不用。*
  * `locales/*`：翻译，需要时可更新。
  * `widgets/`：
    * `about_window.py`：已完成。
    * `config_window.py`：已完成。
    * `marker_editor.py`：未完成。
    * `result_table_dialog.py`：未完成。
    * `system_tray.py`：已完成。