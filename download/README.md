# GEM5

## Description
La simulation a été effectuée sur narval. Ce script sert à transférer les données
sur pampa.

## Liste des fichiers
  - GEM_download.bash  
  
## Exemple de soumission:  
YYYY=2014; soumet GEM_download.bash -args $YYYY -jn GEM_download\_${YYYY} -t 17280  


## Notes:
  1. Temps de téléchargement (1 année): moins de 24 heures
  2. Pour télécharger step0 (requis pour créer le masque terre-mer), il suffit 
  de mettre YYYY=step0
  3. Le réperoire de sortie est "hardcodé" dans le script mais peut évidemment
  être édité au besoin.
  




# MODIS
## Description
Ce script sert à télécharger les données des produits  MOD06_L2 (Terra) et 
MYD06_L2 (Aqua).

## Liste des fichiers
  - MODIS_download.bash
  
## Exemple de soumission:  
dataset=MYD06_L2; YYYY=2015; dddi=334; dddf=365;  
soumet MODIS_download.bash -args $dataset $YYYY $dddi $dddf -jn ${dataset}\_downloadi\_${YYYY}\_${dddi}-${dddf} -t 86400

## Notes:
  1. Temps de téléchargement (1 année): environ 2 semaines (avec 4 cpus)
  2. Le téléchargement de ces produits est particulièrement inefficace car on
  doit télécharger chaque fichier individuellement (il y en 12 par heures) et 
  wget doit se (re)-connecter à plusieurs reprise avant de pouvoir compléter un
  téléchargement avec succès. Un piste à explorer pour un futur usgae serait 
  d'utiliser lftp (pour télécharger un "répertoire" au complet -- chaque 
  "répertoire" correspond à un jour --> 24 x 12 = 288 fichiers).
  4. Si on s'interesse à la plage de données de 2014-2015, on doit aussi 
  télécharger la première demi-heure de 2013 et la première de 2016.
  5. Un clé d'authorisation doit être générée sur le site web (voir ci-dessous).
  6. Le réperoire de sortie est "hardcodé" dans le script mais peut évidemment
  être édité au besoin.

## Références
  - Info          : https://atmosphere-imager.gsfc.nasa.gov/products/cloud
  - Téléchargement: https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61


# CALIPSO
## Description
Ce script sert à télécharger les données du produit CAL_LID_L2_05kmCPro-Standard-V4

## Liste des fichiers
  - CALIPSO_download.bash  
  - CAL_LID_L2_2014.txt
  - CAL_LID_L2_2015.txt

## Exemple de soumission:  
YYYY=2014; soumet CALIPSO_download.bash -args $YYYY -jn CALIPSO_download\_${YYYY} -t 345600

## Notes:
  1. Temps de téléchargement (1 année): environ 3 jours
  2. En plus du script de téléchargement, un lsite des fichiers à télécharger 
  est nécessaire. Cette liste peut être générer en se connecctant au site de
  téléchargement (voir ci-dessous).
  3. Un nom d'usager et un mot de passe sont requis pour télécharger les 
  données (on doit donc s'inscrire au site de téléchargeemnt - voir ci-dessous).
  4. Le réperoire de sortie est "hardcodé" dans le script mais peut évidemment
  être édité au besoin.

## Références

  - Info          : https://www-calipso.larc.nasa.gov/resources/calipso_users_guide/data_summaries/profile_data_v420.php
  - Téléchargement: https://search.earthdata.nasa.gov/search?q=CAL_LID_L2_05kmCPro-Standard-V4-20

