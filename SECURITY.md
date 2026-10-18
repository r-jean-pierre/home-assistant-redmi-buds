# Politique de sécurité

## Versions prises en charge

Les correctifs de sécurité sont apportés à la dernière version publiée.
Si vous utilisez une version plus ancienne, mettez l’intégration à jour avant
de vérifier si le problème est toujours présent.

Avant la première publication, les signalements concernent la branche `main`.

## Signaler une vulnérabilité

Merci de signaler les vulnérabilités en privé, sans ouvrir d’issue publique ni
de pull request contenant les détails d’exploitation.

Sur GitHub, utilisez **Security → Advisories → Report a vulnerability** :

[Signaler une vulnérabilité](https://github.com/r-jean-pierre/home-assistant-redmi-buds/security/advisories/new)

Si cette option est indisponible, contactez le mainteneur par un canal privé
avant de transmettre les détails techniques. Ne publiez pas de preuve
d’exploitation dans une issue pour demander un contact.

Un signalement utile comprend :

- la version de l’intégration et de Home Assistant ;
- le type d’installation et l’adaptateur Bluetooth utilisé ;
- une description du problème et de son impact ;
- les conditions nécessaires et les étapes pour le reproduire ;
- une preuve de concept minimale, si disponible.

Retirez les mots de passe, jetons, adresses Bluetooth et numéros de série des
journaux et captures. N’envoyez pas de sauvegarde complète de Home Assistant.

## Traitement des signalements

Le mainteneur examine le signalement et peut demander des informations
complémentaires. Lorsqu’une vulnérabilité est confirmée, la correction et la
publication des détails sont coordonnées avec la personne qui l’a signalée.
Le délai dépend de la gravité du problème et de la disponibilité du mainteneur.

Merci de laisser le temps de préparer un correctif avant de rendre les détails
publics. Les contributions peuvent être créditées avec l’accord de leur auteur.

## Périmètre

Cette politique concerne le code de l’intégration Redmi Buds 6 Play et ses
fichiers de configuration. Les vulnérabilités de Home Assistant, de BlueZ ou
du firmware des écouteurs doivent être signalées aux projets ou fournisseurs
concernés.

Pour un problème de connexion, un réglage qui ne persiste pas ou une demande
de fonctionnalité sans impact de sécurité, utilisez les issues du dépôt.
