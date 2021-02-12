# Akzeptanzkriterien

Dieser Abschnitt erläutert was die verschiedenen Merkmale untersuchen und wie dies überprüft werden kann.

Automatisierte Akzeptanztests sind in `tests/e2e/e2e_test.py` zu finden.
Dieser Test baut alle Docker Container, schickt eine Test-Webseite zur Überprüfung und evaluiert alle
Merkmale auf erwartetes Verhalten.
Das erwartete Verhalten ist dort einmal exemplarisch definiert und kann von dort übernommen werden.

Die Unit- und Integrationstests vertiefen dies weiter.

## Merkmale

Merkmale geben drei wichtige Werte zurück:

- `decision`: 
    - Die getroffene Entscheidung.
    - `wahr` oder `falsch`. `wahr` zeigt an, dass das Merkmal erfüllt ist.
    - `decision` ist explizit nur in Kombination mit `probability` wertvoll.
- `probability`: 
    - Die Wahrscheinlichkeit, dass die Entscheidung zutrifft.
    - Ein Wert von 0 bedeutet, die Entscheidung hat keinen Wert. Egal ob `wahr` oder `falsch`, wir wissen nichts.
    - Dies geschieht bspw., wenn das Merkmal exakt auf der Schwelle zwischen `wahr` und `falsch`. 
      An diesem Punkt wären beide Entscheidungen möglich und würde sich die Webseite nur minimal ändern, wäre die Entscheidung anders. 
      Daher ist hier nichts sicher auszusagen.
- `values`: 
    - Die rohen Werte, welche das Merkmal gefunden hat
    - Basierend auf diesen Werten werden die Entscheidung und deren Wahrscheinlichkeit bestimmt

### Barrierefreiheit alias Accessibility

Dieses Merkmal gibt an, ob die Webseite barrierefrei nach Google Lighthouse ist.
Dafür wird eine Punktezahl für mobile Endgeräte und Desktop-PCs berechnet.
Deren Mittelwert wird benutzt, um eine Aussage über die Barrierefreiheit zu treffen.
Ist der Mittelwert hoch genug, gilt Barrierefreiheit als `wahr`.

Barrierefreiheit wird hierbei durch Google definiert, bspw., ob zwingend eine Maus benutzt werden muss, um die Webseite zu navigieren.

### Cookies

Dieses Merkmal liest die Cookies ein, die von der Webseite benutzt werden.
Wird eines dieser Cookies als unsicher dargestellt, so wird dieses Merkmal als `wahr` definiert.
Idealerweise sollte eine Webseite so wenig Cookies wie möglich laden, bevor der Verwendung von Cookies (s. DSGVO) zugestimmt wird.
Da diese Zustimmung nicht erfolgt, sollten keine oder wenige Cookies geladen werden.

TODO:

- Die gefundenen Cookies werden für weitere Evaluation zurückgegeben, sodass entschieden werden kann, ob Cookies auf eine Whitelist kommen. 
- Cookies könnten unsicher sein, obwohl die überprüften Merkmale es als sicher anzeigen. Eine Blacklist wäre nötig.

### Dateiextrahierbarkeit alias ExtractFromFiles

Dieses Merkmal untersucht die herunterladbaren Dateien einer Webseite darauf, ob diese als Volltext gelesen werden können.
Unterstützte Dateiformate sind derzeit `.docx` und `.pdf`.
Wenn mehr als die Hälfte aller Dateien extrahiert werden können, so gilt dieses Merkmal als `wahr`.

TODO:

- Welche weiteren Datentypen sind auf den Webseiten vorhanden?
- Diese Datentypen müssen entsprechend eingebunden und automatisch eingelesen werden
- Das Einlesen von PDFs basiert derzeit auf pdfminer.six, ein Package welches durch ein besseres ersetzt werden könnte.
- Zum Einlesen von DOCX Dateien, welche xml enthalten, wird das Package `lxml` benutzt. 
  Dieses Package benötigt viel Zeit während des Baus des Docker Containers. 
  Eine Alternative könnte diesen Prozess und damit CI/CD optimieren.

### DSGVO alias GDPR

Dieses Merkmal untersucht die Übereinstimmung der Webseite mit den Anforderungen der DSGVO. 
Da dieses Merkmal eine juristische Behandlung nicht erfüllen kann, wird dieses Merkmal stets `falsch` anzeigen, wie abgesprochen.

Nichtsdestotrotz werden verschiedene Eigenschaften der Webseite untersucht und hinterlegt, um dieses Merkmal weiter zu verbessern.

Die Eigenschaften umfassen:

- Verlinkt die Seite nur auf sichere HTTPS Webseiten?
- Ist HSTS eingeschalten? Falls ja: Sind sicherheitsrelevante Eigenschaften von HSTS optimal gesetzt?
- Ist die `referrer-policy` optimal eingestellt?
- Werden keine externen Fonts geladen und falls doch, welche?
- Werden keine kompromittierende Eingaben gefordert und falls doch, welche?
- Befindet sich ein Link auf `impressum` auf der Webseite. Dies sagt nichts darüber aus, ob das Impressum korrekt ist.

TODO:

- Welche Fonts sind „akzeptabel“, welche nicht?
- Das Merkmal könnte invertiert werden im Sinne von, ob DSGVO sicher nicht (!) erfüllt ist. 
  D.h. `wahr` zeigt an, dass DSGVO nicht erfüllt ist. 
  Ein `falsch` zeigt an, dass unklar ist, ob DSGVO erfüllt wird oder nicht.

### Javascript

Dieses Merkmal untersucht, ob und welche Javascripts werden ausgeführt. 
Da Javascript potenziell gefährliche Inhalte laden und ausführen kann wird dieses Merkmal `wahr` anzeigen, sobald ein Javascript gefunden wurde.

TODO:
- Weiter klassifizieren, welche Art Javascript akzeptabel sind und welche nicht.
- Sandbox, um Javascript auszuführen und beobachten, welche Zugriffe das Skript vollführt.
- White and blacklist von Javaskripten, welche akzeptabel sind - gibt es Listen, Repos etc. dafür?

### Gefährliche Dateierweiterungen alias MaliciousExtensions

Dieses Merkmal untersucht, ob und welche bekannten gefährlichen Dateiendungen in Dateien der Webseite vorkommen.
Beispiele enthalten, u. a., `.exe`, `.com`, `.js` und `.dll`.
Dieses Merkmal ist noch recht grob und wird `wahr` sobald irgendeine Datei mit solch einer Endung gefunden wird.

### Metabeschreibungsentdecker alias MetatagExplorer

Dieses Merkmal sammelt alle `meta` Merkmale auf der Webseite für zukünftige Auswertung nach Produktivlauf.

TODO:
- Werden `robot` Merkmale gesetzt?
- Welche Merkmale sind auffällig, selten oder ungewöhnlich.


### Sicherheit alias Security

Dieses Merkmal untersucht verschiedene HTML-Header Eigenschaften, um Aussagen über optimal konfigurierte Sicherheitseinstellungen zu liefern.
Sind alle Eigenschaften gesetzt, so gibt dieses Merkmal `wahr` zurück, d. h., es ist strikt.
Es ist zu erwarten, dass nur die wenigsten Webseiten dieses Merkmal erfüllen

### Werbung alias Advertisment

Dieses Merkmal nutzt Adblock-Listen, um Werbung, ungewollte Frames, Bilder und Objekte zu erkennen.
Diese Listen werden für Browser-Plugins zur Werbungsblockierung eingesetzt.
Wird ein Werbeelement entdeckt, so wird dieses Merkmal auf `wahr` gesetzt.

TODO:
- Welche Art von Werbung wird bisher akzeptiert, kann also auf eine whitelist gesetzt werden?
- AdblockParser forken und optimieren. Dieses Plugin ist derzeit der Flaschenhals.
- Dieses Merkmal kann mit anderen Merkmalen zusammengefasst werden, bspw. EasyPrivacy
- Da dies der derzeitige Flaschenhals ist, sollte evaluiert werden, ob dieser Teil in einer low-level Sprache implementiert wird.

### Privatsphäre alias EasyPrivacy

Dieses Merkmal untersucht ob bspw. Tracker u. ä. auf der Webseite eingesetzt werden um die Privatsphäre des Nutzenden zu
kompromittieren.
Es nutzt dafür gepflegte open-source Online-Listen.
Wird ein entsprechendes Element entdeckt, so wird dieses Merkmal auf `wahr` gesetzt.

### Cookies in Html alias CookiesInHtml

Dieses Merkmal untersucht direkt den HTML-Quellcode auf bekannte Cookiesignaturen.
Es erkennt auch DSGVO Fenster und privatsphärenbezogene Benachrichtigungen.
Es nutzt dafür gepflegte open-source Online-Listen.
Wird ein solches Cookie entdeckt, so wird dieses Merkmal auf `wahr` gesetzt.

### FanboyAnnoyance

Dieses Merkmal versucht „nervige“ Elemente zu entdecken, bspw. Pop-Ups.
Es nutzt dafür gepflegte open-source Online-Listen.
Es reduziert signifikant die Ladezeiten.

TODO:
- Weitere Listen sind verfügbar und können zusammengefasst werden, bspw. mit FanboySocialMedia

### Benachrichtigungen alias FanboyNotification

Dieses Merkmal untersucht, ob die Webseite Elemente beinhaltet, die versuchen Benachrichtigungen auf dem Endgerät zu erzeugen.
Es nutzt dafür gepflegte open-source Online-Listen.

### Soziale Netzwerke alias FanboySocialMedia

Dieses Merkmal untersucht, ob die Webseite Elemente beinhaltet, die auf soziale Netzwerke verlinken.
Dazu gehören bspw. der Facebook Like Button und Twitter Einblendungen.
Es nutzt dafür gepflegte open-source Online-Listen.

### Anti-Werbeblocker alias AntiAdBlock

Dieses Merkmal untersucht, ob die Webseite Elemente beinhaltet, die Werbeblocker erkennen und entsprechend den Nutzenden
auffordern diese Werbeblocker zu deaktivieren.
Es nutzt dafür gepflegte open-source Online-Listen.

### spezifisch deutsche Merkmale alias EasylistGermany

Dieses Merkmal untersucht, ob die Webseite Elemente beinhaltet, die spezifisch für das Deutsche sind und geblockt werden sollten.
Es nutzt dafür gepflegte open-source Online-Listen.

### FSK18 alias EasylistAdult

Dieses Merkmal untersucht, ob die Webseite Inhalte oder Links auf spezifisch FSK18 erforderliche Webseiten enthält.
Es nutzt dafür gepflegte open-source Online-Listen.

TODO:
- Die Auswertung bezieht sich allein

### Bezahlbarrieren alias Paywalls

Dieses Merkmal untersucht, ob die Webseite Barrieren beinhaltet, sodass Inhalte nur gegen Bezahlung konsumiert werden können.
Wird eine solche Barriere entdeckt, so wird dieses Merkmal auf `wahr` gesetzt.

TODO:
- Weitere Beispielwebseiten mit diesem Merkmal sollten erfasst und untersucht werden.

### Webseite einbettbar alias IFrameEmbeddable

Dieses Merkmal untersucht, ob die Webseite in einen IFrame auf einer externen Webseite einbettbar ist.
Wird die entsprechende Einstellung entdeckt, so gibt dieses Merkmal `wahr` zurück.

### PopUp

Dieses Merkmal untersucht, ob die Webseite Popups beinhaltet.

TODO:
- Weitere Beispielwebseiten mit diesem Merkmal sollten erfasst und untersucht werden.

### Registrierbarriere alias RegWall

Dieses Merkmal untersucht, ob die Webseite Barrieren beinhaltet, sodass Inhalte nur nach erfolgter Registrierung konsumiert werden können.
Wird eine solche Barriere entdeckt, so wird dieses Merkmal auf `wahr` gesetzt.

TODO:
- Weitere Beispielwebseiten mit diesem Merkmal sollten erfasst und untersucht werden.

### LogInOut

Dieses Merkmal untersucht, ob die Webseite Login/Logout Eingaben beinhaltet und damit potenziell den Nutzer auffordert sich einzuloggen.
Wird eine solche Eingabe entdeckt, so wird dieses Merkmal auf `wahr` gesetzt.
Es werden ausschließlich HTML Eingabeobjekte untersucht.

TODO:
- Weitere Beispielwebseiten mit diesem Merkmal sollten erfasst und untersucht werden.


### Weitere Merkmale

TODO:
- Verlustfreie und verlustbehaftete Bilder: wird ein verlustfreies Bild gefunden, welches einem verlustbehafteten entspricht, sodass ersteres bevorzugt werden kann? 
- PG18/FSK18
- FAIR data
- Wie werden Webseiten auf Google indiziert? SEO-Thema
- Copyright
- SVGs
- RDFa
- GDPR/DSGVO

## Allgemeine TODOs

Derzeit sind Merkmale unabhängig konstruiert, d.h., viele Merkmal überprüfen selbstständig anhand einer Liste ob deren Inhalte in der Webseite vorgefunden werden können.
Dies erzeugt Doppelungen, bspw., im Programmcode, der sich um die Verwaltung der Listen und deren Vorbereitung kümmert.
Würden bestimmte Merkmale zusammengefasst, könnte sich dadurch ein Performanceboost ergeben.
Weiterhin könnte es spannend sein Merkmale zusammenzufassen und hernach anhand der gefundenen Listeneinträge festzustellen,
ob bspw., Popups vorhanden sind o.ä.
Inwiefern ein solcher Wandel in der Architektur lohnenswert ist hängt auch vom jeweiligen Flaschenhals ab. 
Derzeit ist die Überprüfung auf Werbung und Privatsphäre der Flaschenhals, da speziell das Plugin adblockparser.
Entweder wird dieses Plugin geforkt und optimiert oder ersetzt.

Wie besprochen benötigen viele der Merkmale Daten aus der Produktion um weiter verfeinert zu werden.
Idealerweise werden die `values` der Merkmale, die neben `decision` und `probability` zurückgegeben, 
hinterlegt und nachträglich ausgewertet.