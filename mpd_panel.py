#!/usr/bin/env python
import pygtk
pygtk.require('2.0')

import cgi
import sys
import gtk
import gnomeapplet
import gobject
import pynotify

from mpd import (MPDClient)

class MPDPanel(gnomeapplet.Applet):
	def mpd_idled(self, client, condition, *args):
		client.fetch_idle()
		self.update_label();
		client.send_idle('player')
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

	def __init__(self, applet, iid):
		pynotify.init("MPD Applet 0.1")
		self.applet = applet
		self.label = gtk.Label("")
		self.label.set_markup("<b>Connecting to MPD...</b>");
		self.applet.add(self.label);

		self.applet.show_all();

		self.client = MPDClient()
		self.client.connect('localhost', 6600)

		self.update_label()

		self.client.send_idle('player')
		gobject.io_add_watch(self.client, gobject.IO_IN, self.mpd_idled)

gobject.type_register(MPDPanel);

def mpd_panel_factory(applet, iid):
	applet.set_background_widget(applet)
	MPDPanel(applet, iid)
	return gtk.TRUE


if __name__ == '__main__':
	if len(sys.argv) == 2:
		if sys.argv[1] == "-d":
			main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
			main_window.set_title("Python Applet")
			main_window.connect("destroy", gtk.main_quit)
			app = gnomeapplet.Applet()
			mpd_panel_factory(app, None)
			app.reparent(main_window)
			main_window.show_all()
			gtk.main()
			sys.exit()

	gnomeapplet.bonobo_factory("OAFIID:GNOME_MPDPanel_Factory", MPDPanel.__gtype__, "MPD Applet", "0.1", mpd_panel_factory);

