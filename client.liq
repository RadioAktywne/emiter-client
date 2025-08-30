set("server.telnet",false)
set("server.timeout",300.)

%include "client.cfg"

#homedir = path.dirname(argv(0))
#print(socket_path)
set("server.socket",true)
set("server.socket.path",homedir^"/client.sock")

set("log.stdout",true)
set("log.file.path",homedir^"/liquidsoap.log")

#input source
radio = input.pulseaudio(id="emiter-virtual-source")

radio = server.insert_metadata(id="S4",radio)

output.icecast(%mp3(bitrate=256), start=false,
  host = cfg_broadcast_host, port = cfg_broadcast_port, encoding = "UTF-8", 
  password = cfg_broadcast_password, mount = "studio",
  mksafe(radio))

output.dummy(radio)

def sudoku(_)
  log("commiting sudoku")
	shutdown()
  "done"
end
server.register("sudoku",sudoku)
