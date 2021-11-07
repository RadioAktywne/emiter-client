set("server.telnet",false)
set("server.timeout",300.)

%include "client.cfg"
ignore(telnet_port)

log(homedir)
log(cfg_broadcast_password)


#homedir = path.dirname(argv(0))
#print(socket_path)
set("server.socket",true)
set("server.socket.path",homedir^"client.sock")

set("log.stdout",true)
set("log.file.path",homedir^"liquidsoap.log") #ścieżka do loga

#cfg_file = file.contents(homedir^"/config.json")
#print(cfg_file)
#cfg = of_json(default=[("","")], cfg_file)

#log(cfg["broadcast_port"])

radio = input.http(buffer=5.,"http://listen.radioaktywne.pl:8000/ramp3")
#radio=input.jack(id="live")
radio = fallback(track_sensitive=false,[radio,blank()])

output.icecast(%mp3(bitrate=256), start=false,
  host = cfg_broadcast_host, port = cfg_broadcast_port, encoding = "UTF-8", 
  password = cfg_broadcast_password, mount = "studio",
  radio)

output.dummy(radio)

def sudoku(_)
  log("commiting sudoku")
	shutdown()
  "done"
end
server.register("sudoku",sudoku)
