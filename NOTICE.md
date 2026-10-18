# Références

Ce projet est indépendant de Xiaomi. Les noms de produits appartiennent à leurs
propriétaires et servent à identifier le modèle pris en charge.

Cette intégration utilise le protocole MMA sur Bluetooth RFCOMM.

Références consultées :

- XiaomiTWS / `web1n/android_packages_apps_XiaomiTWS`, licence Apache-2.0,
  commit `0927e57cae772ac1016691b0930fb279fff51229` : types MMA, marqueurs,
  ACK et décodages.
  https://github.com/web1n/android_packages_apps_XiaomiTWS
- MiBudsClient / CesurPolat, référence de protocole ; aucun code de ce projet n’est incorporé.
  https://github.com/CesurPolat/MiBudsClient
- TWS-Pods-PC / Zhaoyi-ya : documentation tierce de rétro-ingénierie,
  consultée pour le contexte des indicateurs de trame ; aucun code incorporé.
  https://github.com/Zhaoyi-ya/TWS-Pods-PC/blob/main/xiaomi/PROTOCOL.md

## Photo produit

Les fichiers `assets/REDMI_Buds_6_Play_1.png`,
`custom_components/redmi_buds/brand/icon.png` et `icon@2x.png` proviennent de
l’image produit MiStore Sweden. La provenance, l’empreinte et
les adaptations sont consignées dans `custom_components/redmi_buds/BRANDING.md`.
Cette image tierce et ses adaptations ne sont pas couvertes par la licence MIT
du code. La source ne précise pas la licence de l’image.
