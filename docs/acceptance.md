# Merkmale & Extraktoren

Extraktoren geben drei wichtige Werte zurück:

- `stars`: Ein Rating zwischen 0 und 5 sternen, höhere Ratings bedeuten besser geeignet als OER.
- `explanation`: Eine knappe, prägnante Erläuterung warum das entsprechende rating gewählt wurde.
- `extra`: Die rohen Werte, welche das Extraktor gefunden hat. Basierend auf diesen Werten wurde das Rating bestimmt.

## "Better safe than sorry"

Für die meisten der folgenden Merkmale gilt, das eine 100 prozentige Erkennung i.d.R. nicht möglich ist. Abhängig davon
worüber das Merkmal auskunft gibt, ist es daher manchmal eine "obere Schranke der Qualität" anzugeben. Am Beispiel des
Extraktors, welcher FSK18 Inhalte erkennen soll, lässt sich dies einfach erklären:
Angenommen ein Inhalt verlinkt auf nicht jugendfreie Inhalte:
 - Hat der Extraktor dies sicher erkannt (z.B. ein Link wird durch eine Blockliste erkannt), so kann die "obere
   Schranke" als 0 Sterne angegeben werden. Die Wertung ist sicher 0 Sterne (oder schlechter).
 - Wird der Link nicht durch die Blockliste erkannt, oder es gibt eine anderweitige Ursache für einen nicht
   jugendfreien Inhalt, wird eine 5 Sterne Wertung zurückgegeben. Die Wertung ist sicher 5 Sterne __oder schlechter__.

Im Folgenden werden die verschiedenen Merkmale näher beschrieben und durch Beispiele erläutert.
# Extraktoren mit spezieller Logik
## Barrierefreiheit alias Accessibility

Dieses Merkmal gibt an, ob die Webseite barrierefrei nach
[Google Lighthouse](https://developers.google.com/web/tools/lighthouse/) ist.
Dafür wird eine Punktezahl für mobile Endgeräte und Desktop-PCs berechnet.
Deren Mittelwert wird benutzt, um eine Aussage über die Barrierefreiheit zu treffen.

Barrierefreiheit wird hierbei durch Google definiert, bspw., ob zwingend eine Maus benutzt werden muss, um die Webseite
zu navigieren.

### Vorteil

Statt händisch und subjektiv einzuschätzen, ob eine Webseite, bspw. von Blinden, eingesetzt werden kann wird hier auf ein
gepflegtes Werkzeug zurückgegriffen, welches reproduzierbare Ergebnisse liefert und damit Webseiten vergleichbar macht.

### Ablauf

1. Der Extraktor sendet die Webseite-url an einen Lighthouse Container basierend auf:
   `https://github.com/femtopixel/docker-google-lighthouse`.
2. Zurück kommen Fließkommazahlen zwischen `0` und `1`.
3. Der Wert wird für mobile Endgeräte und Desktop-PCs einzeln berechnet und dann gemittelt.
4. Der Mittelwert wird mit Schwellenwerten für die verschiedenen Rating Stufen verglichen und so das Rating bestimmt.

### Beispiel

Die url `https://canyoublockit.com/extreme-test/` liefert Werte von `0.98` für mobile Endgeräte und Desktop-PCs.
Damit liegt auch der Mittelwert bei `0.98` welcher über dem Schwellwert von `0.95` für ein 5 Sterne rating liegt.

## Cookies
__TODO: https://github.com/openeduhub/metalookup/issues/114__

Dieses Merkmal liest die Cookies ein, die von der Webseite benutzt werden.
Wird eines dieser Cookies als unsicher dargestellt, so wird dieses Merkmal als `false` definiert.
Idealerweise sollte eine Webseite so wenig Cookies wie möglich laden, bevor der Verwendung von Cookies (s. DSGVO) zugestimmt wird.
Da diese Zustimmung nicht erfolgt, sollten keine oder wenige Cookies geladen werden.

### Vorteil

Durch das Aufnehmen aller Cookies kann ein Katalog erstellt werden, anhand dessen entschieden wird, ob ein bestimmtes
Cookie akzeptabel ist oder nicht. Dies kann geschlossen für alle Webseiten erstellt werden, sodass subjektive Einflüsse
entfallen.

### Ablauf

1. Der Extraktor entnimmt alle Cookies, welche von der Webseite benutzt werden.
2. Jedes Cookie wird auf dessen Eigenschaften `httpOnly` sowie `secure` überprüft.
3. Ist eine der beiden Eigenschaften `falsch`, so wird dieses Cookie als „unsicher“ eingestuft.
4. Gibt es mindestens ein unsicheres Cookie auf der Webseite, so wird die `probability` auf `1` und
`isHappyCase` auf `false` gesetzt.

### Beispiel

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

### TODO

- Die gefundenen Cookies werden für weitere Evaluation zurückgegeben, sodass entschieden werden kann, ob Cookies auf eine Whitelist kommen.
- Cookies könnten unsicher sein, obwohl die überprüften Merkmale es als sicher anzeigen. Eine Blacklist wäre nötig.

## Dateiextrahierbarkeit alias ExtractFromFiles
- __TODO: https://github.com/openeduhub/metalookup/issues/110__
- __TODO: https://github.com/openeduhub/metalookup/issues/118__

Dieses Merkmal untersucht die herunterladbaren Dateien einer Webseite darauf, ob diese als Volltext gelesen werden können.
Unterstützte Dateiformate sind derzeit `.docx` und `.pdf`.
Können mehr als die Hälfte aller Dateien extrahiert werden, so wird ein 5 Sterne ranking zurückgegeben, sonst 0 Sterne.

### Vorteil

Statt alle Dateien händisch zu öffnen und auf Extrahierbarkeit zu untersuchen, wird direkt ein Katalog erstellt, welche
Dateien sich für eine weitere Bearbeitung durch Lehrpersonal eignen. Des Weiteren entsteht ein Überblick, wo solche Dateien
angeboten werden.

### Ablauf

1. Der Extraktor entnimmt alle Links, welche von der Webseite benutzt werden.
2. Jeder Link wird untersucht, ob er auf eine Datei mit einem unterstützten Dateiformat verweist.
3. Wird ein solcher Link gefunden, so wird die Datei heruntergeladen.
4. Lässt sich aus einer solchen Datei ohne Fehler ein Text extrahieren, so wird die Datei als lesbar eingestuft.


### Beispiel

1. Die url `https://digitallearninglab.de/unterrichtsbausteine/anlauttraining` enthält Pdf und Docx Dateien.
2. Alle Dateien sind extrahierbar, sodass ein 5 Sterne Rating zurückgegeben wird.
3. Da dies programmatisch passiert, kann lediglich durch den Nutzer überprüft werden, dass die Dateien nicht
   passwortgeschützt sind und der Text in den PDFs selektiert und kopiert werden kann.

#### TODO

- Welche weiteren Datentypen sind auf den Webseiten vorhanden?
- Diese Datentypen müssen entsprechend eingebunden und automatisch eingelesen werden
- Das Einlesen von PDFs basiert derzeit auf pdfminer.six, ein Package welches durch ein besseres ersetzt werden könnte.
- Zum Einlesen von DOCX Dateien, welche xml enthalten, wird das Package `lxml` benutzt.
  Dieses Package benötigt viel Zeit während des Baus des Docker Containers.
  Eine Alternative könnte diesen Prozess und damit CI/CD optimieren.

## DSGVO alias GDPR

Dieses Merkmal untersucht die Übereinstimmung der Webseite mit den Anforderungen der DSGVO.
Da dieses Merkmal eine juristische Behandlung nicht erfüllen kann, wird stets eine 1 Stern Wertung zurückgegeben,
wie abgesprochen.

Nichtsdestotrotz werden verschiedene Eigenschaften der Webseite untersucht und hinterlegt, um dieses Merkmal weiter zu verbessern.

Die Eigenschaften umfassen:

- Verlinkt die Seite nur auf sichere HTTPS Webseiten?
- Ist HSTS eingeschalten? Falls ja: Sind sicherheitsrelevante Eigenschaften von HSTS optimal gesetzt?
- Ist die `referrer-policy` optimal eingestellt?
- Werden keine externen Fonts geladen und falls doch, welche?
- Werden keine kompromittierende Eingaben gefordert und falls doch, welche?
- Befindet sich ein Link auf `impressum` auf der Webseite. Dies sagt nichts darüber aus, ob das Impressum korrekt ist.

### Vorteil

Ob eine Webseite DSGVO konform ist, ist eine komplexe Aussage.
Dieses Merkmal automatisiert einige relevante Überprüfungen,
sodass ungenügende Webseiten vorselektiert werden und zur detaillierteren Untersuchung durch Fachpersonal übergeben
werden können.

### Ablauf

1. Der Extraktor untersucht alle Links der Webseite, ob diese `impressum` enthalten und damit auf ein bestehendes Impressum hinweisen.
2. Es wird untersucht, ob alle Links auf `https` verweisen und damit sicher sind.
3. Es wird untersucht, ob der `strict-transport-security` Header der Webseite `includesubdomains`, `preload` sowie `max-age` enthält
und ob letzteres eine Zeitdauer über 100 Tagen enthält.
4. Es wird untersucht, ob der `referrer-policy` Header definiert ist.
5. Es wird untersucht, ob externe Fonts hinzugeladen werden, da diese auch als Sicherheitslücke ausgenutzt werden können.
Wird ein Font gefunden, gilt dies als negativ.
6. Es wird untersucht, ob auf der Webseite Eingabefelder für Passwörter, E-Mail-Adressen und mehr da ist.
Wird ein Eingabefeld gefunden, gilt dies als negativ.

### TODO

- Welche Fonts sind „akzeptabel“, welche nicht?

## Javascript
- __TODO__: https://github.com/openeduhub/metalookup/issues/151

Dieses Merkmal untersucht, ob und welche Javaskripte werden ausgeführt.
Da Javascript potenziell gefährliche Inhalte laden und ausführen kann werden 0 Sterne zurückgegeben, sobald ein
Javascript gefunden wurde welcher mittels `src` Attribut von einer anderen Quelle geladen wird.

### Vorteil

Der Extraktor scannt Webseiten automatisch auf – versteckte – Javascript, sodass Nutzer*Innen nicht erst aufwändig den HTML
Code lesen müssen.

### Ablauf

1. Der Extraktor untersucht alle `script`-Tags der Webseite, also alle HTML Elemente, die auf Skripte hinweisen.
2. Wird ein Skript gefunden, so gilt dies als negativ, auch wenn dadurch nicht sicher ist, ob das Skript negativ oder positiv ist.

### Beispiel

- In einer hypothetischen Webseite wurde das folgende HTML-Schnipsel gefunden:

```html
<script src='/xlayer/layer.php?uid='></script>
```

- Auch wenn dies kein wirkliches Skript enthält, so deutet der Schlüssel `src` auf ein Skript hin.
- Dieses wird entsprechend extrahiert und erkannt.

### TODO

- Weiter klassifizieren, welche Art Javascript akzeptabel sind und welche nicht.
- Sandbox, um Javascript auszuführen und beobachten, welche Zugriffe das Skript vollführt.
- White- and Blacklist von Javaskripten, welche akzeptabel sind – gibt es Listen, Repos etc. dafür?

## Webseite einbettbar alias IFrameEmbeddable

Dieses Merkmal untersucht, ob die Webseite in einen IFrame auf einer externen Webseite einbettbar ist.

### Vorteil

Da das Einbetten von Webseiten klar durch den Header definiert wird, der für Nutzer*Innen nicht direkt ersichtlich
ist, ermöglicht dieses Merkmal eine Entscheidung, die sonst nicht direkt möglich wäre.

### Quellen

Ob eine Webseite als IFrame einbettbar ist, wird über den Header `X-Frame-Options` definiert.
Ist dieser auf `SAMEORIGIN` oder `DENY`, so kann nicht eingebettet werden.
Dieses Merkmal steht im Kontrast zum Sicherheitsmerkmal, welches denselben Header untersucht.

### Ablauf

Der Webseitenheader wird auf `X-Frame-Options` geprüft. Ist der Header vorhanden und auf `SAMEORIGIN` oder `DENY`
gesetzt, so wird eine 0 Sterne Wertung zurückgegeben, ist der Header nicht gesetzte oder hat einen anderen Wert, wird
eine 5 Sterne Wertung zurückgegeben.

#### Beispiel

1. Der Webseitenheader
    ```json
    {"x-frame-options": "same_origin"}
    ```
    enthält den korrekten Header.
3. Damit wird `isHappyCase` als `false` gesetzt.
4. Die `probability` wird hier auf `1.0` gesetzt.

## Gefährliche Dateierweiterungen alias MaliciousExtensions

Dieses Merkmal untersucht, ob und welche bekannten "gefährlichen" und "potenziell gefährlichen" Dateiendungen in Dateien
der Webseite vorkommen.
Beispiele für "gefährlich" enthalten, u. a., `.exe`, `.com` und `.dll`.
Dieses Merkmal ist noch recht grob und resultiert in einem 0 Sterne Rating, sobald irgendeine Datei mit "gefährlicher"
Endung gefunden wird, werden nur "potenziell gefährliche" Endungen gefunden werden 4 Sterne zurückgegeben. Wird keines
von beiden gefunden werden 5 Sterne zurückgegeben.

### Vorteil

Der Extraktor scannt Webseiten automatisch auf potenziell gefährlichen Dateiendungen, sodass diese Seiten explizit
auf ihre Eignung für den Schulunterricht untersucht werden können.

### Quellen

Die Dateiendungen wurden extrahiert aus:

```
https://www.file-extensions.org/filetype/extension/name/dangerous-malicious-files
https://www.howtogeek.com/137270/50-file-extensions-that-are-potentially-dangerous-on-windows/
https://sensorstechforum.com/file-types-used-malware-2019/
https://www.howtogeek.com/127154/how-hackers-can-disguise-malicious-programs-with-fake-file-extensions/
```

### Ablauf

1. Der Extraktor untersucht alle Links der Webseite auf Dateien mit Dateiendungen.
2. Die Dateiendung wird mit den einprogrammierten Endungen verglichen.

### Beispiel

1. Die url `https://digitallearninglab.de/unterrichtsbausteine/anlauttraining` enthält Pdf und Docx Dateien.
2. Da diese "nur potenziell gefährlich" sind, wird für diese Webseite ein 4 Sterne Rating zurückgegeben.

## Sicherheit alias Security

Dieses Merkmal untersucht verschiedene HTTP-Header Eigenschaften, um Aussagen über optimal konfigurierte
Sicherheitseinstellungen zu liefern.
Sind alle Eigenschaften gesetzt, so erfolgt eine 5 Sterne Wertung, d.h., es ist strikt.
Es ist zu erwarten, dass nur die wenigsten Webseiten dieses Merkmal erfüllen.
Für Information zu den verschiedenen Headern siehe z.B.: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers

### Vorteil

Ähnlich zu DSGVO ist Sicherheit ein komplexes Thema, welches durch dieses Merkmal teilautomatisiert wird, sodass
auffällig unsichere Webseiten früh aussortiert werden können.

### Ablauf

1. Der Extraktor untersucht, ob die folgenden Header gesetzt sind:

    `content-security-policy`
    `referrer-policy`

2. Wird eines der Merkmale nicht gefunden, so ist das negativ.
3. Es überprüft, ob `cache-control` so gesetzt wurde, dass Daten nicht gecached werden
4. Es überprüft, ob `x-content-type-options` auf `nosniff` gesetzt wurde.
5. Es überprüft, ob `x-frame-options` auf `deny` oder `same_origin` gesetzt wurde.
Damit kann die Webseite nicht als iFrame eingebettet werden.
6. Es überprüft, ob `x-xss-protection` auf `1` und `mode=block` gesetzt wurde und damit cross-site-scripting deaktiviert.
7. Es überprüft, ob `strict-transport-security` auf `max-age=` und `includeSubDomains` gesetzt wurde.

### TODO

- Weitere Informationen aus Header und HTML könnten Hinweise geben, ob die Webseite kompromittiert ist.
- Eine Verbindung mit den Merkmalen schädliche Dateiendungen u.ä. könnte ein wertvolleres Gesamtbild ergeben.

# Extraktoren basierend auf Blocklisten (Blacklists)
Mehrere unterschiedliche Merkmale lassens ich auf Basis des gleichen Mechanismus extrahieren. Dazu gehören u.a.

 - `advertisement`: Das Erkennen von Werbung und zugehörigen ungewollte Frames, Bildern oder Objekten
 - `anti_addblock`: Das Erkennen von Elementen, die Werbeblocker erkennen und entsprechend den Nutzenden
    auffordern diese Werbeblocker zu deaktivieren.
 - `easy_privacy`: Das Erkennen von Trackern welche die Privatsphäre der Nutzer kompromittieren
 - `fanboy_annoyance`: Das Erkennen von „nervigen“ Elemente zu entdecken, z.B. Pop-Ups oder Banner.
 - `fanboy_notification`: Das Erkennen von Elementen welche versuchen Benachrichtigungen auf dem Endgerät anzuzeigen.
 - `fanboy_social_media`: Das Erkennen von Elementen die zu sozialen Netzwerken verlinken (z.B. der Facebook Like-Button
   oder Twitter Einblendungen).
 - `easylist_germany`: Erkennen von speziell deutschsprachigen störenden Inhalten
 - `easylist_adult`: Erkennen von Links auf nicht jugendfreie Inhalte

Der Name `Fanboy` ist der Alias eines Software-Ingenieurs: `https://github.com/ryanbr`.

Mit Blocklisten welche Filterregeln enthalten lassen sich solche Elemente oft gut erkennen. Für die
verschiedenen genannten Punkte können verschiedene Blocklisten verwendet werden, sodass eine granulare Analyse möglich
wird. Diese Listen werden für AdBlock-artige Plugins im Browser benutzt, um entsprechend Werbung zu blockieren.
Die Syntax ermöglicht Elemente explizit zu blockieren oder zu erlauben, ganze Domänen zu sperren oder nur gewisse
Bausteine einer Webseite zu erlauben. Die Semantik der Filterregeln kann
[hier](https://adblockplus.org/filter-cheatsheet) nachvollzogen werden. Die Vorteile eines solchen Ansatzes sind
vielseitig:

- Erkennung von versteckten Elementen
- Keinerlei menschliche subjektive Entscheidungen nötig
- Kein aufwendiges Suchen durch Editoren oder Redakteure
- gut gepflegte und aktuelle Blocklisten durch die Community (z.B. durch Browser Plugins wie AddBlockPlus)

Der größte Schwachpunkt eines solchen Ansatzes ist, dass niemals vollständig garantiert werden kann, dass alle
schädlichen oder unerwünschten Inhalte erkannt werden, da z.B. neu aufkommende Ad-Scripte zunächst zu den Blocklisten
hinzugefügt werden müssen.

### Ablauf
Im Ablauf sind alle diese Extraktoren gleichartig, der einzige Unterschied besteht in den verwendeten Blocklisten.
Welche Blocklisten verwendet werden ist einfach in [adblock_based.py](../src/metalookup/features/adblock_based.py)
ersichtlich. Diese werden zur Startzeit des Services durch den entsprechenden Extraktor aus dem online Repository
geladen und sind so stets relativ aktuell. Für eine eingehende URL werden dann

1. Alle Links auf der Webseite werden mit diesen Filterregeln verglichen.
2. Falls eine Übereinstimmung gefunden wurde, so wird eine 0 Sterne Wertung zurückgegeben.

### TODOs
- Weitere Listen:  https://github.com/hectorm/hblock
- Advertisment
  - Welche Art von Werbung wird bisher akzeptiert, kann also auf eine whitelist gesetzt werden?
  - Reicht es abzubrechen, sobald ein Werbeelement entdeckt wurde (Performanceverbesserung möglich)?
  - AdblockParser forken und optimieren. Dieses Plugin ist derzeit der Flaschenhals.
  - Dieses Merkmal kann mit anderen Merkmalen zusammengefasst werden, bspw. EasyPrivacy
  - Da dies der derzeitige Flaschenhals ist, sollte evaluiert werden, ob dieser Teil in einer low-level Sprache
    implementiert wird.
- FanboyAnnoyance
  - Weitere Listen sind verfügbar und können zusammengefasst werden, bspw. mit FanboySocialMedia
- FanboySocialMedia
  - Teilweise doppeln sich Einträge aus den Listen. Eine Zusammenfassung der Listen und entsprechende Konsolidierung könnte
    Performanceverbesserungen bringen.
- EasyListAdult
  - Die Auswertung bezieht sich allein auf Links. Der Fließtext der Webseite, sowie eingebettete Dateien, Audio- und
    Videolinks und deren Inhalte werden bisher nicht untersucht.

# Extraktoren basierend auf einer festen Menge von "keywords"

Neben einer Verwendung von Blacklists, lässt sich auch einfach der komplette HTML Inhalt nach speziellen "keywords"
durchsuchen. Eine solche Suche kann deutlich schneller sein, da keine komplexen "pattern matching" regeln wie bei den
Blocklisten durchgeführt werden müssen. Es können jedoch auch mehr falsche Treffer gefunden werden - besonders für
kurze und prägnante Schlüsselworte wie z.B. `e-mail` oder `input`. Wird eines der Schlüsselwörter gefunden, so wird
eine 0 Sterne Wertung zurückgegeben. Das `extra` Feld beinhaltet die Menge der gefundenen Schlüsselwörter.

Die Stichwörter wurden manuell ausgewählt anhand einer Vielzahl von Webseiten mit Paywalls, RegistrationWalls, Popups,
oder Login anforderungen (z.B. Online-Zeitungen). **TODO**:  Weitere Beispielwebseiten mit diesem Merkmal sollten
erfasst und untersucht werden.

Aktuell mit einem solchen Verfahren implementiert sind folgende Extraktoren

- **Bezahlbarrieren alias Paywalls**: Untersucht, ob die Webseite Barrieren beinhaltet, sodass Inhalte nur gegen
  Bezahlung konsumiert werden können.

- **PopUp**: Untersucht, ob die Webseite Popups beinhaltet.

- **Registrierbarriere alias RegWall**: Untersucht, ob die Webseite Barrieren beinhaltet, sodass Inhalte nur nach
  erfolgter Registrierung konsumiert werden können.

- **LogInOut**: Untersucht, ob die Webseite Login/Logout Eingaben beinhaltet und damit potenziell den Nutzer auffordert
  sich einzuloggen. Es werden ausschließlich HTML Eingabeobjekte untersucht.

# Allgemeine TODOs
Derzeit sind Merkmale unabhängig konstruiert, d.h., viele Merkmale überprüfen selbstständig anhand einer Liste
ob deren Inhalte in der Webseite vorgefunden werden können.
Dies erzeugt Doppelungen, bspw., im Programmcode, der sich um die Verwaltung der Listen und deren Vorbereitung kümmert.
Würden bestimmte Merkmale zusammengefasst, könnte sich dadurch ein Performanceboost ergeben.
Weiterhin könnte es spannend sein, Merkmale zusammenzufassen und hernach anhand der gefundenen Listeneinträge festzustellen,
ob bspw., Popups vorhanden sind o.ä.
Inwiefern ein solcher Wandel in der Architektur lohnenswert ist, hängt auch vom jeweiligen Flaschenhals ab.
Derzeit ist das Abrufen des Inhalts via Splash, sowie die `accessibility` Analyse via Lighthouse der Flaschenhals.

Wie besprochen, benötigen viele der Merkmale Daten aus der Produktion, um weiter verfeinert zu werden.
Idealerweise werden die `extras` der Merkmale, die neben `stars` und `explanation` zurückgegeben werden,
hinterlegt und nachträglich ausgewertet.

## Weitere Merkmale
- Verlustfreie und verlustbehaftete Bilder: wird ein verlustfreies Bild gefunden, welches einem verlustbehafteten entspricht, sodass ersteres bevorzugt werden kann?
- PG18/FSK18
- FAIR data
- Wie werden Webseiten auf Google indiziert? SEO-Thema
- SVGs
- RDFa
- GDPR/DSGVO
