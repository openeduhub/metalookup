# Akzeptanzkriterien

Dieser Abschnitt erläutert was die verschiedenen Merkmale untersuchen und wie dies überprüft werden kann.

Automatisierte Akzeptanztests sind in `tests/e2e/e2e_test.py` zu finden.
Dieser Test baut alle Docker Container, schickt eine Test-Webseite zur Überprüfung und evaluiert alle
Merkmale auf erwartetes Verhalten.

Die Unit- und Integrationstests vertiefen dies weiter.

## Merkmale

### Barrierefreiheit alias Accessibility

Dieses Merkmal gibt an, ob die Webseite barrierefrei nach Google Lighthouse ist.
Dafür wird eine Punktezahl für mobile Endgeräte und Desktop-PCs berechnet.
Deren Mittelwert wird benutzt, um eine Aussage über die Barrierefreiheit zu treffen.
Ist der Mittelwert hoch genug, gilt Barrierefreiheit als `wahr`.

### Cookies

Dieses Merkmal liest die Cookies ein, die von der Webseite benutzt werden.
Wird eines dieser Cookies als unsicher dargestellt, so wird dieses Merkmal als `wahr` definiert.

### Dateiextrahierbarkeit alias ExtractFromFiles

Dieses Merkmal untersucht die herunterladbaren Dateien einer Webseite darauf, ob diese als Volltext gelesen werden können.
Unterstützte Dateiformate sind derzeit `.docx` und `.pdf`.
Wenn mehr als die Hälfte aller Dateien extrahiert werden können, so gilt dieses Merkmal als `wahr`.

TODO:
- Welche weiteren Datentypen sind auf den Webseiten vorhanden?

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

### Javascript

Dieses Merkmal untersucht, ob und welche Javascripts werden ausgeführt. 
Da Javascript potenziell gefährliche Inhalte laden und ausführen kann wird dieses Merkmal `wahr` anzeigen, sobald ein Javascript gefunden wurde.

TODO:
- Weiter klassifizieren, welche Art Javascript akzeptabel sind und welche nicht

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

### Werbung alias Advertisment

Dieses Merkmal nutzt Adblock-Listen, um Werbung zu erkennen.
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
Es nutzt dafür gepflegte open-source Online-Listen.
Wird ein solches Cookie entdeckt, so wird dieses Merkmal auf `wahr` gesetzt.

### FanboyAnnoyance

Dieses Merkmal versucht „nervige“ Elemente zu entdecken.
Es nutzt dafür gepflegte open-source Online-Listen.

### Benachrichtigungen alias FanboyNotification

Dieses Merkmal untersucht, ob die Webseite Elemente beinhaltet, die versuchen Benachrichtigungen auf dem Endgerät zu erzeugen.
Es nutzt dafür gepflegte open-source Online-Listen.

### Soziale Netzwerke alias FanboySocialMedia

Dieses Merkmal untersucht, ob die Webseite Elemente beinhaltet, die auf soziale Netzwerke verlinken.
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

TODO:
- Weitere Beispielwebseiten mit diesem Merkmal sollten erfasst und untersucht werden.


### Weitere Merkmale

TODO:
- Lossless vs lossy images
- PG18/FSK18
- FAIR data
- how a website is indexed on google
- Copyright
- SVGs
- RDFa
- GDPR/DSGVO