# Architecture

## Organisation

```text
custom_components/redmi_buds/
  mma/                 Codec et client indépendants de Home Assistant
  config_flow.py       Choix par nom ou saisie manuelle, vérification VID/PID ; options
  coordinator.py       Sérialisation asyncio et exécution hors boucle
  entity.py            Identité stable et disponibilité
  sensor.py            Batteries, longs, date, diagnostics locaux
  binary_sensor.py     Charge
  switch.py            Faible latence
  select.py            EQ et taps
  button.py            Actualisation
  diagnostics.py       Export par liste de champs autorisés
```

Le transport synchrone ne dépend que de la bibliothèque standard. Un verrou de
thread protège les transactions, y compris si un appelant asyncio est annulé.
Un verrou asyncio du coordinateur sérialise les lectures et écritures. Une socket
appartient à une seule transaction ; fermeture sur succès, erreur et arrêt.
L’arrêt ferme la socket active pour interrompre une lecture, puis attend la fin
de l’opération avant de terminer le déchargement.

Le parseur respecte la longueur annoncée, bornée à 1024 octets de corps. Il
conserve un préfixe d’en-tête fragmenté, traite les trames concaténées et se
resynchronise sur les en-têtes après longueurs invalides ou mauvais terminateurs.
Un `EF` dans les données ne termine pas la trame. Un en-tête à longueur plausible
mais incomplet reste en attente jusqu’à réception de la suite ou expiration du délai.

Une réponse n’achève une requête que si type réponse, opcode, séquence et statut
conviennent. Les notifications reçues pendant les échanges sont acquittées
lorsqu’elles le demandent. Elles ne remplacent pas la relecture complète et ne
sont pas transformées en événements physiques de gestes. Une requête entrante
inconnue reçoit le statut `FF`. Les acquittements utilisent les flags `00`.

Les délais sont bornés : connexion 15 s, réponse 5 s, échanges de session 30 s.
Les séquences évoluent modulo 256 avec une valeur initiale aléatoire. Aucune
écriture n’est réessayée automatiquement.

L’export diagnostic utilise une liste explicite de champs et n’inclut ni
configuration d’entrée brute, ni nom libre, ni MAC, ni série, ni trame complète,
ni message d’exception arbitraire. Les octets bruts de batteries et firmware
restent disponibles dans cet export.

## Sélection des appareils appairés

Le module `mma/bluez.py` lit les objets gérés de BlueZ via le helper
`bluetooth_adapters.dbus.get_dbus_managed_objects`, fourni par la dépendance
Bluetooth native de HA. Ce helper décode les variants et ferme sa connexion
D-Bus. Un délai global de cinq secondes borne sa lecture. Le parseur conserve
les `org.bluez.Device1` appairés, non bloqués, à adresse publique valide,
privilégie l’alias pour l’affichage et regroupe une adresse présente sur
plusieurs contrôleurs.

Les noms servent au tri et à la présélection. Après validation du choix, une
lecture du VID/PID vérifie le modèle. Les appareils déjà configurés sont
écartés de la liste. La sélection ne lance ni appairage ni scan radio.
