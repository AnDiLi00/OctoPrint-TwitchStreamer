# coding=utf-8
from __future__ import absolute_import

import os
import shlex
import subprocess

import octoprint.plugin
from octoprint.events import Events
from octoprint.util import RepeatedTimer
from octoprint.util import ResettableTimer


class TwitchstreamerPlugin(octoprint.plugin.SettingsPlugin, octoprint.plugin.StartupPlugin,
						   octoprint.plugin.TemplatePlugin, octoprint.plugin.EventHandlerPlugin):
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

	webcam_path = ""
	twitch_key = ""

	quality = ""
	bitrate = ""

	font = ""
	font_size = 0

	update_timer = None
	end_timer = None

	process = None
	streaming = False

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			folder="/home/pi/twitchstreamer/",
			temperature_show=True,
			temperature_x=911,
			temperature_y=680,
			status_show=True,
			status_x=13,
			status_y=625,
			graphic_show=True,
			graphic_x=1202,
			graphic_y=640,
			graphic_file="/home/pi/twitchstreamer/overlay.png",
			webcam_path="http://octopi.local/webcam/?action=stream",
			twitch_key="",
			quality="medium",
			bitrate="1000",
			font="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
			font_size=18
		)

	def on_settings_save(self, data):
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

		self.check_settings(self._settings.get(["folder"]),
							self._settings.get(["temperature_show"]),
							self._settings.get(["temperature_x"]),
							self._settings.get(["temperature_y"]),
							self._settings.get(["status_show"]),
							self._settings.get(["status_x"]),
							self._settings.get(["status_y"]),
							self._settings.get(["graphic_show"]),
							self._settings.get(["graphic_x"]),
							self._settings.get(["graphic_y"]),
							self._settings.get(["graphic_file"]),
							self._settings.get(["webcam_path"]),
							self._settings.get(["twitch_key"]),
							self._settings.get(["quality"]),
							self._settings.get(["bitrate"]),
							self._settings.get(["font"]),
							self._settings.get(["font_size"]))

	##~~ StartupPlugin mixin

	def on_after_startup(self):
		self.check_settings(self._settings.get(["folder"]),
							self._settings.get(["temperature_show"]),
							self._settings.get(["temperature_x"]),
							self._settings.get(["temperature_y"]),
							self._settings.get(["status_show"]),
							self._settings.get(["status_x"]),
							self._settings.get(["status_y"]),
							self._settings.get(["graphic_show"]),
							self._settings.get(["graphic_x"]),
							self._settings.get(["graphic_y"]),
							self._settings.get(["graphic_file"]),
							self._settings.get(["webcam_path"]),
							self._settings.get(["twitch_key"]),
							self._settings.get(["quality"]),
							self._settings.get(["bitrate"]),
							self._settings.get(["font"]),
							self._settings.get(["font_size"]))

	##~~ TemplatePlugin mixin

	def get_template_configs(self):
		return [{"type": "settings", "custom_bindings": False}]

	##~~ EventHandlerPlugin mixin

	def on_event(self, event, payload):
		if event == Events.PRINT_STARTED:
			self._logger.info("on_event - Events.PRINT_STARTED")
			self.print_start()
		elif event == Events.PRINT_FAILED:
			self._logger.info("on_event - Events.PRINT_FAILED")
			self.print_end(True)
		elif event == Events.PRINT_DONE:
			self._logger.info("on_event - Events.PRINT_DONE")
			self.print_end(False)

	##~~ Class specific

	def check_settings(self, new_folder, new_temperature, new_temperature_x, new_temperature_y,
					   new_status, new_status_x, new_status_y, new_graphic, new_graphic_x, new_graphic_y,
					   new_graphic_file, new_webcam_path, new_twitch_key, new_quality, new_bitrate,
					   new_font, new_font_size):
		self._logger.info("check_settings - new settings")
		self._logger.info("-- folder={}".format(new_folder))
		self._logger.info("-- temperature")
		self._logger.info("-- -- show={}".format(new_temperature))
		self._logger.info("-- -- x={}".format(new_temperature_x))
		self._logger.info("-- -- y={}".format(new_temperature_y))
		self._logger.info("-- status")
		self._logger.info("-- -- show={}".format(new_status))
		self._logger.info("-- -- x={}".format(new_status_x))
		self._logger.info("-- -- y={}".format(new_status_y))
		self._logger.info("-- graphic")
		self._logger.info("-- -- show={}".format(new_graphic))
		self._logger.info("-- -- x={}".format(new_graphic_x))
		self._logger.info("-- -- y={}".format(new_graphic_y))
		self._logger.info("-- -- file={}".format(new_graphic_file))
		self._logger.info("-- webcam={}".format(new_webcam_path))
		self._logger.info("-- twitchkey={}".format(new_twitch_key))
		self._logger.info("-- quality={}".format(new_quality))
		self._logger.info("-- bitrate={}".format(new_bitrate))
		self._logger.info("-- font={}".format(new_font))
		self._logger.info("-- font size={}".format(new_font_size))

		changed = False

		if self.folder != new_folder:
			self.remove_file(self.folder, self.temperature_file)
			self.remove_file(self.folder, self.status_file)
			self.remove_path(self.folder)

			self.folder = new_folder
			changed = True

		if self.temperature_show != new_temperature:
			self.temperature_show = new_temperature
			changed = True

		if self.temperature_x != new_temperature_x:
			self.temperature_x = new_temperature_x
			changed = True

		if self.temperature_y != new_temperature_y:
			self.temperature_y = new_temperature_y
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

		if self.webcam_path != new_webcam_path:
			self.webcam_path = new_webcam_path
			changed = True

		if self.twitch_key != new_twitch_key:
			self.twitch_key = new_twitch_key
			changed = True

		if self.quality != new_quality:
			self.quality = new_quality
			changed = True

		if self.bitrate != new_bitrate:
			self.bitrate = new_bitrate
			changed = True

		if self.font != new_font:
			self.font = new_font
			changed = True

		if self.font_size != new_font_size:
			self.font_size = new_font_size
			changed = True

		self.updatetimer_start()

		if changed and self.streaming:
			self.print_start()

	def update_temperature(self):
		data = ""

		if self.temperature_data:
			if "tool0" in self.temperature_data:
				data += "nozzle: "
				data += str("{:.1f}".format(self.temperature_data["tool0"]["actual"])).rjust(5)
				data += "°C of "
				data += str("{:.1f}".format(self.temperature_data["tool0"]["target"])).rjust(5)
				data += "°C"

			if data:
				data += "\n"

			if "bed" in self.temperature_data:
				data += "bed:    "
				data += str("{:.1f}".format(self.temperature_data["bed"]["actual"])).rjust(5)
				data += "°C of "
				data += str("{:.1f}".format(self.temperature_data["bed"]["target"])).rjust(5)
				data += "°C"

		self.touch_file(self.folder, self.temperature_file, data)

	def update_status(self):
		data = ""

		if self.status_data:
			printing_state = False

			if "state" in self.status_data:
				state_dict = self.status_data["state"]
				flags_dict = state_dict["flags"]

				if flags_dict["cancelling"] or flags_dict["finishing"] or flags_dict["paused"] or flags_dict[
					"pausing"] or flags_dict["printing"]:
					printing_state = True

				data += "state:   "
				data += state_dict["text"].lower()

			if printing_state:
				data += "\n"

				if "job" in self.status_data:
					job_dict = self.status_data["job"]

					if "file" in job_dict:
						if job_dict["file"]["name"]:
							data += "file:    "
							data += job_dict["file"]["name"]
						else:
							data += "file:    -"
					else:
						data += "file:    -"

					data += "\n"

				if "progress" in self.status_data:
					progress_dict = self.status_data["progress"]
					print_time = progress_dict["printTime"]
					print_time_left = progress_dict["printTimeLeft"]

					if print_time:
						data += "elapsed: "
						data += self.sec_to_text(print_time)
					else:
						data += "elapsed: 0s"

					data += "\n"

					if print_time_left:
						data += "left:    "
						data += self.sec_to_text(print_time_left)
					else:
						data += "left:    0s"

					data += "\n"

					if print_time and print_time_left:
						float_percent = 100.0 * float(print_time / (print_time_left + print_time))
						data += "percent: {:.1f}\%".format(float_percent)
					else:
						data += "percent: 0.0\%"
			else:
				data = "\n\n\n\n" + data

		self.touch_file(self.folder, self.status_file, data)

	def update_values(self):
		self.status_data = self._printer.get_current_data()
		self.temperature_data = self._printer.get_current_temperatures()

		self.update_temperature()
		self.update_status()

	def updatetimer_stop(self):
		if self.update_timer:
			self.update_timer.cancel()
			self.update_timer = None

	def updatetimer_start(self):
		self.updatetimer_stop()

		self.update_timer = RepeatedTimer(5.0, self.update_values, run_first=True)
		self.update_timer.start()

	def stream_start(self):
		filepath_temperature = self.folder + self.temperature_file
		filepath_status = self.folder + self.status_file
		filepath_graphic = self.graphic_file

		command = "ffmpeg -i {self.webcam_path} -i {filepath_graphic} "

		if self.temperature_show or self.status_show or self.graphic_show:
			command += "-filter_complex \"[0:v]"

		if self.temperature_show:
			command += "drawtext=fontfile={self.font}:textfile={filepath_temperature}:"
			command += "x={self.temperature_x}:y={self.temperature_y}:reload=1:"
			command += "fontcolor=white:fontsize={self.font_size}[vtxt1]"
			if self.status_show or self.graphic_show:
				command += ";[vtxt1]"

		if self.status_show:
			command += "drawtext=fontfile={self.font}:textfile={filepath_status}:"
			command += "x={self.status_x}:y={self.status_y}:reload=1:"
			command += "fontcolor=white:fontsize={self.font_size}[vtxt2]"
			if self.graphic_show:
				command += ";[vtxt2]"

		if self.graphic_show:
			command += "[1:v]overlay=x={self.graphic_x}:y={self.graphic_y}[out]\" "
		elif self.temperature_show or self.status_show:
			command += "\" "

		command += "-vcodec libx264 -pix_fmt yuv420p -threads 0 -bufsize 512k "
		command += "-preset {self.quality} -g 20 -b:v {self.bitrate}k -map \""

		if self.graphic_show:
			command += "[out]"
		elif self.status_show:
			command += "[vtxt2]"
		elif self.temperature_show:
			command += "[vtxt2]"
		else:
			command += "[0:v]"

		command += "\" -f flv rtmp://live.twitch.tv/app/{self.twitch_key}"

		command_formated = command.format(**locals())
		self.process = subprocess.Popen(shlex.split(command_formated))

		self._logger.info("stream_start - pid={} - command={}".format(self.process.pid, command_formated))

	def stream_end(self):
		if self.process:
			#os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
			self.process.terminate()
			self.process = None

		self._logger.info("stream_end")

	def print_start(self):
		self._logger.info("print_start")

		self.stream_end()

		if self.end_timer:
			self.end_timer.cancel()

		self.streaming = True
		self.stream_start()

	def print_end(self, forced):
		self._logger.info("print_end - forced={}".format(forced))

		self.streaming = False

		if forced:
			self.stream_end()
		else:
			if self.end_timer:
				self.end_timer.reset()
			else:
				self.end_timer = ResettableTimer(60.0, self.stream_end)
				self.end_timer.start()

	def touch_path(self, path):
		if path:
			if os.path.exists(path):
				pass
			else:
				try:
					os.makedirs(path, exist_ok=True)
				except OSError as error:
					self._logger.error("path '{}' couldn't be created - errno:{}".format(path, error.errno))
		else:
			self._logger.error("path not valid")

	def remove_path(self, path):
		if path:
			if os.path.exists(path) and os.path.isdir(path):
				if not os.listdir(path):
					try:
						os.rmdir(path)
					except OSError as error:
						self._logger.error("path '{}' couldn't be removed - errno:{}".format(path, error.errno))
			else:
				self._logger.error("path does not exist")
		else:
			self._logger.error("path not valid")

	def touch_file(self, path, file, data):
		joined = os.path.join(path, file)

		if path:
			if file:
				self.touch_path(path)

				try:
					file_tmp = open(joined, 'w+')
					file_tmp.write(data)
					file_tmp.close()
				except OSError as error:
					self._logger.error("file '{}' couldn't be created - errno:{}".format(joined, error.errno))
			else:
				self._logger.error("file not valid")
		else:
			self._logger.error("path not valid")

	def remove_file(self, path, file):
		joined = os.path.join(path, file)

		if path:
			if file:
				if os.path.exists(joined):
					try:
						os.remove(joined)
					except OSError as error:
						self._logger.error("file '{}' couldn't be removed - errno:{}".format(joined, error.errno))
				else:
					self._logger.error("file does not exist")
			else:
				self._logger.error("file not valid")
		else:
			self._logger.error("path not valid")

	@staticmethod
	def sec_to_text(seconds):
		result = ""

		days = seconds // 86400
		hours = (seconds - days * 86400) // 3600
		minutes = (seconds - days * 86400 - hours * 3600) // 60
		seconds = seconds - days * 86400 - hours * 3600 - minutes * 60

		if days > 0:
			result = "{}d{}h{}m{}s".format(days, hours, minutes, seconds)
		elif hours > 0:
			result = "{}h{}m{}s".format(hours, minutes, seconds)
		elif minutes > 0:
			result = "{}m{}s".format(minutes, seconds)
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
