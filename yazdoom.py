#!/usr/bin/python3.9

# import json
import logging
import subprocess

from pathlib import Path
from sys import argv as sys_argv
from sys import exit as sys_exit
from sys import platform as sys_platform

import yaml

# from textual.app import App
# from textual.widgets import Footer, Header

_cached_config={}
_cached_game={}
_cached_gameslist=[]


_game_example_yml="""
# This line is a comment in YAML btw

# Name of the game
name: Some DOOM mod

# Path for file to load as the IWAD (-iwad argument in ZDOOM / GZDOOM)
iwad: ./my/legit/doom.wad

# List of aditional filepaths (one or more files) to load, such as aditional WADs and PK3s (-file argument in ZDOOM / GZDOOM)
# This list is not mandatory, but in that case, why would you be using YAZDOOM for anyways?
file(s):
  - /some/file.pk3
  - /some/file.wad
  - /some/other.etc

# The paths shown in this sample file are all UNIX-Like. In Windows, the paths should be something like this:
# C:/Users/SomeKidThatWantsToPlayDOOM/Desktop/some_file.txt
# Do not use the slash that you would use in Windows/DOS (backslash), always use regular shash

# Relative paths can also be used: they are attached to the program's directory
"""

def argument_parser(action:str)->dict:

	argparts=sys_argv[2:]
	pieces_len=len(argparts)

	actions_valid={
		"run":["-i","-f"],
	}

	params={}
	idx=0
	while True:

		if not idx+1<pieces_len:
			break

		key=argparts[idx].strip().lower()
		value=argparts[idx+1]

		idx=idx+2

		if key in params.keys():
			print(key,": already exists")
			continue

		if key not in actions_valid[action]:
			print(key,": not valid")
			break

		if action=="run":

			if len(params)==1:
				break

		params.update({key:value})

	return params

def yaml_read(filepath=None,text=None):

	has_file=(not (not filepath))
	has_text=(not (not text))

	content=None
	if (not has_file) and has_text:
		content=text
	if has_file and (not has_text):
		content=filepath.read_text()

	if not content:
		return {}

	data=yaml.load(
		content,
		Loader=yaml.Loader
	)

	# except Exception as e:
	# 	logging.exception("FUCK")
	# 	print(
	# 		"YAML read error"
	# 		f"\n\tFile: {str(filepath)}"
	# 		f"\n\tError: {str(e)}"
	# 	)
	# 	return {}

	return data

def yaml_write(filepath,data)->bool:
	# try:
	filepath.write_text(
		yaml.dump(
			_cached_game,
			sort_keys=False
		)
	)
	# except Exception as e:
	# 	logging.exception("FUCK")
	# 	print(
	# 		"YAML write error"
	# 		f"\n\tFile: {str(filepath)}"
	# 		f"\n\tData: {data}"
	# 		f"\n\tError: {str(e)}"
	# 	)
	# 	return False

	return True

def get_path_real(fse):
	if fse.is_absolute():
		return fse

	return Path(sys_argv[0]).parent.joinpath(fse)

def get_path_port():

	if sys_platform=="linux":

		path_port=None
		for port in ["/usr/bin/gzdoom","/usr/games/gzdoom"]:
			if Path(port).exists():
				if Path(port).is_file():
					path_port=Path(port)
					break

		if path_port is not None:
			return path_port

	path_port=Path(_cached_config.get("path_port"))
	if path_port is not None:
		if path_port.exists():
			return path_port

	return None

def update_programcfg()->bool:
	path_prog=Path(sys_argv[0])

	possible_matches=(
		f"{path_prog.stem}.yaml",
		f"{path_prog.stem}.yml"
	)

	data={}

	for fse in path_prog.parent.iterdir():
		if not fse.is_file():
			continue
		if fse.name.lower() not in possible_matches:
			continue

		data.update(yaml_read(filepath=fse))

		if not len(data.keys())==0:
			break

	if not data:
		print("Program config file not found")
		return False

	if not data.get("path_port"):

		if sys_platform=="linux":
			print("WARNING: 'path_port' is missing")

		if sys_platform=="win32":
			print("ERROR: 'path_port' is missing")
			return False

	_cached_config.update(data)

	return True

def update_gameslist(force:bool=False)->int:

	if not (len(_cached_gameslist)==0 or force):
		return len(_cached_gameslist)

	if force:
		if len(_cached_gameslist)>0:
			_cached_gameslist.clear()

	path_games=Path(sys_argv[0]).parent.joinpath("games")
	if not path_games.is_dir():
		return []

	games=[]
	for fse in path_games.iterdir():
		if not fse.is_file():
			continue
		if fse.suffix.lower() not in (".yaml",".yml"):
			continue
		if fse.stat().st_size>1024*32:
			continue
		if not game_yaml_to_data(fse):
			continue
		games.append(fse)

	if len(games)>1:
		games.sort()

	_cached_gameslist.extend(games)
	return len(_cached_gameslist)

def get_game_by_index(index:int):

	if len(_cached_gameslist)==0:
		update_gameslist()

	if index>len(_cached_gameslist)-1:
		return None

	return _cached_gameslist[index]

def game_data_to_yaml(fse)->bool:

	key_name=_cached_game.get("name",None)
	key_iwad=_cached_game.get("iwad",None)
	if not key_name:
		return False
	if not key_iwad:
		return False

	return yaml_write()

def game_yaml_to_data(fse)->dict:

	data=yaml_read(filepath=fse)
	if not data.get("name",None):
		return {}
	if not data.get("iwad",None):
		return {}

	return data

def game_yaml_to_data_global(text:str)->bool:

	data=game_yaml_to_data(text)

	if len(_cached_game.keys())>0:
		_cached_game.clear()

	_cached_game.update(data)
	return True

def run_zdoom(
		path_zdoom,
		path_iwad,
		path_savedir,
		path_config,
		list_files=[]
	):

	print(f"\nRunning: {path_zdoom.name}\n\tIWAD:\n\t\t{str(path_iwad)}")
	cmd_line=[
		str(path_zdoom),
		"-savedir",str(path_savedir),
		"-config",str(path_config),
		"-iwad",str(path_iwad),
	]
	if len(list_files)>0:
		print("\nFile(s):")
		cmd_line.append("-file")
		for fse in list_files:
			print(f"\t{str(fse)}")
			cmd_line.append(str(fse))

	print("\n$",cmd_line)

	proc=subprocess.run(cmd_line)
	print("\nSUBPROCESS RETURNCODE:",proc.returncode)

def main_run(fse_game):

	path_port=get_path_port()
	if not path_port:
		print("Path to GZDOOM binary not found")
		return False

	path_progdir=Path(sys_argv[0]).parent
	path_games=path_progdir.joinpath("games")
	path_gamedir=path_games.joinpath(fse_game.stem)
	path_savedir=path_gamedir.joinpath("savegames")
	path_config=path_gamedir.joinpath("config.ini")

	path_savedir.mkdir(parents=True,exist_ok=True)
	if path_config.exists():
		if not path_config.is_file():
			print("Not a file:",str(path_config))
			return False

	if not path_config.exists():
		path_config_local=path_progdir.joinpath("config.ini")
		if path_config_local.exists():
			if path_config_local.is_file():
				path_config.write_bytes(
					path_config_local.read_bytes()
				)

	if not path_config.exists():
		print("WARNING: No config file was found, the game will use the default config provided by the source port")

	if not _cached_game:
		if not game_yaml_to_data_global(fse_game):
			print("Unable to read game file:",fse_game.name)
			return False
	path_iwad=get_path_real(Path(_cached_game["iwad"]))

	the_list=[]
	if "file(s)" in _cached_game.keys():
		for fse_str in _cached_game["file(s)"]:
			the_list.append(
				get_path_real(Path(fse_str))
			)

	run_zdoom(
		path_port,
		path_iwad,
		path_savedir,
		path_config,
		the_list
	)

	return True

if __name__=="__main__":

	binary=Path(sys_argv[0].strip()).name

	if len(sys_argv)<2:

		print(
			"\nYAZDOOM\nYet Another ZDOOM/GZDOOM frontend"
			"\n\nUsage:"
			f"\n\t$ {binary} [Action] (ActionParameters)"
			"\n\nActions:"
			"\n- ui: User interface"
			"\n- list: Lists available games"
			"\n- run: Runs a game"
			"\n- help-program: Prints a sample config file for the program's configuration (in YAML)"
			"\n- help-game: Prints sample game file (in YAML)"
			"\n\nWritten by Carlos Alberto González Hernández (2024-01-02)"
		)

		sys_exit(0)

	action=sys_argv[1].lower().strip()

	if action=="help-program":
		print("This is not clear yet")
		sys_exit(0)

	if action=="help-game":
		path_sample=Path(sys_argv[0]).parent.joinpath("games/example.yml")

		if not path_sample.parent.exists():
			path_sample.parent.mkdir()

		if not path_sample.parent.is_dir():
			print(f"The path\n\t{str(path_sample.parent)}\nis not a directory")
			sys_exit(0)

		print(f"Saved sample game file to:\n\t{str(path_sample)}")
		path_sample.write_text(_game_example_yml)
		sys_exit(0)

	if action=="ui":

		print("The UI is not ready (yet)")
		sys_exit(0)

	if action=="list":

		qtty=update_gameslist()
		if qtty==0:
			print("You have no games")
			sys_exit(1)

		count=0
		print("Index\tName")
		for fse in _cached_gameslist:
			print(f"{count}\t"+yaml_read(filepath=fse)["name"])
			count=count+1

		sys_exit(0)

	if action=="run":

		if len(sys_argv)<3:
			print(
				"\nYAZDOOM (run action)\nHow to run a game"
				"\n\nUsage:"
				f"\n\t$ {binary} {action} -i INDEX"
				f"\n\t$ {binary} {action} -f FILEPATH"
				"\n\n-i INDEX\n\tGame index"
				"\n\n-f FILEPATH\n\tYML Game file"
			)
			sys_exit(0)

		if not update_programcfg():
			print("Failed to load program configuration")
			sys_exit(1)

		args=argument_parser(action)
		if not args:
			print("Error reading parameters")
			sys_exit(1)

		fse_game=None
		if "-i" in args.keys():
			try:
				int(args["-i"])
			except Exception as e:
				print("NaN:",str(e))
				sys_exit(1)

			fse_game=get_game_by_index(int(args["-i"]))

		if "-f" in args.keys():
			fse_game=Path(args["-f"])

		if not fse_game:
			print("The game does not exist")
			sys_exit(1)

		result=main_run(fse_game)
		sys_exit({True:0,False:1}[result])

	print("Unknown action")
	sys_exit(1)
