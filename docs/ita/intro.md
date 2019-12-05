# FiloBlu Service

## Neural Network as Service

Uno degli obiettivi finali del Machine Learning è sicuramente l'automazione dei processi.
Sviluppiamo quotidianamente modelli complessi per eseguire attività che dovrebbero essere eseguite automaticamente da un computer senza supervisione umana.
Le reti neurali sono strumenti matematici classicamente usati per questi scopi.
Oltre alle strutture e agli scopi delle reti neurali, un argomento importante da discutere è l'automazione di questo tipo di algoritmi in un dispositivo informatico.
In questo progetto discuteremo un'implementazione di questi algoritmi come servizio all'interno di un computer-server.
In particolare parleremo dell'implementazione del servizio *FiloBlu* che fa parte di un progetto sviluppato in collaborazione con l'Università La Sapienza (Roma) e il Data Center INFN CNAF di Bologna.
Questo progetto è ancora in corso e il suo scopo va oltre gli obiettivi di questo pacchetto, quindi ci concentreremo solo sull'implementazione del servizio senza alcun riferimento all'algoritmo di Machine Learning utilizzato.
Questa è un'ulteriore prova che le tecniche sviluppate sono totalmente indipendenti dallo scopo dell'applicazione finale.

Un servizio è un software che viene eseguito in background in una macchina.
Nelle macchine Unix viene spesso chiamato `daemon`, mentre nelle macchine Windows è detto *Windows Service*.
Un servizio può essere lanciato solamente con privilegi da amministratore e continua la sua esecuzione senza alcuna interazione dell'utente.
Un altro requisito importante è la possibilità di riavviare tale programma nel momento in cui si verifichino problemi nella funzionalità della macchina e/o all'avvio stesso della macchina.

Un servizio di Machine Learning potrebbe essere utilizzato per applicazioni in cui dobbiamo gestire un flusso asincrono di dati per lunghi intervalli di tempo.
Un esempio potrebbe essere il caso in cui il fornitore di dati sia identificato da un'APP o una videocamera.
Questi dati devono essere archiviati all'interno di un database centrale che può trovarsi in un dispositivo diverso o nello stesso computer in cui è in esecuzione il servizio.
Poiché il servizio viene eseguito in background, l'unico canale di comunicazione con l'utente è dato dai file di log.
Un logfile è un semplice file "leggibile" in cui vengono salvate le informazioni di base sullo stato corrente del servizio.
Pertanto, è fondamentale impostare appropriati punti di controllo nello script del servizio e scegliere la quantità minima di informazioni che il servizio dovrebbe scrivere per rendere comprensibile all'utente il suo stato.

[**next >>**](./service.md)
