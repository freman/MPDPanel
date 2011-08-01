#!/usr/bin/env python
import pygtk
pygtk.require('2.0')

import cgi
import sys
import gtk
import gnomeapplet
import gobject
import pynotify

from mpd import (MPDClient, CommandError)
from socket import error as SocketError


class MPDPanel(gnomeapplet.Applet):
	"""
	MPD Panel main class
	"""
	title = "MPD Panel"
	version = "0.1"

	configuration = {
		"host"   : "localhost",
		"port"   : 6600,
		"retry"  : 10,
		"secret" : False
	}

	def mpd_idled(self, client, condition, *args):
		idled = client.fetch_idle()
		if idled[0] == "player":
			self.update_label();
			client.send_idle("player")

		return True

	def update_label(self):
		output = "";
		status = self.client.status()

		if status["state"] == "play":
			current = self.client.currentsong()
			output = cgi.escape(current["name"]) + ': ' + cgi.escape(current["title"]) + ''
			notification = pynotify.Notification(current["name"], current["title"], "/usr/share/panflute/panflute.svg")
			notification.set_timeout(3)
			notification.show()
		if status["state"] == "pause":
			current = self.client.currentsong()
			if current["file"].startswith("http://"):
				output = "MPD Paused"
		if status["state"] == "stop":
			output = "MPD Stopped"

		if output != "":
			self.label.set_markup(output)

	def connect(self, *args):
		"""
		Attempt to connect to MPD
		"""
		try:
			self.client.connect(self.configuration["host"], self.configuration["port"])
		except SocketError:
			self.label.set_markup("<b>Conneccting to MPD...</b> - Socket Error - Retrying")
			gobject.timeout_add(self.configuration["retry"] * 1000, self.connect)
			return False

		if self.configuration["secret"]:
			try:
				self.client.password(self.configuration["secret"])
			except CommandError:
				self.label.set_markup("<b>Connecting to MPD...</b> - Authentication error")
				gobject.timeout_add(self.configuration["retry"] * 1000, self.connect)
				return False

		self.update_label()
		self.client.send_idle('player')
		gobject.io_add_watch(self.client, gobject.IO_IN, self.mpd_idled)
		return False


	def __init__(self, applet, iid):
		pynotify.init("MPD Applet 0.1")
		self.applet = applet
		self.label = gtk.Label("")
		self.label.set_alignment (0.5, 0.5)
		self.label.set_markup("<b>Connecting to MPD...</b>")
		self.applet.add(self.label)
		self.applet.show_all()
		self.client = MPDClient();
		self.connect()

gobject.type_register(MPDPanel);

def mpd_panel_factory(applet, iid):
	applet.set_border_width(0)
	applet.set_background_widget(applet)
	applet.set_flags(gnomeapplet.HAS_HANDLE | gnomeapplet.EXPAND_MINOR)
	MPDPanel(applet, iid)
	return gtk.TRUE


if __name__ == '__main__':
	if len(sys.argv) == 2:
		if sys.argv[1] == "-d":
			main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
			main_window.set_title(MPDPanel.title + " Window")
			main_window.connect("destroy", gtk.main_quit)
			app = gnomeapplet.Applet()
			mpd_panel_factory(app, None)
			app.reparent(main_window)
			main_window.show_all()
			gtk.main()
			sys.exit()

	gnomeapplet.bonobo_factory("OAFIID:GNOME_MPDPanel_Factory", MPDPanel.__gtype__, MPDPanel.title, MPDPanel.version, mpd_panel_factory);

