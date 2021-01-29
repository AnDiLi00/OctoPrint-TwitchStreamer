# coding=utf-8
from __future__ import absolute_import

import os

import octoprint.plugin
from octoprint.util import RepeatedTimer


class TwitchstreamerPlugin(octoprint.plugin.SettingsPlugin,
						   octoprint.plugin.StartupPlugin,
						   octoprint.plugin.TemplatePlugin):
	folder = ""

	temperature_show = False
	temperature_x = 0
	temperature_y = 0
	temperature_file = "temperature.txt"
	temperature_data = None

	status_show = False
	status_x = 0
	status_y = 0
	status_file = "status.txt"
	status_data = None

	graphic_show = False
	graphic_x = 0
	graphic_y = 0
	graphic_file = ""

	twitch_key = ""

	timer = None

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			folder="~/twitchstreamer/",
			temperature_show=True,
			temperature_x=911,
			temperature_y=680,
			status_show=True,
			status_x=13,
			status_y=625,
			graphic_show=True,
			graphic_x=0,
			graphic_y=0,
			graphic_file="overlay.png",
			twitch_key=""
		)

	def on_settings_save(self, data):
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

		self.check(self._settings.get(["folder"]))

	##~~ StartupPlugin mixin

	def on_after_startup(self):
		self.check(self._settings.get(["folder"]))

	##~~ TemplatePlugin mixin

	def get_template_configs(self):
		return [{"type": "settings", "custom_bindings": False}]

	##~~ Class specific

	def check(self,
			  new_folder,
			  new_temp,
			  new_temp_x,
			  new_temp_y,
			  new_status,
			  new_status_x,
			  new_status_y,
			  new_graphic,
			  new_graphic_x,
			  new_graphic_y,
			  new_graphic_file,
			  new_twitch_key):
		changed = False

		if self.folder != new_folder:
			try:
				os.makedirs(new_folder, exist_ok=True)
				self.folder = new_folder
				changed = True
			except OSError as error:
				self._logger.error("directory {new_folder} couldn't be created".format(**locals()))

		if self.temperature_show != new_temp:
			self.temperature_show = new_temp
			changed = True

		if self.temperature_x != new_temp_x:
			self.temperature_x = new_temp_x
			changed = True

		if self.temperature_y != new_temp_y:
			self.temperature_y = new_temp_y
			changed = True

		if self.status_show != new_status:
			self.status_show = new_status
			changed = True

		if self.status_x != new_status_x:
			self.status_x = new_status_x
			changed = True

		if self.status_y != new_status_y:
			self.status_y = new_status_y
			changed = True

		if self.graphic_show != new_graphic:
			self.graphic_show = new_graphic
			changed = True

		if self.graphic_x != new_graphic_x:
			self.graphic_x = new_graphic_x
			changed = True

		if self.graphic_y != new_graphic_y:
			self.graphic_y = new_graphic_y
			changed = True

		if self.graphic_file != new_graphic_file:
			self.graphic_file = new_graphic_file
			changed = True

		if self.twitch_key != new_twitch_key:
			self.twitch_key = new_twitch_key
			changed = True

		if changed:
			self.start_timer()

	def start_timer(self):
		if self.timer:
			self.timer.cancel()
			self.timer = None

		self.timer = RepeatedTimer(5.0, self.update_values, run_first=True)
		self.timer.start()

	def update_values(self):
		self.status_data = self._printer.get_current_data()
		self.temperature_data = self._printer.get_current_temperatures()

		self.write_temperature()
		self.write_status()

	def write_temperature(self):
		write_data = ""

		if self.temperature_data:
			if "tool0" in self.temperature_data:
				write_data += "nozzle: "
				write_data += str("{:.1f}".format(self.temperature_data["tool0"]["actual"])).rjust(5)
				write_data += "°C of "
				write_data += str("{:.1f}".format(self.temperature_data["tool0"]["target"])).rjust(5)
				write_data += "°C"

			if write_data:
				write_data += "\n"

			if "bed" in self.temperature_data:
				write_data += "bed:    "
				write_data += str("{:.1f}".format(self.temperature_data["bed"]["actual"])).rjust(5)
				write_data += "°C of "
				write_data += str("{:.1f}".format(self.temperature_data["bed"]["target"])).rjust(5)
				write_data += "°C"

		self.touch(self.folder, self.temperature_file, write_data)

	def write_status(self):
		write_data = ""

		if self.status_data:
			flag_paused = False
			flag_printing = False
			flag_pausing = False
			flag_canceling = False
			flag_finishing = False

			if "state" in self.status_data:
				state_dict = self.status_data["state"]
				flags_dict = state_dict["flags"]

				flag_paused = flags_dict["paused"]
				flag_printing = flags_dict["printing"]
				flag_pausing = flags_dict["pausing"]
				flag_canceling = flags_dict["cancelling"]
				flag_finishing = flags_dict["finishing"]

				write_data += "state:   "
				write_data += state_dict["text"].lower()

			if flag_paused or flag_printing or flag_pausing or flag_canceling or flag_finishing:
				write_data += "\n"

				if "job" in self.status_data:
					job_dict = self.status_data["job"]

					if "file" in job_dict:
						if job_dict["file"]["name"] is None:
							write_data += "file:    -"
						else:
							write_data += "file:    "
							write_data += job_dict["file"]["name"]
					else:
						write_data += "file:    -"

					write_data += "\n"

				if "progress" in self.status_data:
					progress_dict = self.status_data["progress"]
					print_time = progress_dict["printTime"]
					print_time_left = progress_dict["printTimeLeft"]

					if print_time is None:
						write_data += "elapsed: 0s"
					else:
						write_data += "elapsed: "
						write_data += self.sec_to_text(print_time)

					write_data += "\n"

					if print_time_left is None:
						write_data += "left:    0s"
					else:
						write_data += "left:    "
						write_data += self.sec_to_text(print_time_left)

					write_data += "\n"

					if print_time is None or print_time_left is None:
						write_data += "percent: 0.0\%"
					else:
						float_percent = 100.0 * float(print_time / (print_time_left + print_time))

						write_data += "percent: "
						write_data += str("{:.1f}".format(float_percent))
						write_data += "\%"
			else:
				write_data = "\n\n\n\n" + write_data

		self.touch(self.folder, self.status_file, write_data)

	@staticmethod
	def touch(path, filename, data):
		if filename:
			file_tmp = open(os.path.join(path, filename), 'w+')
			file_tmp.write(data)
			file_tmp.close()

	@staticmethod
	def sec_to_text(seconds):
		result = ""

		days = seconds // 86400
		hours = (seconds - days * 86400) // 3600
		minutes = (seconds - days * 86400 - hours * 3600) // 60
		seconds = seconds - days * 86400 - hours * 3600 - minutes * 60

		if days > 0:
			result = "{}d".format(days) + "{}h".format(hours) + "{}m".format(minutes) + "{}s".format(seconds)
		elif hours > 0:
			result = "{}h".format(hours) + "{}m".format(minutes) + "{}s".format(seconds)
		elif minutes > 0:
			result = "{}m".format(minutes) + "{}s".format(seconds)
		elif seconds >= 0:
			result = "{}s".format(seconds)

		return result

	##~~ SoftwareUpdate hook

	def get_update_information(self):
		return dict(
			twitchstreamer=dict(
				displayName="Twitchstreamer Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="andili00",
				repo="OctoPrint-TwitchStreamer",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/andili00/OctoPrint-TwitchStreamer/archive/{target_version}.zip"
			)
		)


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "TwitchStreamer Plugin"
__plugin_author__ = "Andreas Pecuch"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
# __plugin_pythoncompat__ = ">=2.7,<3" # only python 2
# __plugin_pythoncompat__ = ">=3,<4" # only python 3
__plugin_pythoncompat__ = ">=2.7,<4"  # python 2 and 3


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = TwitchstreamerPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}
