#!/usr/bin/env python
import pygtk
pygtk.require('2.0')

import cgi
import sys
import logging
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

	logging.basicConfig(level=logging.DEBUG)

	configuration = {
		"host"   : "localhost",
		"port"   : 6600,
		"retry"  : 10,
		"secret" : False
	}

	def show_notification(self, title, text):
		if self.__notification is None:
			try:
				import pynotify
				self.__notification = pynotify.Notification (" ", "", "/usr/share/panflute/panflute.svg")
				self.__notification.set_urgency(pynotify.URGENCY_LOW)
			except ImportError, e:
				return

		self.__notification.update(title, text, "/usr/share/panflute/panflute.svg")
		self.__notification.show()

	def mpd_idled(self, client, condition, *args):
		logging.debug('mpd_idled')
		idled = client.fetch_idle()
		if idled[0] == "player":
			self.update_label();
			client.send_idle("player")

		return True

	def update_label(self):
		logging.debug('update_label')
		output = "";
		status = self.__mpdclient.status()

		if status["state"] == "play":
			current = self.__mpdclient.currentsong()
			output = cgi.escape(current["name"]) + ': ' + cgi.escape(current["title"]) + ''
			self.show_notification(current["name"], current["title"])
		if status["state"] == "pause":
			current = self.__mpdclient.currentsong()
			if current["file"].startswith("http://"):
				output = "MPD Paused"
		if status["state"] == "stop":
			output = "MPD Stopped"

		if output != "":
			self.__label.set_markup(output)

	def connect(self, *args):
		"""
		Attempt to connect to MPD
		"""
		logging.debug('connect')
		try:
			self.__mpdclient.connect(self.configuration["host"], self.configuration["port"])
		except SocketError:
			self.__label.set_markup("<b>Conneccting to MPD...</b> - Socket Error - Retrying")
			gobject.timeout_add(self.configuration["retry"] * 1000, self.connect)
			return False

		if self.configuration["secret"]:
			try:
				self.__mpdclient.password(self.configuration["secret"])
			except CommandError:
				self.__label.set_markup("<b>Connecting to MPD...</b> - Authentication error")
				gobject.timeout_add(self.configuration["retry"] * 1000, self.connect)
				return False

		self.update_label()
		self.__mpdclient.send_idle('player')
		gobject.io_add_watch(self.__mpdclient, gobject.IO_IN, self.mpd_idled)
		return False

	def __init__(self, applet, iid):
		logging.debug('__init__')

		self.__applet = applet
		self.__mpdclient = MPDClient();

		applet.set_border_width(0)
		applet.set_background_widget(applet) # Transparency hack?

		try:
			import pynotify;
			pynotify.init(self.title)
		except ImportError, e:
			self.log.warn("Couldn't initialize notifications: {0}".format(e))

		self.__notification = None

		applet.set_applet_flags(gnomeapplet.EXPAND_MINOR | gnomeapplet.EXPAND_MAJOR | gnomeapplet.HAS_HANDLE)

		hbox = gtk.HBox ()
		label = gtk.Label("<b>Connecting</b>")
		hbox.pack_start(label, True, True)
		applet.add(hbox)
		hbox.show();
		applet.show_all()

		self.__label = label
		self.connect()


gobject.type_register(MPDPanel);

def mpd_panel_factory(applet, iid):
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

