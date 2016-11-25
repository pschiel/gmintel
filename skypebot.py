import Skype4Py
import MySQLdb
import time
import re
import urllib

def onAttach(status):
	print "API attachment status: " + skype.Convert.AttachmentStatusToText(status)
	if status == Skype4Py.apiAttachAvailable:
		skype.Attach()
	

def onMessageStatus(message, status):
	if status == "RECEIVED":
		print(message.FromDisplayName + ": " + message.Body)
		
		db = MySQLdb.connect(host="localhost", user="foo", passwd="bar", db="baz")
		cur = db.cursor()
		db.set_character_set('utf8')
		cur.execute('SET NAMES utf8;')
		cur.execute('SET CHARACTER SET utf8;')
		cur.execute('SET character_set_connection=utf8;')

		# attacker changes
		m = re.match("intel attackers\?", message.Body, re.I)
		if m:
			result = "Latest 20 attack score changes (2000+ points):"
			cur.execute("select distinct a.d,a.points-b.points,x.player,x.alliance from attackers a, attackers b, x_world x where a.uid=x.uid and a.last=b.id and a.points-b.points>2000 order by d desc limit 20")
			rows = cur.fetchall()
			for row in rows:
				result += "\n" + str(row[2]) + " (" + str(row[3]) + ") - " + str(row[1]) + " points on " + re.sub("(..):..:..", "\\1:00", str(row[0]))
			message.Chat.SendMessage(result)
			return
		
		# arti changes
		m = re.match("intel art(e|i)(fact)?s?\?", message.Body, re.I)
		if m:
			result = "Latest 10 artefact changes:"
			cur.execute("select a.*,b.* from artis a, artis b where a.id=b.id and a.village!=b.village and a.d>b.d order by a.d desc limit 10")
			rows = cur.fetchall()
			for row in rows:
				result += "\n" + str(row[4]) + " - " + str(row[2]) + " (" + str(row[3]) + ") conquered " + re.sub("  ", " ", str(row[0])) + " from " + str(row[8]) + " (" + str(row[9]) + ")"
			message.Chat.SendMessage(result)		
			return
		
		# intel for player
		m = re.match("intel (.*)\?", message.Body, re.I)
		if m:
			target = m.group(1)
			result = ""
			# x_world info
			cur.execute("select *,count(*),sum(population) from x_world where player='" + target + "' having count(*)>0")
			xrow = cur.fetchone()
			if xrow != None:
				result += "Player: " + xrow[7] + " - http://foo.bar.org/spieler.php?uid=" + str(xrow[6]) + "\n"
				result += "Alliance: " +xrow[9].decode("utf8").encode("latin1") + " - http://foo.bar.org/allianz.php?aid=" + str(xrow[8]) + "\n"
				villages = xrow[11]
				pop = xrow[12]
				if xrow[3] == 1:
					tribe = "Roman"
				if xrow[3] == 2:
					tribe = "Teuton"
				if xrow[3] == 3:
					tribe = "Gaul"
				
				# attack ranking
				cur.execute("select * from attackers where uid=(select uid from x_world where player='" + target + "' limit 1) order by d desc limit 1")
				row = cur.fetchone()
				if row:
					result += tribe + ", " + str(row[2]) + " villages, " + str(row[1]) + " pop, attack rank #" + str(row[5]) + "\n"
				else:
					result += tribe + ", " + str(villages) + " villages, " + str(pop) + " pop, attack rank not in top500\n"
				
				# last attack point changes
				cur.execute("select a.*,a.points-b.points from attackers a, attackers b where a.uid=" + str(xrow[6]) + " and a.last=b.id and a.points-b.points>1000 order by d desc limit 1")
				row = cur.fetchone()
				if row:
					result += "\nLast attack score change (1000+ points):\n   " + str(row[8]) + " points on " + re.sub("(..):..:..", "\\1:00", str(row[4])) + "\n"
				else:
					result += "\nLast attack score change (1000+ points):\n   no record\n"
				
				# last hero attack
				cur.execute("select * from reports r, x_world x where r.av=x.id and r.au=" + str(xrow[6]) + " and hero=1 order by r.d desc limit 1")
				row = cur.fetchone()
				heroid = 0
				if row:
					heroid = row[0]
					result += "\nLast hero attack:"
					result += "\n   " + str(row[5]) + " - http://foo.bar.org/berichte.php?id=" + str(row[0])
					if row[1] != "undefine":
						result += "|" + row[1]
					result += "\n   Attacker: " + xrow[7] #target.decode('latin1').encode('latin1')
					result += ", village: " + row[18].decode('utf8').encode('latin1')
					result += " (" + str(row[14]) + "|" + str(row[15]) + ")"
					result += "\n   Defender: "
					cur.execute("select * from x_world where id=" + str(row[9]))
					row2 = cur.fetchone()
					if row2:
						result += row2[7].decode('utf8').encode('latin1') + ", village: " + row2[5].decode('utf8').encode('latin1') + " (" + str(row2[1]) + "|" + str(row2[2]) + ")"
					result += "\n"
					atroops = str(row[2]).split("-")
					ctroops = str(row[3]).split("-")
					diff = ""
					for i in range(0, 11):
						if i < len(atroops) and not atroops[i] == "":
							diff += str(int(atroops[i]) - int(ctroops[i])) + " "
					result += "   Survivors: " + diff + "\n"
					result += "   (was: " + re.sub("-", " ", str(row[2])) + ")\n"
				else:
					result += "\nLast hero attack:\n   no record\n"
					
				# last cata attacks
				cur.execute("select * from reports r, x_world x where r.id!=" + str(heroid) + " and r.au!=r.du and r.av=x.id and r.au=" + str(xrow[6]) + " and (r.cata>0 or r.crop>5000) and r.crop>100 and r.crop=(select max(s.crop) from reports s where s.dv=r.dv and s.d>date_add(r.d,interval -3 minute) and s.d<date_add(r.d,interval 3 minute)) order by r.id desc limit 5")
				rows = cur.fetchall()
				if len(rows) > 0:
					result += "\nLast 5 major attacks (cata or 5000+ crop):"
					for row in rows:
						result += "\n   " + str(row[5]) + " - http://foo.bar.org/berichte.php?id=" + str(row[0])
						if row[1] != "undefine":
							result += "|" + row[1]
						result += "\n   Attacker: " + target + ", village: " + str(row[18]) + " (" + str(row[14]) + "|" + str(row[15]) + ")"
						result += "\n   Defender: "
						cur.execute("select * from x_world where id=" + str(row[9]))
						row2 = cur.fetchone()
						if row2:
							result += row2[7].decode("utf8") + ", village: " + row2[5].decode("utf8") + " (" + str(row2[1]) + "|" + str(row2[2]) + ")"
						result += "\n"
						atroops = str(row[2]).split("-")
						ctroops = str(row[3]).split("-")
						diff = ""
						for i in range(0, 11):
							if i < len(atroops) and not atroops[i] == "":
								diff += str(int(atroops[i]) - int(ctroops[i])) + " "
						result += "   Survivors: " + diff + "\n"
						result += "   (was: " + re.sub("-", " ", str(row[2])) + ")\n"
						leading = 0
						leadingdone = 0
						maxescort = 0
						infos = ""
						cur.execute("select * from reports r where dv=" + str(row[9]) + " and d>date_add('" + str(row[5]) + "',interval -3 minute) and d<date_add('" + str(row[5]) + "',interval 3 minute) order by id")
						rows2 = cur.fetchall()
						for row2 in rows2:
							escort = int(row2[10]) - int(row2[12])*6
							if escort > maxescort and row2[0]!=row[0]:
								maxescort = escort
							if row2[10] > 100:
								leadingdone = 1
							if leadingdone == 0:
								leading = leading+1
							infos += row2[4]+"\n"
								
						diff = rows2[len(rows2)-1][5] - rows2[0][5]
						seconds = diff.seconds + 1
						if len(rows2)>1:
							result += "   " + str(len(rows2)) + " waves in " + str(seconds) + " second"
							if seconds > 1:
								result += "s"
							if leading > 0:
								result += ", " + str(leading) + " leading fakes"
							else:
								result += ", no leading fakes"
							result += ", max escort: " + str(maxescort)
							result += "\n"
							#result += re.sub("(.*)\n", "     \\1\n", infos)
							#result += "   " + re.sub("\n", " ", infos) + "\n"
					
				else:
					result += "\nLast 5 major attacks (cata or 5000+ crop):\n   no record\n"
				
				# current incomings
				cur.execute("select * from rps where rp like '%spieler.php?uid=" + str(xrow[6]) + "\"%' and time > date_sub(now(), interval 12 hour)")
				rows = cur.fetchall()
				tmpres = ""
				result += "\nCurrent incomings from this player (rally points from last 12hrs):"
				if len(rows) > 0:
					for row in rows:
						num = len(re.findall("Attack in.*spieler\.php\?uid=" + str(xrow[6]), str(row[1])))
						if num > 0:
							tmpres += "   " + str(num) + " attack"
							if num > 1:
								tmpres += "s"
							tmpres += " on " + str(row[4]) + ", village: " + str(row[5]) + " - http://foo.bar.org/tr/viewrps/index.php?rp=" + str(row[0]) + "\n"
				if tmpres == "":
					result += "\n   none\n"
				else:
					result += "\n" + tmpres.decode("utf8")
				
				# send result
				message.Chat.SendMessage(result)
			else:
				message.Chat.SendMessage("Player not found: " + target)
				
		m = re.match("intel.*joke", message.Body, re.I)
		if m:
			file = urllib.urlopen("http://www.randomjoke.com/topic/dirty.php")
			s = file.read()
			s = re.sub("\n|\r", "", s)
			n = re.search("back to topic list\"></P><P>(.*?)<CENTER>", s)
			if n:
				joke = n.group(1)
				joke = re.sub("<p>|<blockquote>", "\n", joke)
				joke = re.sub("<.*?>", "", joke)
				message.Chat.SendMessage(joke)
		

skype = Skype4Py.Skype()
skype.OnAttachmentStatus = onAttach
skype.OnMessageStatus = onMessageStatus
skype.Attach()

while True:
	time.sleep(300.0)
