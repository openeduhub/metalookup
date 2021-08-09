# Akzeptanzkriterien

Dieser Abschnitt erläutert was die verschiedenen Merkmale untersuchen und wie dies überprüft werden kann.

Automatisierte Akzeptanztests sind in `tests/e2e/e2e_test.py` zu finden.
Dieser Test baut alle Docker Container, schickt eine Test-Webseite zur Überprüfung und evaluiert alle
Merkmale auf erwartetes Verhalten.
Das erwartete Verhalten ist dort einmal exemplarisch definiert und kann von dort übernommen werden.

Die Unit- und Integrationstests vertiefen dies weiter.

## Merkmale

Merkmale geben vier wichtige Werte zurück:

- `isHappyCase`:
    - Die getroffene Entscheidung.
    - `true`, `unknown` oder `false`. `true` zeigt an, ob das Merkmal zum Knockout oder zum HappyCase führt.
    - Als HappyCase gilt im allgemeinen die Merkmalsfreiheit, also das bspw. eine Webseite frei von Werbung ist.
    - Knockout bedeutet hingegen ein negatives Ergebnis zum Happy Case, also bspw. das DGSVO nicht erfüllt ist oder Werbung vorhanden ist.
    - `isHappyCase` ist explizit nur in Kombination mit `probability` wertvoll.
- `probability`:
    - Die Wahrscheinlichkeit, dass die Entscheidung zutrifft.
    - Ein Wert von 0 bedeutet, die Entscheidung hat keinen Wert. Egal ob `true` oder `false`, wir wissen nichts. Standardmäßig wird hier `unknown` zurück gegeben.
    - Dies geschieht bspw., wenn das Merkmal exakt auf der Schwelle zwischen `true` und `false`.
      An diesem Punkt wären beide Entscheidungen möglich und würde sich die Webseite nur minimal ändern, wäre die Entscheidung anders.
      Daher ist hier nichts sicher auszusagen.
- `values`:
    - Die rohen Werte, welche das Merkmal gefunden hat
    - Basierend auf diesen Werten werden die Entscheidung und deren Wahrscheinlichkeit bestimmt
- `explanation`:
  - eine knappe, prägnante Erläuterung warum der entsprechende Wert für `isHappyCase` gewählt wurde.
  - Der Eintrag `Cached` deutet hier an, dass die Daten aus dem Cache reproduziert worden.
    - Möglicherweise hat die Webseite sich seit dem Cache-Eintrag verändert. Das Ergebnis sollte ggf. hinterfragt werden.

Im Folgenden werden die verschiedenen Merkmale näher beschrieben und durch Beispiele erläutert.

### Barrierefreiheit alias Accessibility

Dieses Merkmal gibt an, ob die Webseite barrierefrei nach [Google Lighthouse](https://developers.google.com/web/tools/lighthouse/) ist.
Dafür wird eine Punktezahl für mobile Endgeräte und Desktop-PCs berechnet.
Deren Mittelwert wird benutzt, um eine Aussage über die Barrierefreiheit zu treffen.
Ist der Mittelwert hoch genug, gilt Barrierefreiheit als `true`.

Barrierefreiheit wird hierbei durch Google definiert, bspw., ob zwingend eine Maus benutzt werden muss, um die Webseite zu navigieren.

#### Vorteil

Statt händisch und subjektiv einzuschätzen, ob eine Webseite, bspw. von Blinden, eingesetzt werden kann wird hier auf ein
gepflegtes Werkzeug zurückgegriffen, welches reproduzierbare Ergebnisse liefert und damit Webseiten vergleichbar macht.
daren
#### Ablauf

1. Das Merkmal sendet die Webseite-url an einen Lighthouse Container basierend auf:
   `https://github.com/femtopixel/docker-google-lighthouse`.
2. Zurück kommen Fließkommazahlen zwischen `0` und `1`.
3. Der Wert wird für mobile Endgeräte und Desktop-PCs einzeln berechnet und dann gemittelt.
4. Liegt der Mittelwert über dem konfigurierten Schwellwert, e.g., `0.8`, so wird `isHappyCase` `true`.
Die `probability` wird entsprechend zwischen dem Schwellwert und `1` linear skaliert.
Je näher der Mittelwert am Schwellwert liegt, desto geringer ist `probability`.
D. h., liegt der Mittelwert bei `0.85` und der Schwellwert bei `0.8`, so wird `probability` `0.25`.

#### Beispiel

Die url `https://canyoublockit.com/extreme-test/` liefert Werte von `0.98` für mobile Endgeräte und Desktop-PCs.
Damit liegt auch der Mittelwert bei `0.98` und die `probability` bei `0.9` für einen Schwellwert von `0.8`.

### Cookies

Dieses Merkmal liest die Cookies ein, die von der Webseite benutzt werden.
Wird eines dieser Cookies als unsicher dargestellt, so wird dieses Merkmal als `false` definiert.
Idealerweise sollte eine Webseite so wenig Cookies wie möglich laden, bevor der Verwendung von Cookies (s. DSGVO) zugestimmt wird.
Da diese Zustimmung nicht erfolgt, sollten keine oder wenige Cookies geladen werden.

#### Vorteil

Durch das Aufnehmen aller Cookies kann ein Katalog erstellt werden, anhand dessen entschieden wird, ob ein bestimmtes
Cookie akzeptabel ist oder nicht. Dies kann geschlossen für alle Webseiten erstellt werden, sodass subjektive Einflüsse
entfallen.

#### Ablauf

1. Das Merkmal entnimmt alle Cookies, welche von der Webseite benutzt werden.
2. Jedes Cookie wird auf dessen Eigenschaften `httpOnly` sowie `secure` überprüft.
3. Ist eine der beiden Eigenschaften `falsch`, so wird dieses Cookie als „unsicher“ eingestuft.
4. Gibt es mindestens ein unsicheres Cookie auf der Webseite, so wird die `probability` auf `1` und
`isHappyCase` auf `false` gesetzt.

#### Beispiel

Cookie 1:
```json
{
"name": "test_cookie",
"httpOnly": false,
"secure": true
}
```
→ dieses Cookie wird als „unsicher“ eingestuft.

Cookie 2:
```json
{
"name": "test_cookie",
"httpOnly": true,
"secure": true
}
```
→ dieses Cookie wird als „sicher“ eingestuft und daher nicht weiter beachtet.

#### TODO

- Die gefundenen Cookies werden für weitere Evaluation zurückgegeben, sodass entschieden werden kann, ob Cookies auf eine Whitelist kommen.
- Cookies könnten unsicher sein, obwohl die überprüften Merkmale es als sicher anzeigen. Eine Blacklist wäre nötig.

### Dateiextrahierbarkeit alias ExtractFromFiles

Dieses Merkmal untersucht die herunterladbaren Dateien einer Webseite darauf, ob diese als Volltext gelesen werden können.
Unterstützte Dateiformate sind derzeit `.docx` und `.pdf`.
Wenn mehr als die Hälfte aller Dateien extrahiert werden können, so gilt dieses Merkmal als `true`.

#### Vorteil

Statt alle Dateien händisch zu öffnen und auf Extrahierbarkeit zu untersuchen, wird direkt ein Katalog erstellt, welche
Dateien sich für eine weitere Bearbeitung durch Lehrpersonal eignen. Des Weiteren entsteht ein Überblick, wo solche Dateien
angeboten werden.

#### Ablauf

1. Das Merkmal entnimmt alle Links, welche von der Webseite benutzt werden.
2. Jeder Link wird untersucht, ob er auf eine Datei mit einem unterstützten Dateiformat verweist.
3. Wird ein solcher Link gefunden, so wird die Datei heruntergeladen und temporär gespeichert.
4. Lässt sich aus einer solchen Datei ohne Fehler ein Text extrahieren, so wird die Datei als lesbar eingestuft und zu
   `values` hinzugefügt.
5. Die `probability` ergibt sich als Anteil solcher extrahierbarer Dateien im Vergleich zu allen vorhandenen Dateien.
4. Ist die `probability` über dem Schwellwert, so wird `isHappyCase` auf `true` gesetzt.

#### Beispiel

1. Die url `https://digitallearninglab.de/unterrichtsbausteine/anlauttraining` enthält Pdf und Docx Dateien.
2. Alle Dateien sind extrahierbar, sodass das Merkmal hier die `isHappyCase` `true` zurückgegeben wird.
3. Da dies programmatisch passiert, kann lediglich durch den Nutzer überprüft werden, dass die Dateien nicht
   passwortgeschützt sind und der Text in den PDFs selektiert und kopiert werden kann.

#### TODO

- Welche weiteren Datentypen sind auf den Webseiten vorhanden?
- Diese Datentypen müssen entsprechend eingebunden und automatisch eingelesen werden
- Das Einlesen von PDFs basiert derzeit auf pdfminer.six, ein Package welches durch ein besseres ersetzt werden könnte.
- Zum Einlesen von DOCX Dateien, welche xml enthalten, wird das Package `lxml` benutzt.
  Dieses Package benötigt viel Zeit während des Baus des Docker Containers.
  Eine Alternative könnte diesen Prozess und damit CI/CD optimieren.

### DSGVO alias GDPR

Dieses Merkmal untersucht die Übereinstimmung der Webseite mit den Anforderungen der DSGVO.
Da dieses Merkmal eine juristische Behandlung nicht erfüllen kann, wird dieses Merkmal stets `false` anzeigen, wie abgesprochen.

Nichtsdestotrotz werden verschiedene Eigenschaften der Webseite untersucht und hinterlegt, um dieses Merkmal weiter zu verbessern.

Die Eigenschaften umfassen:

- Verlinkt die Seite nur auf sichere HTTPS Webseiten?
- Ist HSTS eingeschalten? Falls ja: Sind sicherheitsrelevante Eigenschaften von HSTS optimal gesetzt?
- Ist die `referrer-policy` optimal eingestellt?
- Werden keine externen Fonts geladen und falls doch, welche?
- Werden keine kompromittierende Eingaben gefordert und falls doch, welche?
- Befindet sich ein Link auf `impressum` auf der Webseite. Dies sagt nichts darüber aus, ob das Impressum korrekt ist.

#### Vorteil

Ob eine Webseite DSGVO konform ist, ist eine komplexe Aussage.
Dieses Merkmal automatisiert einige relevante Überprüfungen,
sodass ungenügende Webseiten vorselektiert werden und zur detaillierteren Untersuchung durch Fachpersonal übergeben
werden können.

#### Ablauf

1. Das Merkmal untersucht alle Links der Webseite, ob diese `impressum` enthalten und damit auf ein bestehendes Impressum hinweisen.
2. Es wird untersucht, ob alle Links auf `https` verweisen und damit sicher sind.
3. Es wird untersucht, ob der `strict-transport-security` Header der Webseite `includesubdomains`, `preload` sowie `max-age` enthält
und ob letzteres eine Zeitdauer über 100 Tagen enthält.
4. Es wird untersucht, ob der `referrer-policy` Header definiert ist.
5. Es wird untersucht, ob externe Fonts hinzugeladen werden, da diese auch als Sicherheitslücke ausgenutzt werden können.
Wird ein Font gefunden, gilt dies als negativ.
6. Es wird untersucht, ob auf der Webseite Eingabefelder für Passwörter, E-Mail-Adressen und mehr da ist.
Wird ein Eingabefeld gefunden, gilt dies als negativ.
7. Da das Merkmal derzeit unzureichend auf DSGVO-Konformität untersucht wird `isHappyCase` immer `false` oder `unknown` sein.
8. Die `probability` wird verringert, wenn ein negativer Fall eintritt, bspw., `impressum` nicht gefunden wird.

#### TODO

- Welche Fonts sind „akzeptabel“, welche nicht?

### Javascript

Dieses Merkmal untersucht, ob und welche Javaskripte werden ausgeführt.
Da Javascript potenziell gefährliche Inhalte laden und ausführen kann wird dieses Merkmal `false` anzeigen, sobald ein Javascript gefunden wurde.

#### Vorteil

Das Merkmal scannt Webseiten automatisch auf – versteckte – Javascript, sodass Nutzer*Innen nicht erst aufwändig den HTML
Code lesen müssen.

#### Ablauf

1. Das Merkmal untersucht alle `script`-Tags der Webseite, also alle HTML Elemente, die auf Skripte hinweisen.
2. Wird ein Skript gefunden, so gilt dies als negativ, auch wenn dadurch nicht sicher ist, ob das Skript negativ oder positiv ist.

#### Beispiel

- In einer hypothetischen Webseite wurde das folgende HTML-Schnipsel gefunden:

```html
<script src='/xlayer/layer.php?uid='></script>
```

- Auch wenn dies kein wirkliches Skript enthält, so deutet der Schlüssel `src` auf ein Skript hin.
- Dieses wird entsprechend extrahiert und erkannt.
- Hier wird `decision` `false`.

#### TODO

- Weiter klassifizieren, welche Art Javascript akzeptabel sind und welche nicht.
- Sandbox, um Javascript auszuführen und beobachten, welche Zugriffe das Skript vollführt.
- White- and Blacklist von Javaskripten, welche akzeptabel sind – gibt es Listen, Repos etc. dafür?

### Gefährliche Dateierweiterungen alias MaliciousExtensions

Dieses Merkmal untersucht, ob und welche bekannten gefährlichen Dateiendungen in Dateien der Webseite vorkommen.
Beispiele enthalten, u. a., `.exe`, `.com` und `.dll`.
Dieses Merkmal ist noch recht grob und wird `false` sobald irgendeine Datei mit solch einer Endung gefunden wird.

#### Vorteil

Das Merkmal scannt Webseiten automatisch auf potenziell gefährlichen Dateiendungen, sodass diese Seiten explizit
auf ihre Eignung für den Schulunterricht untersucht werden können.

#### Quellen

Die Dateiendungen wurden extrahiert aus:

```
https://www.file-extensions.org/filetype/extension/name/dangerous-malicious-files
https://www.howtogeek.com/137270/50-file-extensions-that-are-potentially-dangerous-on-windows/
https://sensorstechforum.com/file-types-used-malware-2019/
https://www.howtogeek.com/127154/how-hackers-can-disguise-malicious-programs-with-fake-file-extensions/
```

#### Ablauf

1. Das Merkmal untersucht alle Links der Webseite auf Dateien mit Dateiendungen.
2. Die Dateiendung wird mit den einprogrammierten Endungen verglichen.
3. Wird eine potenziell gefährliche Dateiendung erkannt, so wird direkt `isHappyCase` auf `false` gesetzt.

#### Beispiel

1. Die url `https://digitallearninglab.de/unterrichtsbausteine/anlauttraining` enthält Pdf und Docx Dateien.
2. Da diese potenziell gefährlich sein könnten, wird für diese Webseite `isHappyCase` auf `false` gesetzt.

### Metabeschreibungsentdecker alias MetatagExplorer

Dieses Merkmal sammelt alle `meta` HTML Elemente der Webseite für zukünftige Auswertung nach Produktivlauf.
Da es derzeit rein explorativ ist, wird dieses Merkmal stets `unknown` als `isHappyCase` zurückgeben.

#### Ablauf

1. Das Merkmal untersucht alle `meta` HTML Elemente und speichert `name` sowie `value` in `values` ab.
2. Es wird keine weitere Entscheidung getroffen

#### TODO

- Werden `robot` Merkmale gesetzt?
- Welche Merkmale sind auffällig, selten oder ungewöhnlich? Wie können diese weiter verarbeitet werden?


### Sicherheit alias Security

Dieses Merkmal untersucht verschiedene HTML-Header Eigenschaften, um Aussagen über optimal konfigurierte Sicherheitseinstellungen zu liefern.
Sind alle Eigenschaften gesetzt, so gibt dieses Merkmal `true` zurück, d. h., es ist strikt.
Es ist zu erwarten, dass nur die wenigsten Webseiten dieses Merkmal erfüllen.

#### Vorteil

Ähnlich zu DSGVO ist Sicherheit ein komplexes Thema, welches durch dieses Merkmal teilautomatisiert wird, sodass
auffällig unsichere Webseiten früh aussortiert werden können.

#### Ablauf

1. Das Merkmal untersucht, ob die folgenden Header gesetzt sind:

    `content-security-policy`
    `referrer-policy`

2. Wird eines der Merkmale nicht gefunden, so ist das negativ.
3. Es überprüft, ob `cache-control` so gesetzt wurde, dass Daten nicht gecached werden
4. Es überprüft, ob `x-content-type-options` auf `nosniff` gesetzt wurde.
5. Es überprüft, ob `x-frame-options` auf `deny` oder `same_origin` gesetzt wurde.
Damit kann die Webseite nicht als iFrame eingebettet werden.
6. Es überprüft, ob `x-xss-protection` auf `1` und `mode=block` gesetzt wurde und damit cross-site-scripting deaktiviert.
7. Es überprüft, ob `strict-transport-security` auf `max-age=` und `includeSubDomains` gesetzt wurde.

#### TODO

- Weitere Informationen aus Header und HTML könnten Hinweise geben, ob die Webseite kompromittiert ist.
- Eine Verbindung mit den Merkmalen schädliche Dateiendungen u. ä. könnte ein wertvolleres Gesamtbild ergeben.

### Werbung alias Advertisement

Dieses Merkmal nutzt Adblock-Listen, um Werbung, ungewollte Frames, Bilder und Objekte zu erkennen.
Diese Listen werden für Browser-Plugins zur Werbungsblockierung eingesetzt.
Wird ein Werbeelement entdeckt, so wird dieses Merkmal auf `false` gesetzt.

#### Vorteil

Da Werbung teilweise versteckt ist, ermöglicht dieses Merkmal anhand eines großen Fundus an Informationen automatisiert
Werbung zu erkennen. Es eliminiert aufwändiges Suchen durch Menschen und subjektive Entscheidungen.

#### Quellen

Die Listen werden als open-source Repository von der Community gepflegt.
Ein Überblick kann hier gefunden werden: `https://easylist.to/`.
Weitere Listen werden hier bezogen: `https://github.com/easylist/easylist/tree/master/easylist`.
Diese Listen werden für AdBlock-artige Plugins im Browser benutzt, um entsprechend Werbung zu blockieren.
Die Syntax ermöglicht Elemente explizit zu blockieren oder zu erlauben, ganze Domänen zu sperren oder nur gewisse
Bausteine einer Webseite zu erlauben.
Die Semantik der Filterregeln kann hier nachvollzogen werden: `https://adblockplus.org/filter-cheatsheet`.

#### Ablauf

1. Das Merkmal lädt die aktuellsten Listen aus dem Repository und verarbeitet diese zu Adblock-Filterregeln.
2. Alle Links auf der Webseite werden mit diesen Filterregeln verglichen.
3. Wird eine Übereinstimmung gefunden, so wird der Link zu `values` hinzugefügt.
4. Sobald ein Link gefunden wurde, gilt dieses Merkmal als `false`.
5. Die `probability` gibt den Anteil von Links mit Werbung zu allen Links an.

#### Beispiel

1. Das HTML Schnipsel
    ```
    <script src='/xlayer/layer.php?uid='></script>
    ```
    enthält Werbung, in diesem Falle den Baustein `/xlayer/layer.php?uid=`.
2. Das Merkmal erkennt diesen Baustein und gibt den Link entsprechend zu `values` zurück.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt, da es nur einen Link im HTML Schnipsel gibt.

#### TODO

- Welche Art von Werbung wird bisher akzeptiert, kann also auf eine whitelist gesetzt werden?
- Reicht es abzubrechen, sobald ein Werbeelement entdeckt wurde (Performanceverbesserung möglich)?
- AdblockParser forken und optimieren. Dieses Plugin ist derzeit der Flaschenhals.
- Dieses Merkmal kann mit anderen Merkmalen zusammengefasst werden, bspw. EasyPrivacy
- Da dies der derzeitige Flaschenhals ist, sollte evaluiert werden, ob dieser Teil in einer low-level Sprache implementiert wird.

### Privatsphäre alias EasyPrivacy

Dieses Merkmal untersucht ob bspw. Tracker u. ä. auf der Webseite eingesetzt werden um die Privatsphäre des Nutzenden zu
kompromittieren.
Es nutzt dafür gepflegte open-source Online-Listen.
Wird ein entsprechendes Element entdeckt, so wird dieses Merkmal auf `false` gesetzt.

#### Vorteil

Da Tracker u. ä. unbeobachtet im Hintergrund laufen, ermöglicht dieses Merkmal anhand eines großen Fundus an
Informationen automatisiert solche Elemente zu erkennen.
Es eliminiert aufwändiges Suchen durch Menschen und subjektive Entscheidungen.

#### Quellen

Die Listen werden als open-source Repository von der Community gepflegt.
Ein Überblick kann hier gefunden werden: `https://easylist.to/`.
Weitere Listen werden hier bezogen: `https://github.com/easylist/easylist/tree/master/easyprivacy`.
Diese Listen werden für AdBlock-artige Plugins im Browser benutzt, um entsprechende Elemente zu blockieren, die die
Privatsphäre untergraben.
Die Syntax ermöglicht Elemente explizit zu blockieren oder zu erlauben, ganze Domänen zu sperren oder nur gewisse
Bausteine einer Webseite zu erlauben.
Die Semantik der Filterregeln kann hier nachvollzogen werden: `https://adblockplus.org/filter-cheatsheet`.

#### Ablauf

1. Das Merkmal lädt die aktuellsten Listen aus dem Repository und verarbeitet diese zu Adblock-Filterregeln.
2. Alle Links auf der Webseite werden mit diesen Filterregeln verglichen.
3. Wird eine Übereinstimmung gefunden, so wird der Link zu `values` hinzugefügt.
4. Sobald ein Link gefunden wurde, gilt dieses Merkmal als `false`.
5. Die `probability` gibt den Anteil von Links mit kompromittierenden Inhalten zu allen Links an.

#### Beispiel

1. Das HTML Schnipsel
    ```
    <link rel='dns-prefetch' href='//www.googletagmanager.com' />
    ```
    enthält den Baustein `//www.googletagmanager.com`.
2. Das Merkmal erkennt diesen Baustein und gibt den Link entsprechend zu `values` zurück.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt, da es nur einen Link im HTML Schnipsel gibt.

### FanboyAnnoyance

Dieses Merkmal versucht „nervige“ Elemente zu entdecken, bspw. Pop-Ups.
Es nutzt dafür gepflegte open-source Online-Listen.
Es reduziert signifikant die Ladezeiten.
Der Name `Fanboy` ist der Alias eines Software-Ingenieurs: `https://github.com/ryanbr`.

#### Vorteil

Da die Einschätzung, ob ein Element als `nervig` gilt rein subjektiv ist, ermöglicht dieses Merkmal anhand eines großen
Fundus an Informationen automatisiert solche Elemente zu erkennen.
Es eliminiert aufwändiges Suchen durch Menschen und subjektive Entscheidungen.

#### Quellen

Die Listen werden als open-source Repository von der Community gepflegt.
Ein Überblick kann hier gefunden werden: `https://easylist.to/`.
Weitere Listen werden hier bezogen: `https://github.com/easylist/easylist/tree/master/fanboy-addon`.
Diese Listen werden für AdBlock-artige Plugins im Browser benutzt, um entsprechende `nervige` Elemente zu blockieren.
Die Syntax ermöglicht Elemente explizit zu blockieren oder zu erlauben, ganze Domänen zu sperren oder nur gewisse
Bausteine einer Webseite zu erlauben.
Die Semantik der Filterregeln kann hier nachvollzogen werden: `https://adblockplus.org/filter-cheatsheet`.

#### Ablauf

1. Das Merkmal lädt die aktuellsten Listen aus dem Repository und verarbeitet diese zu Adblock-Filterregeln.
2. Alle Links auf der Webseite werden mit diesen Filterregeln verglichen.
3. Wird eine Übereinstimmung gefunden, so wird der Link zu `values` hinzugefügt.
4. Sobald ein Link gefunden wurde, gilt dieses Merkmal als `false`.
5. Die `probability` gibt den Anteil von Links mit `nervigen` Elementen zu allen Links an.

#### Beispiel

1. Das HTML Schnipsel
    ```
    <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/build/push.js' type='text/css' media='all' />
    ```
    enthält den Link zum Javascript `/build/push.js`.
2. Das Merkmal erkennt diesen Baustein und gibt den Link entsprechend zu `values` zurück.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt, da es nur einen Link im HTML Schnipsel gibt.

#### TODO

- Weitere Listen sind verfügbar und können zusammengefasst werden, bspw. mit FanboySocialMedia

### Benachrichtigungen alias FanboyNotification

Dieses Merkmal untersucht, ob die Webseite Elemente beinhaltet, die versuchen Benachrichtigungen auf dem Endgerät zu erzeugen.
Es nutzt dafür gepflegte open-source Online-Listen.
Der Name `Fanboy` ist der Alias eines Software-Ingenieurs: `https://github.com/ryanbr`.

#### Vorteil

Da Benachrichtigungen häufig erst nach einer gewissen Nutzungsdauer einer Webseite aktiv werden, ermöglicht dieses
Merkmal anhand eines großen Fundus an Informationen automatisiert solche Elemente zu erkennen.
Es eliminiert aufwändiges Suchen durch Menschen und subjektive Entscheidungen.

#### Quellen

Die Listen werden als open-source Repository von der Community gepflegt.
Ein Überblick kann hier gefunden werden: `https://easylist.to/`.
Weitere Listen werden hier bezogen: `https://github.com/easylist/easylist/tree/master/fanboy-addon`.
Diese Listen werden für AdBlock-artige Plugins im Browser benutzt, um entsprechende Benachrichtigungen zu blockieren.
Die Syntax ermöglicht Elemente explizit zu blockieren oder zu erlauben, ganze Domänen zu sperren oder nur gewisse
Bausteine einer Webseite zu erlauben.
Die Semantik der Filterregeln kann hier nachvollzogen werden: `https://adblockplus.org/filter-cheatsheet`.

#### Ablauf

1. Das Merkmal lädt die aktuellsten Listen aus dem Repository und verarbeitet diese zu Adblock-Filterregeln.
2. Alle Links auf der Webseite werden mit diesen Filterregeln verglichen.
3. Wird eine Übereinstimmung gefunden, so wird der Link zu `values` hinzugefügt.
4. Sobald ein Link gefunden wurde, gilt dieses Merkmal als `false`.
5. Die `probability` gibt den Anteil von Links, welche als Benachrichtigungen fungieren, zu allen Links an.

#### Beispiel

1. Das HTML Schnipsel
    ```
    <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/build/push.js' type='text/css' media='all' />
    ```
    enthält den Link zum Javascript `/build/push.js`.
2. Das Merkmal erkennt diesen Baustein und gibt den Link entsprechend zu `values` zurück.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt, da es nur einen Link im HTML Schnipsel gibt.

### Soziale Netzwerke alias FanboySocialMedia

Dieses Merkmal untersucht, ob die Webseite Elemente beinhaltet, die auf soziale Netzwerke verlinken.
Dazu gehören bspw. der Facebook Like Button und Twitter Einblendungen.
Es nutzt dafür gepflegte open-source Online-Listen.
Der Name `Fanboy` ist der Alias eines Software-Ingenieurs: `https://github.com/ryanbr`.

#### Vorteil

Da Elemente sozialer Netzwerke häufig im Fließtext einer Webseite eingebunden und dadurch wenig offensichtlich sind,
ermöglicht dieses Merkmal anhand eines großen Fundus an Informationen automatisiert solche Elemente zu erkennen.
Es eliminiert aufwändiges Suchen durch Menschen und subjektive Entscheidungen.

#### Quellen

Die Listen werden als open-source Repository von der Community gepflegt.
Ein Überblick kann hier gefunden werden: `https://easylist.to/`.
Weitere Listen werden hier bezogen: `https://github.com/easylist/easylist/tree/master/fanboy-addon`.
Diese Listen werden für AdBlock-artige Plugins im Browser benutzt, um entsprechende Elemente sozialer Netzwerke zu blockieren.
Die Syntax ermöglicht Elemente explizit zu blockieren oder zu erlauben, ganze Domänen zu sperren oder nur gewisse
Bausteine einer Webseite zu erlauben.
Die Semantik der Filterregeln kann hier nachvollzogen werden: `https://adblockplus.org/filter-cheatsheet`.

#### Ablauf

1. Das Merkmal lädt die aktuellsten Listen aus dem Repository und verarbeitet diese zu Adblock-Filterregeln.
2. Alle Links auf der Webseite werden mit diesen Filterregeln verglichen.
3. Wird eine Übereinstimmung gefunden, so wird der Link zu `values` hinzugefügt.
4. Sobald ein Link gefunden wurde, gilt dieses Merkmal als `false`.
5. Die `probability` gibt den Anteil von Links, welche als Elemente sozialer Netzwerke fungieren, zu allen Links an.

#### Beispiel

1. Das HTML Schnipsel
    ```
    <script type="4fc846f350e30f875f7efd7a-text/javascript" src=
'https://canyoublockit.com/wp-content/plugins/elementor/assets/lib/share-link/share-link.min.js?ver=3.0.15'
id='share-link-js'></script>
    ```
    enthält den Link zum Javascript `share-link.min.js`.
2. Das Merkmal erkennt diesen Baustein und gibt den Link entsprechend zu `values` zurück.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt, da es nur einen Link im HTML Schnipsel gibt.

#### TODO

- Teilweise doppeln sich Einträge aus den Listen. Eine Zusammenfassung der Listen und entsprechende Konsolidierung könnte
Performanceverbesserungen bringen.

### Anti-Werbeblocker alias AntiAdBlock

Dieses Merkmal untersucht, ob die Webseite Elemente beinhaltet, die Werbeblocker erkennen und entsprechend den Nutzenden
auffordern diese Werbeblocker zu deaktivieren.
Es nutzt dafür gepflegte open-source Online-Listen.

#### Vorteil

Da Werbeblocker weit verbreitet sind, sind auch Werbeblocker-Blocker verbreitet und automatisch erkennbar.
Daher ermöglicht dieses Merkmal anhand eines großen Fundus an Informationen automatisiert solche Elemente zu erkennen.
Es eliminiert aufwändiges Suchen durch Menschen und subjektive Entscheidungen.

#### Quellen

Die Listen werden als open-source Repository von der Community gepflegt.
Ein Überblick kann hier gefunden werden: `https://easylist.to/pages/other-supplementary-filter-lists-and-easylist-variants.html`.
Weitere Listen werden hier bezogen: `https://github.com/easylist/antiadblockfilters/tree/master/antiadblockfilters`.
Diese Listen werden für AdBlock-artige Plugins im Browser benutzt, um Anti-Werbeblocker Elemente zu blockieren.
Die Syntax ermöglicht Elemente explizit zu blockieren oder zu erlauben, ganze Domänen zu sperren oder nur gewisse
Bausteine einer Webseite zu erlauben.
Die Semantik der Filterregeln kann hier nachvollzogen werden: `https://adblockplus.org/filter-cheatsheet`.

#### Ablauf

1. Das Merkmal lädt die aktuellsten Listen aus dem Repository und verarbeitet diese zu Adblock-Filterregeln.
2. Alle Links auf der Webseite werden mit diesen Filterregeln verglichen.
3. Wird eine Übereinstimmung gefunden, so wird der Link zu `values` hinzugefügt.
4. Sobald ein Link gefunden wurde, gilt dieses Merkmal als `false`.
5. Die `probability` gibt den Anteil von Links, welche Anti-Werbeblocker Elemente enthalten, zu allen Links an.

#### Beispiel

1. Das HTML Schnipsel
    ```
    <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/adb_script/' type='text/css' media='all' />
    ```
    enthält den Link `/adb_script/`, also ein Adblock Script.
2. Das Merkmal erkennt diesen Baustein und gibt den Link entsprechend zu `values` zurück.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt, da es nur einen Link im HTML Schnipsel gibt.

### spezifisch deutsche Merkmale alias EasylistGermany

Dieses Merkmal untersucht, ob die Webseite Elemente beinhaltet, die spezifisch für das Deutsche sind und geblockt werden sollten.
Es nutzt dafür gepflegte open-source Online-Listen.

#### Vorteil

Ähnlich zu Werbung und Co. werden hier bekannte, deutsch-spezifische Elemente untersucht.
Dieses Merkmal ermöglicht anhand eines großen Fundus an Informationen automatisiert solche Elemente zu erkennen.
Es eliminiert aufwändiges Suchen durch Menschen und subjektive Entscheidungen.

#### Quellen

Die Listen werden als open-source Repository von der Community gepflegt.
Ein Überblick kann hier gefunden werden: `https://easylist.to/`.
Weitere Listen werden hier bezogen: `https://github.com/easylist/easylistgermany`.
Diese Listen werden für AdBlock-artige Plugins im Browser benutzt, um deutsch-spezifische Elemente zu blockieren.
Die Syntax ermöglicht Elemente explizit zu blockieren oder zu erlauben, ganze Domänen zu sperren oder nur gewisse
Bausteine einer Webseite zu erlauben.
Die Semantik der Filterregeln kann hier nachvollzogen werden: `https://adblockplus.org/filter-cheatsheet`.

#### Ablauf

1. Das Merkmal lädt die aktuellsten Listen aus dem Repository und verarbeitet diese zu Adblock-Filterregeln.
2. Alle Links auf der Webseite werden mit diesen Filterregeln verglichen.
3. Wird eine Übereinstimmung gefunden, so wird der Link zu `values` hinzugefügt.
4. Sobald ein Link gefunden wurde, gilt dieses Merkmal als `false`.
5. Die `probability` gibt den Anteil von Links, welche deutsch-spezifische Elemente enthalten, zu allen Links an.

#### Beispiel

1. Das HTML Schnipsel
    ```
    <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='/werbung/banner_' type='text/css' media='all' />
    ```
    enthält das Werbebanner `/werbung/banner_`.
   Dies kann lediglich durch eine sprach-sensible Filterregel erkannt werden.
2. Das Merkmal erkennt diesen Baustein und gibt den Link entsprechend zu `values` zurück.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt, da es nur einen Link im HTML Schnipsel gibt.

### FSK18 alias EasylistAdult

Dieses Merkmal untersucht, ob die Webseite Inhalte oder Links auf spezifisch FSK18 erforderliche Webseiten enthält.
Es nutzt dafür gepflegte open-source Online-Listen.

#### Vorteil

Da FSK18 Inhalte im Schulunterricht nicht akzeptabel sind, hilft dieses Merkmal bei der Vorauswahl entsprechender Seiten.
Dieses Merkmal ermöglicht anhand eines großen Fundus an Informationen automatisiert solche Elemente zu erkennen.
Es eliminiert aufwändiges Suchen durch Menschen und subjektive Entscheidungen.

#### Quellen

Die Listen werden als open-source Repository von der Community gepflegt.
Ein Überblick kann hier gefunden werden: `https://easylist.to/`.
Weitere Listen werden hier bezogen: `https://github.com/easylist/easylistgermany`.
Diese Listen werden für AdBlock-artige Plugins im Browser benutzt, um FSK18 Elemente zu blockieren.
Die Syntax ermöglicht Elemente explizit zu blockieren oder zu erlauben, ganze Domänen zu sperren oder nur gewisse
Bausteine einer Webseite zu erlauben.
Die Semantik der Filterregeln kann hier nachvollzogen werden: `https://adblockplus.org/filter-cheatsheet`.

#### Ablauf

1. Das Merkmal lädt die aktuellsten Listen aus dem Repository und verarbeitet diese zu Adblock-Filterregeln.
2. Alle Links auf der Webseite werden mit diesen Filterregeln verglichen.
3. Wird eine Übereinstimmung gefunden, so wird der Link zu `values` hinzugefügt.
4. Sobald ein Link gefunden wurde, gilt dieses Merkmal als `false`.
5. Die `probability` gibt den Anteil von Links, welche FSK18 Elemente enthalten, zu allen Links an.

#### Beispiel

1. Das HTML Schnipsel
    ```
    <link href='geobanner.fuckbookhookups.com'/>
    ```
    enthält einen FSK18 Link.
2. Das Merkmal erkennt diesen Baustein und gibt den Link entsprechend zu `values` zurück.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt, da es nur einen Link im HTML Schnipsel gibt.

#### TODO

- Die Auswertung bezieht sich allein auf Links.
  Der Fließtext der Webseite, sowie eingebettete Dateien, Audio- und Videolinks
  und deren Inhalte werden bisher nicht untersucht.

### Bezahlbarrieren alias Paywalls

Dieses Merkmal untersucht, ob die Webseite Barrieren beinhaltet, sodass Inhalte nur gegen Bezahlung konsumiert werden können.
Wird eine solche Barriere entdeckt, so wird dieses Merkmal auf `false` gesetzt.

#### Vorteil

Da Bezahlbarrieren erst nach einer gewissen Seitennutzung aufkommen, verringert dieses Merkmal die benötigte Zeit für die
Webseitenklassifizierung.
Dieses Merkmal ermöglicht anhand eines großen Fundus an Informationen automatisiert solche Elemente zu erkennen.
Es eliminiert aufwändiges Suchen durch Menschen und subjektive Entscheidungen.

#### Quellen

Die Stichwörter wurden manuell ausgewählt anhand einer Vielzahl von Webseiten mit Paywalls, bspw., Online-Zeitungen.

#### Ablauf

1. Alle Links auf der Webseite werden mit den Stichwörtern verglichen.
2. Wird eine Übereinstimmung gefunden, so wird der Link zu `values` hinzugefügt.
3. Sobald ein Link gefunden wurde, gilt dieses Merkmal als `false`.
4. Die `probability` gibt den Anteil von Links, welche Paywall Elemente enthalten, zu allen Links an.

#### Beispiel

1. Das HTML Schnipsel
    ```
    <paywall>
    ```
    enthält ein Paywallelement.
2. Das Merkmal erkennt diesen Baustein und gibt den Link entsprechend zu `values` zurück.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt, da es nur einen Link im HTML Schnipsel gibt.

#### TODO
- Weitere Beispielwebseiten mit diesem Merkmal sollten erfasst und untersucht werden.

### Webseite einbettbar alias IFrameEmbeddable

Dieses Merkmal untersucht, ob die Webseite in einen IFrame auf einer externen Webseite einbettbar ist.
Wird die entsprechende Einstellung entdeckt, so gibt dieses Merkmal `true` zurück.

#### Vorteil

Da das Einbetten von Webseiten klar durch den Header definiert wird, der für Nutzer*Innen nicht direkt ersichtlich
ist, ermöglicht dieses Merkmal eine Entscheidung, die sonst nicht direkt möglich wäre.

#### Quellen

Ob eine Webseite als IFrame einbettbar ist, wird über den Header `x-frame-options` definiert.
Ist dieser auf `same-origin` oder `deny`, so kann nicht eingebettet werden.
Dieses Merkmal steht im Kontrast zum Sicherheitsmerkmal, welches denselben Header untersucht.

#### Ablauf

1. Der Webseitenheader wird auf `x-frame-options` geprüft.
2. Wird `same-origin` oder `deny` gefunden, so ist `isHappyCase` sofort `false`.
3. Die `probability` ist `0`, falls kein Header definiert wurde, sonst `1`.

#### Beispiel

1. Der Webseitenheader
    ```json
    {"x-frame-options": "same_origin"}
    ```
    enthält den korrekten Header.
2. Das Merkmal erkennt diesen Baustein und gibt den Wert `same-origin` zu `values` zurück.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt.

### PopUp

Dieses Merkmal untersucht, ob die Webseite Popups beinhaltet.

#### Vorteil

Da PopUp erst nach einer gewissen Seitennutzung aufkommen, verringert dieses Merkmal die benötigte Zeit für die
Webseitenklassifizierung.
Dieses Merkmal ermöglicht anhand eines großen Fundus an Informationen automatisiert solche Elemente zu erkennen.
Es eliminiert aufwändiges Suchen durch Menschen und subjektive Entscheidungen.

#### Quellen

Die Stichwörter wurden manuell ausgewählt anhand einer Vielzahl von Webseiten mit PopUps, bspw., Online-Zeitungen.

#### Ablauf

1. Alle Links auf der Webseite werden mit den Stichwörtern verglichen.
2. Wird eine Übereinstimmung gefunden, so wird der Link zu `values` hinzugefügt.
3. Sobald ein Link gefunden wurde, gilt dieses Merkmal als `false`.
4. Die `probability` ist `1` sobald Popups gefunden wurden.

#### Beispiel

1. Das HTML Schnipsel
    ```
    <noscript><img width="845" height="477"
src="https://canyoublockit.com/wp-content/uploads/2020/01/Screenshot_1.png" class="attachment-large size-large"
alt="Scum Interstitial Ad Placement" loading="lazy" /></noscript>
    ```
    enthält ein Interstitial, also ein Popup.
2. Das Merkmal erkennt diesen Baustein und gibt den Link entsprechend zu `values` zurück.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt, da es nur einen Link im HTML Schnipsel gibt.

#### TODO

- Weitere Beispielwebseiten mit diesem Merkmal sollten erfasst und untersucht werden.

### Registrierbarriere alias RegWall

Dieses Merkmal untersucht, ob die Webseite Barrieren beinhaltet, sodass Inhalte nur nach erfolgter Registrierung konsumiert werden können.
Wird eine solche Barriere entdeckt, so wird dieses Merkmal auf `false` gesetzt.

#### Vorteil

Da Registrierbarrieren erst nach einer gewissen Seitennutzung aufkommen, verringert dieses Merkmal die benötigte Zeit für die
Webseitenklassifizierung.
Dieses Merkmal ermöglicht anhand eines großen Fundus an Informationen automatisiert solche Elemente zu erkennen.
Es eliminiert aufwändiges Suchen durch Menschen und subjektive Entscheidungen.

#### Quellen

Die Stichwörter wurden manuell ausgewählt anhand einer Vielzahl von Webseiten mit Registrierbarrieren, bspw.,
Online-Zeitungen.

#### Ablauf

1. Alle Links auf der Webseite werden mit den Stichwörtern verglichen.
2. Wird eine Übereinstimmung gefunden, so wird der Link zu `values` hinzugefügt.
3. Sobald ein Link gefunden wurde, gilt dieses Merkmal als `false`.
4. Die `probability` ist `1` sobald Registrierbarrieren gefunden wurden.

#### Beispiel

1. Das HTML Schnipsel
    ```
    <link rel='stylesheet' id='wpzoom-social-icons-block-style-css'  href='regwall' type='text/css' media='all' />
    ```
    enthält `regwall`, also eine Registrierbarriere.
2. Das Merkmal erkennt diesen Baustein und gibt den Link entsprechend zu `values` zurück.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt, da es nur einen Link im HTML Schnipsel gibt.

#### TODO

- Weitere Beispielwebseiten mit diesem Merkmal sollten erfasst und untersucht werden.

### LogInOut

Dieses Merkmal untersucht, ob die Webseite Login/Logout Eingaben beinhaltet und damit potenziell den Nutzer auffordert sich einzuloggen.
Wird eine solche Eingabe entdeckt, so wird dieses Merkmal auf `false` gesetzt.
Es werden ausschließlich HTML Eingabeobjekte untersucht.

#### Vorteil

Da Eingabeobjekte häufig versteckt oder an mehreren Orten der Webseite vorkommen, verringert dieses Merkmal die
benötigte Zeit für die Webseitenklassifizierung.
Dieses Merkmal ermöglicht anhand eines großen Fundus an Informationen automatisiert solche Elemente zu erkennen.
Es eliminiert aufwändiges Suchen durch Menschen und subjektive Entscheidungen.

#### Quellen

Die Stichwörter wurden manuell ausgewählt anhand einer Vielzahl von Webseiten mit Eingabeelementen, bspw.,
Online-Zeitungen.

#### Ablauf

1. Alle Links auf der Webseite werden mit den Stichwörtern verglichen.
2. Wird eine Übereinstimmung gefunden, so wird der Link zu `values` hinzugefügt.
3. Sobald ein Link gefunden wurde, gilt dieses Merkmal als `false`.
4. Die `probability` ist `1` sobald Eingabeelemente gefunden wurden.

#### Beispiel

1. Das HTML Schnipsel
    ```
    input[type="email"]:focus,
    ```
    enthält ein Eingabeelement für `email`.
2. Das Merkmal erkennt diesen Baustein und gibt den Link entsprechend zu `values` zurück.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt, da es nur einen Link im HTML Schnipsel gibt.

#### TODO

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

### Merkmale, die nie `true` zurückgeben

Manche Merkmale sind so komplex, dass eine sichere Rückmeldung `true` nicht möglich ist.
Diese Merkmale geben lediglich `false` (Knockout) oder `unknown` zurück.
Somit haben die Nutzer*Innen lediglich einen Einblick, ob Mindestanforderungen erfüllt sind.

Beispiele:
- DSGVO
- Sicherheit

## Allgemeine TODOs

Derzeit sind Merkmale unabhängig konstruiert, d. h., viele Merkmale überprüfen selbstständig anhand einer Liste
ob deren Inhalte in der Webseite vorgefunden werden können.
Dies erzeugt Doppelungen, bspw., im Programmcode, der sich um die Verwaltung der Listen und deren Vorbereitung kümmert.
Würden bestimmte Merkmale zusammengefasst, könnte sich dadurch ein Performanceboost ergeben.
Weiterhin könnte es spannend sein, Merkmale zusammenzufassen und hernach anhand der gefundenen Listeneinträge festzustellen,
ob bspw., Popups vorhanden sind o. ä.
Inwiefern ein solcher Wandel in der Architektur lohnenswert ist, hängt auch vom jeweiligen Flaschenhals ab.
Derzeit ist die Überprüfung auf Werbung und Privatsphäre der Flaschenhals, da speziell das Plugin `adblockparser`.
Entweder wird dieses Plugin optimiert oder ersetzt.

Wie besprochen, benötigen viele der Merkmale Daten aus der Produktion, um weiter verfeinert zu werden.
Idealerweise werden die `values` der Merkmale, die neben `isHappyCase` und `probability` zurückgegeben,
hinterlegt und nachträglich ausgewertet.

Weitere Listen:
- https://github.com/hectorm/hblock