# emiter-client

GUI dla komputera emisyjnego do połączenia z serwerem emisji Emiter (https://github.com/radioaktywne/emiter) na systemy Linux.

## Co potrafi emiter-client

Emiter-client zbiera stream audio z JACKa i emituje go jako substream Icecast2 na podany w configu serwer. 
Jednocześnie pobiera z API listę audycji i zarządza metadanymi w sposób kompatybilny z Emiterem.

## Jak działa?

Emiter-client'a zbudowano w Pythonie na silniku PyQt5. GUI zbuildowano z użyciem Qt Designera. 
GUI zarządza skryptem w Liquidsoapie przez socat, a Liquidsoap streamuje audio na serwer.

## Instalacja

Pobranie repo

```
git clone https://github.com/radioaktywne/emiter-client
cd emiter-client
```

#### Prerekwizyty

* Przed instalacją należy zainstalować pakiet **Liquidsoap w wersji co najmniej 1.4.3** (https://www.liquidsoap.info/doc-1.4.3/). W przypadku Ubuntu zwykle wystarczające jest:
```
sudo apt-get update
sudo apt-get install liquidsoap
```
W pozostałych przypadkach instalację opisano w https://www.liquidsoap.info/doc-1.4.3/install.html 

* Należy zainstalować pakiet PyQt5 (na systemach Ubuntu powinien być preinstalowany)

* Pozostałe pakiety instalujemy poprzez skrypty `INSTALL.sh` i `DEVINSTALL.sh` - ten drugi doinstalowuje narzędzia deweloperskie (m.in. Qt Designera)

## Konfiguracja

#### Konfiguracja połączenia
Należy skopiować `client.cfg.example` na `client.cfg` i wprowadzić:
* `homedir` - miejesce umieszczenia kodu
* `cfg_broadcast_host` - URL serwera
* `cfg_broadcast_port` - port dosyłu
* `cfg_broadcast_password` - hasło dosyłu

Oprócz tego należy skonfigurować API edytując plik `client.py`

```
#API path
api_path="https://cloud.radioaktywne.pl/api"

#loglevel
loglevel = logging.INFO

#### CONFIG END ####
```

## Obsługa

Obsługa została opisana w instrukcji Emitera 
