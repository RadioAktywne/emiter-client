settings.server.telnet := false
settings.server.timeout := 300.

%include "client.cfg"

#homedir = path.dirname(argv(0))
#print(socket_path)
settings.server.socket := true
settings.server.socket.path := homedir^"client.sock"

settings.log.stdout := true
settings.log.file.path := homedir^"liquidsoap.log" #ścieżka do loga

#input source
radio = input.jack(id="emiter")

radio = server.insert_metadata(id="S4", radio)

studio_output = output.icecast(%mp3(bitrate=256),
  host = cfg_broadcast_host, port = cfg_broadcast_port, encoding = "UTF-8", 
  password = cfg_broadcast_password, mount = "studio",
  mksafe(radio))

# Initially stop the output
studio_output.stop()

output.dummy(radio)

# Register studio control commands
def studio_start(_)
  studio_output.start()
  "Studio started"
end

def studio_stop(_)
  studio_output.stop()
  "Studio stopped"
end

def studio_status(_)
  if studio_output.is_started() then
    "on"
  else
    "off"
  end
end

server.register("studio.start", studio_start)
server.register("studio.stop", studio_stop)
server.register("studio.status", studio_status)

def sudoku(_)
  log("commiting sudoku")
  shutdown()
  "done"
end
server.register("sudoku", sudoku)
