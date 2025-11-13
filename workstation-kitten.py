import os
import weakref
import subprocess
import shlex
import json
from kitty.boss import Boss
from kitty.tabs import TabManager,Tab
from kitty.window import Window
from kitty.utils import log_error, safe_print
from kitty.fast_data_types import log_error_string
from kitty.constants import clear_handled_signals

KITTY_SESSION_FILE: str = ".kitty-session.json"
PROJECT_BUILD_TITLE: str = "project-build"
PROJECT_LOG_TITLE: str = "project-log"

def main(args: list[str]) -> str:
	q = '"' if len(args) > 0 else ""
	if (len(args) < 3):
		input(f'Call to kitten missing arguments [{q + ', "'.join(args) + q}].\nPress "Enter" to continue.\n')
		print()
		return ""
	found = False
	for arg in args:
		if found:
			build = ""
			if arg == "input":
				build = input(f'Please enter an option present in your "{KITTY_SESSION_FILE}":\n')
			else:
				build = arg
			print(f'Args Passed: [{', '.join(args)}].')
			input('Press "Enter" to continue.\n')
			return build 
		if arg == "-build":
			found = True
	input(f'Call to kitten missing arguments [{q + ', "'.join(args) + q}].\nPress "Enter" to continue.\n')
	return ""
	
def parse_kitty_session_json(win: Window, boss: Boss):
	json_path = '/'.join([win.child.foreground_cwd, KITTY_SESSION_FILE])
	try:
		with open(json_path, "r") as file:
			json_data = json.load(file)
	except json.JSONDecodeError:
		boss.show_error("JSON Parse Failed",
			f'json.JSONDecodeError (The file "{json_path}" is not in the correct json format).')
		return None
	except UnicodeDecodeError:
		boss.show_error("JSON Parse Failed",
			f'UnicodeDecodeError (The files "{json_path}" data is not in UTF-8, UTF-16, or UTF-18).')
		return None
	if len(json_data) == 0 :
		boss.show_error("Kitty Session Json Incomplete",
			f'Kitty session json "{json_path}" incomplete and missing entries.')
		return None
	return json_data

def set_window_active(win: Window, boss: Boss):
	return boss.set_active_window(win, True, True)

def find_build_window_in_tab(title: str, tab: Tab, boss: Boss) -> Window:
	for win in tab.windows.all_windows:
		if win.override_title is not None and win.override_title == title:
			return win
	return None

def find_build_kitty_window(title: str, tabs: list[Tab], boss: Boss) -> Window:
	for tab in tabs:
		win = find_build_window_in_tab(title, tab, boss)
		if win is not None:
			break
	return win

def get_window_environ(win: Window, boss: Boss):
	if (len(win.child.foreground_environ) == 0):
		boss.show_error("Environment Of Window Not Found",
			"Was unable to find the environment of the build window.")
		return None
	env = win.child.foreground_environ
	env['KITTY_CHILD_CMDLINE'] = ' '.join(map(shlex.quote, win.child.cmdline))
	return env

def build_command_str(cb, boss, depth: int = 0) -> str:
	parts = []
	for item in cb:
		if isinstance(item, (list, tuple)):
			if depth > 5:
				boss.show_error("CMD Building Error",
					f'Too much type recursion.')
				return None
			inner = [];
			for i in item:
				if isinstance(i, (list, tuple)):
					string = build_command_str(i, boss, depth + 1)
					if string is None:
						return None
					inner.append(string)
				elif isinstance(i, str):
					inner.append(i);
				else:
					boss.show_error("CMD Building Error",
						f'Unexpected token type "{type(i)}".')
					return None
			parts.append(shlex.join(inner))
		elif isinstance(item, str):
			parts.append(item)
		else:
			boss.show_error("CMD Building Error",
				f'Unexpected token type "{type(item).__name__}".')
			return None
	return " ".join(parts);

def get_cmds_list(entry: str, option: str, win: Window, boss: Boss):
	json_data = parse_kitty_session_json(win, boss)
	if (json_data is None or
		entry not in list(json_data) or
		option not in list(json_data[entry])):
		return None
	return json_data[entry][option]

def send_cmds(cmds_list, win: Window, boss: Boss):
	# Popen() cannot send commands to another kitty window (or so it seems to me)
	cmds = build_command_str(cmds_list, boss, 0);
	# SIGKILL (9) is a forcefull termination
	# SIGTERM (15) is a gracefull shutdown
	win.signal_child(15)
	win.clear_screen(True, True)
	win.paste_bytes(cmds + "\n")
	return

def process_tab_manager(entry: str, tab_manager: TabManager, boss:Boss, built: bool, logged: bool):
	new_built = built
	new_logged = logged
	if not built:
		build_win = find_build_kitty_window(PROJECT_BUILD_TITLE, tab_manager.tabs, boss)
		if build_win is not None:
			build_win.signal_child(15)
			build_win.signal_child(15)
			cmds_list = get_cmds_list(entry, "build", build_win, boss);
			if cmds_list is not None:
				send_cmds(cmds_list, build_win, boss)
				new_built = True
	if not logged:
		log_win = find_build_kitty_window(PROJECT_LOG_TITLE, tab_manager.tabs, boss)
		if log_win is not None:
			log_win.signal_child(15)
			log_win.signal_child(15)
			cmds_list = get_cmds_list(entry, "log", log_win, boss);
			if cmds_list is not None:
				send_cmds(cmds_list, log_win, boss)
				new_logged = True

	return [new_built, new_logged]

def handle_result(args: list[str], answer: str, target_window_id: int, boss: Boss) -> None:
	if (answer == ""):
		return
	entry = answer
	built = False
	logged = False
	
	#tab_manager = boss.window_id_map.get(target_window_id).tabref().tab_manager_ref()
	for os_window_id,tab_manager in boss.os_window_map.items():
		if logged and built:
			return
		var = process_tab_manager(entry, 
			tab_manager,
			boss,
			built,
			logged)
		if not built:
			built = var[0]
		if not logged:
			logged = var[1] 

	if not built:
		boss.show_error("Build Window Not Found",
			"Could not find build kitty window.")
	if not logged:
		boss.show_error("Log Window Not Found",
			"Could not find log kitty window.")

	return
