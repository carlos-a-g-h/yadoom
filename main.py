#!/usr/bin/python3.9

import subprocess

from pathlib import Path
from sys import argv as sys_argv
from sys import exit as sys_exit

# from internals import cached_game_update
from internals import create_gameslist
from internals import game_yaml_to_data
from internals import get_game_by_index
from internals import get_path_program
from internals import get_path_srcport
from internals import get_path_real
from internals import program_config_read
from internals import program_config_write
from internals import update_cached_config
# from internals import update_gameslist
from internals import util_yaml_read
# from internals import util_yaml_write

from tui import UI_SetupSourcePortNOW

# from textual.app import App
# from textual.widgets import Footer, Header

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

def run_srcport(
		path_srcport,
		path_iwad,
		path_savedir,
		path_config,
		extra_files=[]
	):

	print(f"\nRunning: {path_srcport.name}\n\tIWAD:\n\t\t{str(path_iwad)}")
	cmd_line=[
		str(path_srcport),
		"-savedir",str(path_savedir),
		"-config",str(path_config),
		"-iwad",str(path_iwad),
	]
	if len(extra_files)>0:
		print("\nFile(s):")
		cmd_line.append("-file")
		for fse in extra_files:
			print(f"\t{str(fse)}")
			cmd_line.append(str(fse))

	print("\n$",cmd_line)

	proc=subprocess.run(cmd_line)

	return proc.returncode

def main_run(fse_game,path_srcport):

	path_program=get_path_program()
	path_progdir=path_program.parent
	in_library=fse_game.is_relative_to(path_progdir)

	print("In library?",{True:"Yes",False:"No"}[in_library])

	path_offset={
		True:path_progdir,
		False:fse_game.parent
	}[in_library]

	path_games={
		True:path_offset.joinpath(f"{path_program.stem}.games"),
		False:path_offset
	}[in_library]

	path_game_dir=path_games.joinpath(fse_game.stem)
	path_game_savedir=path_game_dir.joinpath("savegames")
	path_game_config=path_game_dir.joinpath("config.ini")

	path_game_savedir.mkdir(parents=True,exist_ok=True)
	if path_game_config.exists():
		if not path_game_config.is_file():
			print("[ ERROR ] Not a file:",str(path_game_config))
			return False

	if not path_game_config.exists():
		path_game_config_local=path_progdir.joinpath("config.ini")
		if path_game_config_local.exists():
			if path_game_config_local.is_file():
				path_game_config.write_bytes(
					path_game_config_local.read_bytes()
				)

	if not path_game_config.exists():
		print(
			"[ WARNING ] No config file was found\
			\nThe selected game will use the default config provided by the source port\
			\nDon't complain"
		)

	data=game_yaml_to_data(fse_game)
	if not data:
		print("[ ERROR ] Failed to load game")
		return False

	path_iwad=get_path_real(
		path_offset,
		Path(data["iwad"].strip())
	)

	the_list=[]
	files_raw=data.get("file(s)")
	if isinstance(files_raw,list):
		for fse_str in files_raw:
			if not isinstance(fse_str,str):
				continue

			fse_str=fse_str.strip()
			if len(fse_str)==0:
				continue

			the_list.append(
				get_path_real(
					path_offset,
					Path(fse_str)
				)
			)

	return_code=run_srcport(
		path_srcport,
		path_iwad,
		path_game_savedir,
		path_game_config,
		extra_files=the_list
	)

	print("ReturnCode:",return_code)

	return return_code==0

# def validate_filepath(path):
# 	if not path:
# 		return False
# 	if not path.is_file():
# 		return False
# 	if path.absolute()==Path(sys_argv[0]).absolute():
# 		return False
# 	return True

# class Validator_Filepath(Validator):
# 	def validate(self,value:str)->ValidationResult:

# 		if not validate_filepath(Path(value)):
# 			return self.failure("The file does not exist")

# 		return self.success()

# class QuickForm_SourcePort(App):

# 	CSS="Label,Input,Button,Select { margin:1 }\n#cancel { dock:right; }"

# 	path_last_visited=Path(sys_argv[0]).parent
# 	path_selected=None

# 	def compose(self)->ComposeResult:
# 		yield Label(
# 			"There is no source port to be found!\
# 			\nGo find it somewhere on the computer or type the path yourself by hand"
# 		)
# 		with Horizontal():
# 			yield Select.from_values(
# 				get_places(),
# 				prompt="Select where to open the picker"
# 			)
# 			yield Button(label="Open",id="search")

# 		yield Input(
# 			placeholder="Path to ZDoom/GZDoom executable",
# 			validators=[Validator_Filepath()],
# 			validate_on=["submitted"],
# 		)

# 		with Horizontal():
# 			yield Button(label="Confirm",id="accept")
# 			yield Button(label="Exit",id="cancel")

# 	def save_selected_path(self,filepath):
# 		if not filepath:
# 			return

# 		self.path_selected=filepath
# 		self.path_last_visited=filepath.parent

# 		widget_input=self.query_one(Input)
# 		widget_input.clear()
# 		widget_input.insert_text_at_cursor(str(filepath))

# 	@on(Button.Pressed,"#search")
# 	def form_openfile(self):
# 		start_point=self.query_one(Select).value
# 		if start_point==Select.BLANK:
# 			start_point=self.path_last_visited

# 		the_filters={
# 			True:Filters(
# 				("Windows executable",lambda p:p.suffix.lower()==".exe")
# 			),
# 			False:None
# 		}[sys_platform=="win32"]

# 		self.push_screen(
# 			FileOpen(
# 				start_point,
# 				filters=the_filters
# 			),
# 			callback=self.save_selected_path
# 		)

# 	@on(Button.Pressed,"#accept")
# 	def form_proceed(self):
# 		if not validate_filepath(self.path_selected):
# 			self.notify("The given path is not valid")
# 			return

# 		self.exit(self.path_selected)

# 	@on(Button.Pressed,"#cancel")
# 	def form_bail(self):
# 		self.exit()

# def launch_quickform_sourceport():
# 	path_source_port=QuickForm_SourcePort().run()
# 	if not path_source_port:
# 		return False

# 	_cached_config.update({"path_port":path_source_port})

# 	data_ok={}

# 	for key in _cached_config.keys():
# 		if type(_cached_config[key]) is not str:
# 			data_ok.update({key:str(_cached_config[key])})
# 			continue

# 		data_ok.update({key:_cached_config[key]})

# 	path_program=Path(sys_argv[0])

# 	try:
# 		util_yaml_write(
# 			path_program.parent.joinpath(f"{path_program.stem}.yaml"),
# 			data_ok
# 		)
# 	except Exception as e:
# 		print("WARNING: Failed to write the new config file;",str(e))
# 		pass

# 	return True

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

		games=create_gameslist()
		if len(games)==0:
			print("You have no games")
			sys_exit(1)

		index=0
		print("Index\tName")
		for fse in games:
			print(f"{index}\t"+util_yaml_read(filepath=fse)["name"])
			index=index+1

		print(
			f"\nTo run a game:\
			\n$ {sys_argv[0]} run -i N\
			\nN = Game index"
		)

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

		# path_program=Path(sys_argv[0])

		program_config_read()

		update_config_at_the_end=False
		path_srcport=get_path_srcport()
		if not path_srcport:
			path_srcport_str=UI_SetupSourcePortNOW().run()
			if not path_srcport_str:
				print("Path to source port binary not found")
				sys_exit(1)

			path_srcport=Path(path_srcport_str)

			update_config_at_the_end=True
			update_cached_config({"path_srcport":str(path_srcport)})

		print(f"Path to source port:\n\t{path_srcport}")

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

			fse_game=get_game_by_index(
				int(args["-i"])
			)

		if "-f" in args.keys():
			fse_game=Path(args["-f"])

		if not fse_game:
			print("The game does not exist")
			sys_exit(1)

		ok=main_run(fse_game,path_srcport)
		if ok and update_config_at_the_end:
			program_config_write()

		sys_exit({True:0,False:1}[ok])

	print("Unknown action")
	sys_exit(1)
