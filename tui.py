#!/usr/bin/python3.9

from pathlib import Path

from datetime import datetime

from textual import on
from textual.app import App,ComposeResult
# from textual.screens import Screen
from textual.containers import Container,Horizontal
# from textual.vion import ValidationResult,Validator
from textual.widgets import Button,Label,Select,Static
from textual_fspicker import FileOpen,Filters

from internals import get_list_of_places
from internals import get_path_program
from internals import get_sys_platform

def only_when_its_dark():
	h=datetime.now().hour
	return (h<7 or h>18)

class UI_SetupSourcePortNOW(App):

	TITLE="YAZDOOM"

	CSS="""
	Button,Container,Input,Label,Select,#selected_path { margin:2; }
	#open_picker { dock:right; }
	#selected_path { text-align:center; }
	Button.btn { content-align: center middle; }
	"""

	# /*
	# 	Container.bbt { content-align: center middle; }
	# */
	# """

	dark=only_when_its_dark()

	path_program=get_path_program()
	path_cached=path_program.parent
	path_selected=None

	def get_places(self):
		places=get_list_of_places()
		platform=get_sys_platform()
		if platform=="linux":
			places.extend([
				Path("/usr/bin/"),
				Path("/usr/games/"),
				Path("/")
			])
		return places

	def save_selected(self,filepath):
		if not filepath:
			return

		self.path_selected=filepath
		self.path_cached=filepath.parent

		self.query_one("#selected_path").update(
			f"[b]Selected Path[/b]: {str(filepath)}"
		)

	def check_filepath(self,filepath:Path)->bool:
		if not filepath.exists():
			return False

		if not filepath.is_file():
			return False

		return True

	def compose(self)->ComposeResult:
		yield Label(
			"The ZDoom/GZDoom executable was not found in the config"
		)
		yield Horizontal(
			Select.from_values(
				self.get_places(),
				prompt="Select a place"
			),
			Button(
				"Open file picker at the selected place",
				id="open_picker"
			)
		)
		yield Static("",id="selected_path")
		yield Horizontal(
			Container(
				Button(
					"Confirm",
					id="confirm",
					classes="btn"
				),classes="bbt"
			),
			Container(
				Button(
					"Cancel",
					id="cancel",
					classes="btn"
				),classes="bbt"
			),
			id="bottom_btns"
		)

	@on(Button.Pressed,"#open_picker")
	def open_picker(self):
		place=self.query_one(Select).value
		if place==Select.BLANK:
			place=self.path_cached

		the_filters={
			True:Filters(
				("Windows .EXE",lambda p: p.suffix.lower() == ".exe")
			),
			False:None
		}[get_sys_platform()=="win32"]

		self.push_screen(
			FileOpen(
				place,
				filters=the_filters
			),
			callback=self.save_selected
		)

	@on(Button.Pressed,"#confirm")
	def btn_confirm(self):
		if not self.path_selected:
			self.notify(
				"Select a path using the file picker",
				severity="error"
			)
			return
		if not self.check_filepath(self.path_selected):
			self.notify(
				"The path is not valid",
				severity="error"
			)
			return

		self.exit(self.path_selected)

	@on(Button.Pressed,"#cancel")
	def btn_cancel(self):
		self.exit()

