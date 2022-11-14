# GEM5

## Description
Effectue la converstion des fichiers fst (la simulation faite sur narval) vers le format fst en utilisant le script python fstd2nc

## Liste des fichiers
  - GEM5\_format.bash
  
## Exemple de soumission:  
YYYYMM=201401; soumet GEM\_format.bash \-args &nbsp;$YYYYMM \-jn GEM5\_format\_\${YYYYMM} \-t 43200


## Notes:
  1. Temps de téléchargement (1 mois): environ 8 heures (pour le domaine/variables actuelles)
  2. Pour formater step0 (requis pour créer le masque terre-mer), il suffit 
  de mettre YYYYMM=step0
  3. Les réperoires d'entrées et de sortie est "hardcodé" dans le script mais peut évidemment
  être édité au besoin.
  4. Si on relance le script, les anciens fichiers de sortie sont simplement écrasés. 
  5. Le module python fstd2nc est utilisé au lieu du plus conventionnel cdf2rpn car ce dernier
  ne garde pas les coefficient de pression a et b (p=a+bLOG(ps/pref)). Ceux-ci vont éventuellemnt
  être  nécessaires pour calculer les niveaux de pression (momentum + thermodynamic)


## Références

  - Module python fstd2nc : https://pypi.org/project/fstd2nc
 


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
  1. L'attribut valid\_range est originellement donné par une chaine de caractère, formé de 2 nombres 
  séparés par 3 points ... Ce format fait planter d'autres outils. On formate donc la valeur de
  valid\_range en un array (format beaucoup plus standard)
  2. Les réperoires d'entrées et de sortie est "hardcodé" dans le script mais peut évidemment
  être édité au besoin.
  3. Si on relance le script, les anciens fichiers de sortie sont simplement écrasés.

## Références

  - h4tonccf\_nc4: http://hdfeos.org/software/h4cflib.php


