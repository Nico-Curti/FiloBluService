## Data Transmission

Nella configurazione precedente ci siamo concentrati sulla pipeline che elabora il flusso di dati ignorando qualsiasi problema relativo alla comunicazione tra il dispositivo esterno e la macchina che ospita il servizio.
Il progetto *FiloBlu* utilizza un'APP esterna per inviare dati al server principale, quindi abbiamo due sistemi che devono comunicare automaticamente tra loro tramite connessione Internet.
In generale, potremmo dover gestire dati sensibili che potrebbero essere vulnerabili utilizzando una comunicazione Internet.
Per affrontare questo problema abbiamo sviluppato un semplice pacchetto client-server TCP/IP che supporti anche una crittografia RSA, il pacchetto `CryptoSocket` [[CryptoSocket](https://github.com/Nico-Curti/CryptoSocket)].

La sicurezza della comunicazione potrebbe essere un punto importante in molte applicazioni di ricerca ed è essenziale una valida procedura di crittografia.
La crittografia RSA è considerata uno dei metodi di crittografia più sicuri per la trasmissione dei dati ed è abbastanza facile da implementare.
Nel pacchetto `CryptoSocket` abbiamo implementato un semplice wrap della libreria `Python` `socket` per eseguire una serializzazione dei nostri dati che sono (opzionalmente) elaborati dalla nostra implementazione dell'[algoritmo RSA](https://en.wikipedia.org/wiki/RSA_(cryptosystem)).
In questo modo diversi tipi di dati possono essere inviati dal client contemporaneamente.
Lo script di [client](https://github.com/Nico-Curti/CryptoSocket/blob/master/CryptoSocket/examples/client.py) può essere adattato con piccole modifiche a qualsiasi necessità dell'utilizzatore, il quale è in grado di serializzare anche strutture `Python` complesse e trasmettere tali pacchetti dati tra due macchine (al [server](https://github.com/Nico-Curti/CryptoSocket/blob/master/CryptoSocket/examples/server.py)).
Il modulo di crittografia è stato scritto in puro `C++` per efficienza computazionale ed un wrap in `Cython` è stato fornito per applicazioni pure-`Python`.
`CryptoSocket` ha solo uno scopo dimostrativo e quindi funziona solo per una trasmissione di dati 1-to-1 (1 server e 1 client) per il momento.

Poiché questa seconda implementazione potrebbe essere utilizzata anche per altre applicazioni, è stata trattata come un progetto separato e ha un proprio codice open source.
Il pacchetto `CryptoSocket` può essere installato mediante [`CMake`](https://github.com/Nico-Curti/CryptoSocket/blob/master/CMakeLists.txt) in ogni piattaforma e/o sistema operativo e una guida completa all'installazione è fornita all'interno della repository del pacchetto.
La continuous integration del progetto è garantita testando l'installazione del pacchetto su diverse macchine e piattaforme via [Travis CI](https://github.com/Nico-Curti/CryptoSocket/blob/master/.travis.yml) e [Appveyor CI](https://github.com/Nico-Curti/CryptoSocket/blob/master/appveyor.yml).

