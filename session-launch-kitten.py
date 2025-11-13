import os
import weakref
import subprocess
import shlex
import json
from kitty.boss import Boss
from kitty.tabs import TabManager,Tab,SpecialWindow
from kitty.window import Window,CwdRequest
from kitty.session import Session,create_session
from kitty.utils import log_error, safe_print
from kitty.fast_data_types import log_error_string
from kitty.constants import clear_handled_signals


SUPPORTED_TYPES = ["single", "double"]

def main(args: list[str]) -> str:
	if (len(args) < 3):
		input(f'Call to kitten missing arguments [{q + ', "'.join(args) + q}].\nPress "Enter" to continue.\n')
		return ""
	found = False
	for arg in args:
		if found:
			return arg
		if arg == "-type":
			found = True
	return "single"
	
def handle_result(args: list[str], answer: str, target_window_id: int, boss: Boss) -> None:
	no_windows = answer
	if no_windows not in SUPPORTED_TYPES:
		boss.show_error("Unsupported Type", f'Kitten does not support "{no_windows}".')
		return
	starting_win = boss.window_id_map.get(target_window_id)
	cwd = starting_win.child.foreground_cwd

	if no_windows == "single":
		build_single_os_window_session(cwd, starting_win, boss)
	elif no_windows == "double":
		build_double_os_window_session(cwd, starting_win, boss)
		
	boss.focus_os_window(starting_win.os_window_id)
	return

	
def build_single_os_window_session(cwd: str, starting_win: Window, boss: Boss):
	new_os_window_id = boss.add_os_window()
	main_tab_manager = boss.os_window_map.get(new_os_window_id)
	cwd_request = CwdRequest(starting_win)
	cur_tab = main_tab_manager.new_tab(cwd_from=cwd_request)
	if main_tab_manager is None:
		boss.mark_os_window_for_close(new_os_window_id)
		return
	windows = cur_tab.windows.all_windows
	main_win = windows[-1]
	build_win = cur_tab.new_window(override_title = "project-build",
		env = main_win.child.foreground_environ,
		cwd = cwd,
		location = "vsplit")
	log_win = cur_tab.new_window(override_title = "project-log",
		env = build_win.child.foreground_environ,
		cwd = cwd,
		location = "hsplit", 
		next_to = build_win)

def build_double_os_window_session(cwd: str, starting_win: Window, boss: Boss):
	main_os_window_id = boss.add_os_window()
	debug_os_window_id = boss.add_os_window()
	main_tab_manager = boss.os_window_map.get(main_os_window_id)
	debug_tab_manager = boss.os_window_map.get(debug_os_window_id)
	cwd_request = CwdRequest(starting_win)
	main_tab = main_tab_manager.new_tab(cwd_from=cwd_request)
	main_tab.set_title("project-main");
	debug_tab = debug_tab_manager.new_tab(cwd_from=cwd_request)
	debug_tab.set_title("project-debug");
	if None in [main_tab, debug_tab]:
		boss.mark_os_window_for_close(main_os_window_id)
		boss.mark_os_window_for_close(debug_os_window_id)
		return
	main_windows = main_tab.windows.all_windows
	main_windows[-1].set_title("project-main")
	debug_windows = debug_tab.windows.all_windows
	debug_windows[-1].set_title("project-build")
	log_win = debug_tab.new_window(override_title = "project-log",
		env = debug_windows[-1].child.foreground_environ,
		cwd = cwd,
		location = "vsplit", 
		next_to = debug_windows[-1])

