#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
# This is a very quick and dirty rss reader with sqlite support
##############################################################################
# This script will read rss feeds (crontab version)
##############################################################################
#    rssreader.py is a script which reads rss feeds
#    Copyright (C) 2008  Juhapekka Piiroinen & Petri Ilmarinen
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################
# Contact: 	juhapekka.piiroinen@gmail.com
# 		petri.ilmarinen@gmail.com
#############################################################################
# Release info for 
#  version 0.1 - pi
#  - rssreader must have in the database "feeds" -table
#  - database path must be absolute
#  - configuration file passed as parameter must also be absolute
#  version 0.2 - jp
#  - includes support for html generation
#  - includes support for ftp upload
#  - generates default configuration automatically
#  - divided into multiple files
############################################################################
# Version 0.2
############################################################################
import feedparser,sys,ConfigParser,os,time
from sqlite3 import dbapi2 as sqlite
import rss_config
import rss_db
import rss_www
import rss_ftp
import sys

_LOOP = 0
_DEBUG = False

if len(sys.argv)>1:
	_DEBUG = True

def p(msg):
	if (_DEBUG):
		print f(msg)

#def notify(topic,msg):
#	if (rss_config.Config().get("NOTIFICATIONS","enabled")=="1"):
#		notification_id = notifications_interface.Notify("qad_rssreader", 0, '', 
#topic, msg, dbus.Array([], signature='s'), dbus.Array([], signature='(sv)'), -1)
		

def f(data):
	return data.encode("latin1","ignore")

def rss_feed(feed,feedid):
	d = feedparser.parse(feed)
	db.write_stamp_feed(feed)
	try:
		db.update_feedtitle(feed,d.channel.title)
	except AttributeError:
		pass
	try:
		if db.read_feedimage(feedid)==None:
			db.update_feedimage(feedid,d.channel.image)
#		print "Feed image available!"
	except AttributeError:
#		print "No image available!"
		pass #no image available
	feeds = db.read_newslinks()
	p("Total items: "+str(len(feeds)))
	news = ""
	for entry in d.entries:
		if not entry.link in feeds:
			p("Adding new link "+entry.link)
			db.write_table(entry.title,entry.link,feedid)
			news = "<a href=\""+entry.link+"\">"+entry.title+"</a>"
#			notify(d.channel.title,news)

if __name__ == "__main__":
	force = False
	if len(sys.argv)>1:
		if sys.argv[1]=="-f":
			force = True
#	if not _DEBUG:
#		#do first fork
#		try: 
#       		pid = os.fork() 
#	        	if pid > 0:
#	        	    # exit first parent
#       		    sys.exit(0) 
#	    	except OSError, e: 
#       		print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror) 
#	        	sys.exit(1)
#	
#		#os.chdir("/") 
#		#os.setsid() 
#		#os.umask(0) 
#
#	    	# do second fork
#    		try: 
#	        	pid = os.fork() 
#        		if pid > 0:
#            			# exit from second parent, print eventual PID before
#           			print "Daemon PID %d" % pid 
#	            		sys.exit(0) 
#    		except OSError, e: 
#	        	print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, 
#e.strerror) 
#        		sys.exit(1)

	p("Starting qad_rssreader..")
#	if (rss_config.Config().get("NOTIFICATIONS","enabled")=="1"):#
#		try:
#			import dbus
#			session_bus = dbus.SessionBus()
#			notifications_object = 
#session_bus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
#			notifications_interface = dbus.Interface(notifications_object, 
#'org.freedesktop.Notifications')
#		except dbus.DBusException, e:
#			print "Error: %s" % str(e)
	while (_LOOP==0):
		
		c = rss_config.Config()
		db_things = c.read_conf()
	
		db = rss_db.db_connection(db_things[0])
		newslinks = db.read_newslinks()
		feeds = db.read_feeds(db_things[1])
	
		for feed in feeds:
			p("")
			p("Reading feed: "+feed[1])
			p("Feed id: "+str(feed[2]))
			rss_feed(feed[0],feed[2])
		
		if force or (len(newslinks)!=len(db.read_newslinks())):
			p("Generating html file.")
			tmpfolder = c.get("GENERAL","tempfolder")
			if (os.path.exists(tmpfolder)==False):
				os.mkdir(tmpfolder)
			localfile = tmpfolder+c.get("HTML","filename")
			www = rss_www.document(filename=localfile)
			www.generate(feeds=db.read_latest(150))
			otherfiles = www.files()
			del www
#			print otherfiles
			feeds = db.read_allfeeds()
			for feed in feeds:
				filename="tmp/"+feed[3].lower().replace(" ","")+".php"
				www = rss_www.document(filename=filename)
				www.generate(feeds=db.read_latestFromFeed(feed[0],amount=100))
				del www
				otherfiles.append(filename)
			server = c.get("FTP","server")
			username = c.get("FTP","username")
			password = c.get("FTP","password")
			path = c.get("FTP","path")
			p("Uploading to "+server)
			ftp = rss_ftp.ftp_upload(server=server,username=username,password=password,path=path)
#			print localfile
			ftp.upload(localfile)
			for filen in otherfiles:
#				print filen
				ftp.upload(filen)
			del ftp
						
#		p("Sleeping for "+str(db_things[3])+" seconds")
#		time.sleep(db_things[3])
		_LOOP = 1
