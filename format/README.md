# Contenu
  1. Résumé
  2. Structure générale
  3. Description détaillée des scripts

# Résumé
Ce répertoire contient les scripts qui servent à "formater" les trois jeux de données.  

**GEM5** 
 - Conversion: fst --> NetCDF

**CALIPSO** 
 - Conversion: hdf --> NetCDF
 - Sélection des traces qui passent dans le domaine d'intérêt (liste de fichiers).

**MODIS**
 - Conversion: hdf --> NetCDF
 - Interpolation vers le domaine d'intérêt + fusion des fichiers de 5 min --> fichiers horaires
 - Fusion MYD06_L2 et MOD06_L2 --> MCD06_L2.


&nbsp;
# Structure générale

&nbsp;
**Scripts principaux et scripts de lancement**
À chacun des scripts principaux (debutant par le préfixe main) correspond un script de lancement (débutant par le préfixe submit). Par exemple:
> Pour lancer `main_GEM5_01_format.bash`, on utilise `submit_GEM5_01_format.bash`
  
&nbsp;
**Ordre de lancement**
Les scripts de lancements sont numérotés pour chaque jeux de données (GEM5, CALIPSO, MODIS) et ils doivent être lancés dans l'ordre correspondant. Par exemple:
> `main_CALIPSO_02_makefilelist.bash` doit être lancé après `main_CALIPSO_01_format.bash`

Il est à noter qu'il existe des tests sanitaires dans les scripts de lancements pour vérifier si l'étape à été complétée. Ces tests vérfient par exemples l'existence de répertoires ou de fichiers, mais ne sont pas exhaustifs. Il est préférable que l'usager s'assure lui-même que l'étape précédente a été complétée avant de passer à la suivante.

Par ailleur, à partir de l'étape 02 pour les jeux de données CALIPSO et MODIS, il est nécessaire d'avoir d'avoir au moins un fichier de GEM5 converti en format NetCDF (pour faire l'interpolation, identifier les traces de satellites passant au-dessus du domaine). Donc,
> `main_CALIPSO_02_makefilelist.bash` et `main_MODIS_02_interpolate_and_merge.bash` doivent être lancés après avoir produit au moins un fichier avec `main_GEM5_01_format.bash` (le chemin de ce fichier sera trouvé automatiquement).


&nbsp;
# Description détaillée des scripts

#### main_GEM5_01_format.bash

##### Soumission
>`./submit_GEM5_01_format.bash YYYYMMi YYYYMMf overwrite submission_type`
- **YYYYMMi**: Date de début de l'intervalle des données à traiter (année + mois).
- **YYYYMMf**: Date de fin de l'intervalle des données à traiter (année + mois).
- **overwrite** [true/false]:  
&nbsp;&nbsp;&nbsp;&nbsp; 'true': lors d'une resoumission, écrase les données déjà existantes. 
&nbsp;&nbsp;&nbsp;&nbsp; 'false': ne traite que les fichiers manquants ou corrompues. 
- **submission_type** [interactive/scheduler]: Soumettre la tâche interactivement ou en passant par l'ordonannceur.

Une tâche consiste à tariter tous les fichiers d'un répertoire mensuel.

**[IMPORTANT]** Cas spécial: Pour convertir le répertoire step0, il faut utiliser YYYYMMi=0 YYYYMMf=0. Les fichiers de ce répertoire contiennent des champs géophysiques dont on va se servir, il est donc important de ne pas oublié de le convertir lui aussi.

##### Scripts auxillaires
  - yamlmanip.py (lien vers ../yamlmanip.py)

##### Description
Effectue la converstion des fichiers fst (dm et pm contenues) vers le format fst en utilisant le module python **fstd2nc**.  

Note:  Le module python **fstd2nc** est utilisé au lieu du plus conventionnel **cdf2rpn** car ce dernier ne garde pas les coefficients de pression a et b (p=a+bLOG(ps/pref)). Ceux-ci vont éventuellemnt être nécessaires pour calculer les niveaux de pression (momentum + thermodynamic).
  
##### Références
  - Module python fstd2nc : https://pypi.org/project/fstd2nc


&nbsp;
#### main_CALIPSO_01_format.bash
##### Soumission
>`./submit_CALIPSO_01_format.bash YYYYi YYYYf overwrite submission_type`
- **YYYYi**: Date de début de l'intervalle des données à traiter (année seule).
- **YYYYf**: Date de fin de l'intervalle des données à traiter (année seule).
- **overwrite** [true/false]:  
&nbsp;&nbsp;&nbsp;&nbsp; 'true': lors d'une resoumission, écrase les données déjà existantes. 
&nbsp;&nbsp;&nbsp;&nbsp; 'false': ne traite que les fichiers manquants ou corrompues. 
- **submission_type** [interactive/scheduler]: Soumettre la tâche interactivement ou en passant par l'ordonannceur.

Une tâche correspond à traiter toutes les données d'une année.

##### Scripts auxillaires
  - yamlmanip.py (lien vers ../yamlmanip.py)
  - h4tonccf_nc4
  - aux_CALIPSO_format_attributes.py

##### Description
Effectue la conversion des fichiers hdf en NetCDF en utilisant **h4tonccf_nc4**. 

Note: Dans le fichier original, l'attribut valid_range est une chaine de caractère formé de 2 nombres séparés par trois points (...). Ce format non-standard peut créer certains bogues lors de la manipulation subséquente des fichiers NetCDF. Cet attribut est donc modifié en utilisant **aux_CALIPSO_format_attributes.py**
> Latitude:valid_range = "-90.0...90.0" ; (original)
> Latitude:valid_range = -90., 90. ;  (modifié)

##### Références
  - h4tonccf_nc4: http://hdfeos.org/software/h4cflib.php



&nbsp;
&nbsp;
- main_CALIPSO_02_makefilelist.bash
- main_MODIS_01_format.bash
- main_MODIS_02_interpolate_and_merge.bash
- main_MODIS_03_merge_MOD06_and_MYD06.bash






# CALISPO

## Description
Effectue la converstion des fichiers hdf vers Netcdf
Corrige un problème au niveau des attribut

## Liste des fichiers
  - CALIPSO\_format.bash (driver)
  - h4tonccf\_nc4 (hdf --> NetCDF)
  - calipso\_fix\_attribute\_problem.py

## Exemple de soumission:  
YYYY=2014; soumet CALIPSO\_format.bash \-args &nbsp;$YYYY \-jn CALIPSO\_format\_\${YYYY} \-t 86400


## Notes:
  1. L'attribut valid\_range est originellement donné par une chaine de caractère, formée de 2 nombres
  séparés par 3 points ... Ce format fait planter d'autres outils. On formate donc la valeur de
  valid\_range en un array (format beaucoup plus standard)
  2. Les réperoires d'entrées et de sortie sont "hardcodé" dans le script mais peut évidemment
  être édité au besoin.
  3. Si on relance le script, les anciens fichiers de sortie sont simplement écrasés.
"README.md" 58L, 2076C                                                                                                                                                                    1,6           Top































