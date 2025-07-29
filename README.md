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

* Przed instalacją należy zainstalować pakiet **Liquidsoap w wersji co najmniej 2.2.5** (https://www.liquidsoap.info/doc-2.2.5/). W przypadku Ubuntu może być konieczne dodanie dodatkowego repozytorium lub kompilacja ze źródeł:
```
curl -fsSL https://deb.liquidsoap.info/liquidsoap.gpg | sudo apt-key add -
echo "deb https://deb.liquidsoap.info/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/liquidsoap.list
sudo apt-get update
sudo apt-get install liquidsoap
```
W pozostałych przypadkach instalację opisano w https://www.liquidsoap.info/doc-2.2.5/install.html 

* Należy zainstalować pakiet PyQt5 (na systemach Ubuntu powinien być preinstalowany)

* Pozostałe pakiety instalujemy poprzez skrypty `INSTALL.sh` i `DEVINSTALL.sh` - ten drugi doinstalowuje narzędzia deweloperskie (m.in. Qt Designera)

#### Alternatywna instalacja z Nix

Jeśli używasz Nix/NixOS, możesz skorzystać z flake.nix:

```
nix develop
```

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

## Zmiany w wersji dla Liquidsoap 2.2.5

Ta wersja została zaktualizowana do kompatybilności z Liquidsoap 2.2.5. Główne zmiany:

* Zaktualizowano składnię ustawień (`set()` → `settings.*`)
* Poprawiono zarządzanie wyjściem Icecast z możliwością start/stop
* Zaktualizowano komendy serwera do nowej składni
* Poprawiono wstawianie metadanych RDS

## Obsługa

Obsługa została opisana w instrukcji Emitera
