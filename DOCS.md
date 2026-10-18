# Utilisation et dépannage

## Appairer les écouteurs

Les écouteurs doivent être appairés au contrôleur Bluetooth local de Home
Assistant avant l’ajout de l’intégration. Un appairage avec le téléphone seul
ne suffit pas. Si les écouteurs sont déjà appairés à Home Assistant, conserver
cet appairage.

Si votre installation donne accès à `bluetoothctl`, lancer :

```bash
bluetoothctl
```

Dans l’invite interactive, rechercher les écouteurs, puis remplacer
`AA:BB:CC:DD:EE:01` par leur adresse :

```text
power on
agent on
default-agent
scan on
pair AA:BB:CC:DD:EE:01
trust AA:BB:CC:DD:EE:01
scan off
quit
```

Le terminal utilisé doit avoir accès au contrôleur Bluetooth de Home Assistant.
Ouvrir le boîtier et placer les écouteurs en mode appairage selon leur notice.

## Ajouter l’intégration

Dans **Paramètres → Appareils et services → Ajouter une intégration**,
rechercher **Redmi Buds 6 Play**, puis choisir les écouteurs par leur nom.
Après un nouvel appairage, rouvrir le formulaire pour actualiser la liste.

Si la liste est vide ou inaccessible, utiliser la saisie manuelle de l’adresse
Bluetooth. Le canal par défaut est **6**. Le nom affiché ne suffit pas à
identifier un modèle compatible : l’intégration vérifie l’appareil à la connexion.

## Consulter les mesures

Appuyer sur **Actualiser** sur la fiche appareil pour lire les batteries,
la charge et les réglages. Les niveaux de batterie sont exprimés en pourcentage ;
les états de charge indiquent si l’élément est en charge.

Les valeurs restent celles de la dernière lecture. Si une lecture échoue,
les mesures deviennent indisponibles et la date de dernière lecture réussie
reste visible. Réveiller les écouteurs, puis actualiser de nouveau.

Les capteurs **Firmware version** et **Serial number** sont désactivés par
défaut. Ils peuvent être activés depuis la liste des entités de l’appareil.
Une version de firmware non reconnue s’affiche sous sa forme brute.

## Régler l’actualisation automatique

Ouvrir les options de l’intégration depuis **Paramètres → Appareils et services**.

| Valeur | Fonctionnement |
| --- | --- |
| `0` | Actualisation manuelle |
| `5` à `1440` | Intervalle en minutes |

L’activation d’un intervalle déclenche une lecture. En mode manuel, aucune
lecture automatique n’est effectuée au démarrage : utiliser **Actualiser**.
Une interrogation peut perturber la connexion du téléphone.

## Modifier les réglages

Les sélecteurs de la section **Configuration** permettent de modifier les gestes.
Les libellés anglais correspondent à ceux de l’application Xiaomi Earbuds.

| Geste | Gauche | Droite |
| --- | --- | --- |
| Simple | Tap left earphone once | Tap right earphone once |
| Double | Double tap left earphone | Double tap right earphone |
| Triple | Triple tap left earphone | Triple tap right earphone |
| Long | Press and hold left earphone | Press and hold right earphone |

Les appuis simples, doubles et triples proposent **None**, **Play/Pause**,
**Volume up**, **Volume down**, **Previous song**, **Next song** et **Take photo**.
Les appuis longs proposent **None**, **Voice assistant** et **Take photo**.
Les capteurs d’appui long dans **Diagnostic** affichent uniquement l’état ;
utiliser les sélecteurs de **Configuration** pour le modifier.

**Audio balance** propose Balanced sound, Enhance Voice, Enhance Bass,
Enhance Treble et Boost Volume. **Low latency** active ou désactive la faible latence.

Après une modification, l’intégration relit les réglages. Certaines actions,
notamment **Take photo**, peuvent également modifier un autre geste.
La fonction photo nécessite un téléphone compatible Xiaomi HyperOS et n’est
pas disponible en double connexion, selon l’application Xiaomi Earbuds.

Si une erreur survient après une modification, **actualiser avant de réessayer** :
le réglage peut avoir été appliqué malgré une confirmation manquante.

## Résoudre un problème de connexion

- Vérifier que l’adaptateur Bluetooth classique local est accessible à Home Assistant.
- Ouvrir le boîtier, réveiller les écouteurs et les rapprocher de l’adaptateur.
- Déconnecter temporairement le téléphone et fermer les autres applications utilisant les écouteurs.
- Vérifier l’appairage au contrôleur de Home Assistant, puis actualiser.

Si le téléphone ne reprend pas l’audio, déconnecter les écouteurs du contrôleur
Home Assistant. Depuis un terminal ayant accès à ce contrôleur :

```bash
bluetoothctl disconnect AA:BB:CC:DD:EE:01
```

Remplacer l’adresse par celle des écouteurs. Cette commande coupe leurs
connexions sur ce contrôleur sans supprimer l’appairage. L’intégration ne
l’exécute pas automatiquement. Privilégier le mode manuel si les lectures
périodiques gênent l’usage audio.

## Signaler un problème

Indiquer la version de Home Assistant, le type d’installation, l’adaptateur
Bluetooth, le message d’erreur et les étapes permettant de reproduire le problème.
Les diagnostics téléchargeables de l’intégration excluent l’adresse Bluetooth
et le numéro de série. Vérifier les autres journaux et captures avant de les publier.
