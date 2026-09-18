Prova su casi samplici (il tempo di vitamin sale troppo velocemente per casi più complessi)
Mixed è considerato come vitamin fosse eseguito dopo ga quando ga fallisce.
Nel primo test Vitamin ha trovato qualche strategia che GA ha mancato, ma GA ne ha trovate comunque di più,
anche se Vitamin non è andato in timeout, cosa che non mi era successa durante test precedenti,
devo capire se Vitamin manca ancora delle strategie

Sistemato il problema nel secondo test, aggiungendo self loop su ogni stato in cui il pruning
toglie tutte le transizioini uscenti, sia su GA, sia su Vitamin, in quanto non sono riuscito
a far funzionare correttamente questi casi su Vitamin.

Dovrei fare un altro test con più popolazione(30) o più generazioni(60), per vedere meglio il miss rate,
questo test era più per valutare l'approccio misto.

Nel secondo test ho fatto una versione dei grafici dove ho rimosso l'ultima riga del csv, in quanto vitamin è andato in timeout (120 sec)
divrese volte.
