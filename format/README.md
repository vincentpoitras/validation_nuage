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
  5. Le script python fstd2nc est utilisé au lieu du plus conventionnel cdf2rpn car ce dernier
  ne garde pas les coefficient de pression a et b (p=a+bLOG(ps/pref)). Ceux-ci sont nécessaires
  pour calculer les niveaux de pression.


## Références

  - Script python fstd2nc : https://pypi.org/project/fstd2nc
 



