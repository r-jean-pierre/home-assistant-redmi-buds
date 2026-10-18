# Redmi Buds 6 Play pour Home Assistant

![Redmi Buds 6 Play](custom_components/redmi_buds/brand/icon.png)

Intégration personnalisée pour consulter la batterie et configurer les
**Redmi Buds 6 Play** depuis Home Assistant. Connexion Bluetooth directe,
configuration dans l’interface et traductions en français et en anglais.

[English](README.en.md) · [Guide d’utilisation](DOCS.md)

## Fonctionnalités

- Niveau de batterie et état de charge de chaque écouteur et du boîtier.
- Réglage de la faible latence et des cinq profils audio.
- Configuration des appuis simples, doubles, triples et longs, à gauche et à droite.
- Actualisation manuelle ou périodique et date de dernière lecture réussie.
- Version du firmware, référence du modèle et numéro de série.

Les réglages de gestes modifient les actions des écouteurs. Ils ne génèrent
pas d’événements d’appui utilisables dans les automatisations Home Assistant.

## Prérequis

- Home Assistant sous Linux, avec un adaptateur Bluetooth classique local accessible à Core.
- Écouteurs Redmi Buds 6 Play déjà appairés à cet adaptateur.

Les proxys Bluetooth BLE ESPHome ne prennent pas en charge cette connexion.
Seul le modèle Redmi Buds 6 Play est pris en charge. L’environnement logiciel
utilisé pour les tests est indiqué dans [VALIDATION.md](docs/VALIDATION.md).

## Installation

1. Télécharger et extraire le projet.
2. Copier `custom_components/redmi_buds` dans `/config/custom_components/redmi_buds`.
3. Redémarrer Home Assistant.
4. Ouvrir le boîtier, réveiller les écouteurs et déconnecter temporairement le téléphone.
5. Ouvrir **Paramètres → Appareils et services → Ajouter une intégration**,
   puis rechercher **Redmi Buds 6 Play**.
6. Sélectionner les écouteurs dans la liste des appareils appairés.
7. Sur la fiche de l’appareil, appuyer sur **Actualiser**.

La saisie manuelle de l’adresse Bluetooth reste disponible si les écouteurs
ne figurent pas dans la liste. L’intégration vérifie le modèle à la connexion.
L’appairage initial et le dépannage sont décrits dans le [guide](DOCS.md).

## Actualisation

L’actualisation est **manuelle par défaut**. Dans les options de l’intégration,
choisir `0` pour le mode manuel ou un intervalle de **5 à 1440 minutes**.
Les valeurs correspondent à la dernière lecture réussie.

Une connexion depuis Home Assistant peut gêner la connexion audio du téléphone.
Choisir un intervalle adapté à cet usage. Après un redémarrage en mode manuel,
appuyer sur **Actualiser** pour obtenir les valeurs.

## Mise à jour

Remplacer `/config/custom_components/redmi_buds`, puis redémarrer Home Assistant.
Il n’est pas nécessaire de supprimer l’intégration ni de la configurer à nouveau.

## Documentation

- [Utilisation et dépannage](DOCS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Tests et limites de validation](docs/VALIDATION.md)
- [Changelog](CHANGELOG.md)

Code sous [licence MIT](LICENSE). Les attributions des ressources tierces
figurent dans [NOTICE.md](NOTICE.md). Projet indépendant de Xiaomi.
