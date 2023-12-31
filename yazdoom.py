#!/usr/bin/python3.9

# import json
import subprocess

from pathlib import Path
from sys import argv as sys_argv
from sys import exit as sys_exit
from sys import platform as sys_platform

import yaml

# from textual.app import App
# from textual.widgets import Footer, Header

_sample_game="""
# Redirect this to a YAML file
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

_config_program={}

_current_game={}

_list_of_games=[]

def argument_parser(action:str)->dict:

	pieces=sys_argv[2:]
	pieces_len=len(pieces)

	actions_valid={
		"run":["-i","-f"],
	}

	params={}
	idx=0
	while True:

		if not idx+1<pieces_len:
			break

		key=pieces[idx]
		value=pieces[idx+1]

		idx=idx+2

		if key in params.keys():
			print(key,": already gotten")
			continue

		if key not in actions_valid[action]:
			print(key,": ")
			break

		if action=="run":

			if len(params)==1:
				break

		params.update({key:value})

	return params

def get_path_real(fse):
	if fse.is_absolute():
		return fse

	return Path(sys_argv[0]).parent.joinpath(fse)

def get_path_port():

	path_port=_config_program.get("path_port")
	if path_port is not None:
		if path_port.exists():
			return path_port

	if sys_platform=="linux":

		path_port=None
		for port in ["/usr/bin/gzdoom","/usr/games/gzdoom"]:
			if Path(port).exists():
				if Path(port).is_file():
					path_port=Path(port)
					break

		if path_port is not None:
			return path_port

		path_port_local=Path(sys_argv[0]).parent.joinpath("gzdoom")
		if path_port_local.exists():
			if path_port_local.is_file():
				return path_port_local

	if sys_platform=="windows":
		path_port_local=Path(sys_argv[0]).parent.joinpath("gzdoom.exe")
		if path_port_local.exists():
			if path_port_local.is_file():
				return path_port_local

	return None

def get_games(force:bool=False)->int:

	if not (len(_list_of_games)==0 or force):
		return len(_list_of_games)

	if force:
		if len(_list_of_games)>0:
			_list_of_games.clear()

	games=[]

	for fse in Path(sys_argv[0]).parent.iterdir():
		if not fse.is_file():
			continue
		if fse.suffix.lower() not in (".yaml",".yml"):
			continue
		if fse.stat().st_size>1024*32:
			continue
		if not game_yaml_to_data(fse.read_text()):
			continue
		games.append(fse)

	if len(games)>1:
		games.sort()

	_list_of_games.extend(games)
	return len(_list_of_games)

def get_game_by_index(index:int):

	if len(_list_of_games)==0:
		get_games()

	if index>len(_list_of_games)-1:
		return None

	return _list_of_games[index]

def game_data_to_yaml(fse)->bool:

	key_name=_current_game.get("name",None)
	key_iwad=_current_game.get("iwad",None)
	if not key_name:
		return False
	if not key_iwad:
		return False

	fse.write_text(
		yaml.dump(
			_current_game,
			sort_keys=False
		)
	)
	return True

def game_yaml_to_data(text:str)->dict:
	data={}
	try:
		data.update(yaml.load(stream=text,Loader=yaml.Loader))
		assert data.get("name",None)
		assert data.get("iwad",None)
	except Exception as e:
		print(str(e))
		return {}

	return data

def game_yaml_to_data_global(text:str)->bool:

	data=game_yaml_to_data(text)

	if len(_current_game.keys())>0:
		_current_game.clear()

	_current_game.update(data)
	return True

def run_zdoom(path_zdoom,path_iwad,path_savedir,path_config,list_files=[]):

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
	path_gamedir=path_progdir.joinpath(fse_game.stem)
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
		print("Unable to find a config file")
		return False

	if not _current_game:
		if not game_yaml_to_data_global(fse_game.read_text()):
			print("Unable to read game file:",fse_game.name)
			return False
	path_iwad=get_path_real(Path(_current_game["iwad"]))

	the_list=[]
	if "file(s)" in _current_game.keys():
		for fse_str in _current_game["file(s)"]:
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
			"\n- help-program: Prints a sample config file for the program's configuration (in JSON)"
			"\n- help-game: Prints sample game file (in YAML)"
		)

		sys_exit(0)

	action=sys_argv[1].lower().strip()

	if action=="help-program":
		print("This is not clear yet")
		sys_exit(0)

	if action=="help-game":
		print(_sample_game)
		sys_exit(0)

	if action=="ui":

		print("The UI is not ready (yet)")
		sys_exit(0)

	if action=="list":

		qtty=get_games()
		if qtty==0:
			print("You have no games")
			sys_exit(0)

		count=0
		print("Index\tName")
		for fse in _list_of_games:
			print(f"{count}\t"+game_yaml_to_data(fse.read_text())["name"])
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
