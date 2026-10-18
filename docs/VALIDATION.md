# Tests et validation

## Environnement de test

- CPython 3.14.8.
- Home Assistant 2026.10.2.
- `pytest-homeassistant-custom-component==0.13.373`.
- Ruff 0.17.1.

La dernière exécution complète a produit **50 tests réussis**, dont 28 tests
unitaires et 22 tests avec le logiciel Home Assistant. Le Bluetooth et les
écouteurs sont simulés ; cette suite ne constitue pas un test matériel.

## Exécuter les contrôles

Depuis la racine du projet, avec Python 3.14 :

```bash
python -m pip install -r requirements_test.txt
python -m pytest -q --disable-warnings --tb=short
```

Les tests autonomes du protocole, du client et de la sélection d’appareils
peuvent aussi être exécutés avec Python 3.12 ou ultérieur :

```bash
python3 -m unittest tests.test_protocol tests.test_client tests.test_discovery -v
```

## Couverture

- Construction et décodage des trames, fragmentation, concaténation et données invalides.
- Vérification du modèle, délais, réponses et notifications.
- Fermeture des connexions et arrêt des opérations en cours.
- Lecture des batteries, de la charge, du firmware et des réglages.
- Écriture des gestes, conservation du côté opposé et relecture après modification.
- Formulaires de configuration, sélection BlueZ, doublons et saisie manuelle.
- Options d’actualisation, minuterie, disponibilité et horodatage.
- Entités, traduction des états et export diagnostic sans adresse ni numéro de série.

Les contrôles de présentation comprennent la validité des JSON, la cohérence
des libellés anglais et les icônes de charge pour les états actif, inactif et inconnu.
HACS et Hassfest n’ont pas été exécutés.

## Limites matérielles

| Fonction | État de validation matérielle |
| --- | --- |
| Connexion et lecture complète | Fonctionnement confirmé sur Redmi Buds 6 Play |
| Batteries, série et réglages | Lectures comparées à l’application Xiaomi Earbuds |
| Charge | Transitions et comportement boîtier fermé à vérifier |
| Faible latence | Écriture ON/OFF confirmée ; persistance du réglage à vérifier |
| Profils audio | Cinq profils lus ; écriture confirmée pour Balanced sound |
| Gestes simples, doubles et triples | Écritures confirmées ; toutes les combinaisons et la conservation du côté opposé restent à vérifier sur le matériel |
| Appuis longs | Lecture confirmée ; écriture directe à valider sur le matériel |
| Action photo | Couplage simple/long observé ; règles complètes non établies |
| Firmware | Correspondance connue de la signature 20222022 vers 2.0.2.2 ; autres signatures affichées brutes |
| Connexion du téléphone | Contention possible ; reprise audio et stabilité prolongée à vérifier |

Les tests automatisés ne valident ni le comportement physique des gestes ni
la cohabitation audio avec le téléphone. Voir le [guide utilisateur](../DOCS.md)
pour la configuration et le dépannage.
