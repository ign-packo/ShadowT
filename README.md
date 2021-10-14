# Script de détection d'ombre par seuillage sur histogramme

## Description du script
Ce script utilise différentes méthodes de seuillage d'histogramme dans le but de détecter l'ombre d'images aériennes 8 ou 16 bits. L'algorithme utilisé a besoin d'au moins les 3 bandes couleurs RVB (rouge, verte et bleue) dans le visible, une bande en proche-infrarouge (PIR) de plus serait encore mieux.  

## Algorithme

`shadow_mask.py` combine les différentes méthodes de détection d'ombre pour construire un processus robuste. L'idée principale est d'appliquer un seuillage global sur un groupe d'images qui présente les différentes scènes de payage d'un chantier. Le seuil déterminé peut être appliqué sur l'ensemble d'images aérienne du même chantier.

Inspiré par l'article [Adeline13], dans le cas d'images RVB, la méthode de couleur invariante [Tsai06] est appliquée. Il s'agit d'abord de convertir l'espace couleur RVB en HSI (Hue Saturation Intensity) puis d'appliquer le seuillage d'histogramme [Otsu79] sur le ratio entre H et I. Dans le cas d'images RVB-PIR, la méthode [Tsai06] est conservée, avec une autre option: la méthode [Nagao79]. Il s'agit d'un seuillage d'histogramme de "première vallée" sur la luminosité pondérée d'image. En fin, les seuillages d'histogramme sur les cartes de  NDWI (Normalized Difference Water Index) et NDVI (Normalized difference Vegetaion Index) permettent de détecter des surfaces d'eau et de végétation qui risquent d'être confondues avec l'ombre.

## Références

* [Adeline, K.R.M., Chen, M., Briottet, X., Pang, S.K., Paparoditis, N.,  2013. Shadow detection in very high spatial resolution aerial images: A  comparative study. ISPRS Journal of Photogrammetry and Remote Sensing  80, 21–38.](https://www.sciencedirect.com/science/article/pii/S0924271613000415)
* [Otsu, N., 1979. A threshold selection method from gray-level histograms. IEEE transactions on systems, man, and cybernetics 9, 62–66.](https://ieeexplore.ieee.org/document/4310076)
* [Nagao, M., Matsuyama, T., Ikeda, Y., 1979. Region extraction and shape  analysis in aerial photographs. Computer Graphics and Image Processing  10, 195–223.](https://www.sciencedirect.com/science/article/pii/0146664X79900017)
* [Tsai, V.J.D., 2006. A comparative study on shadow compensation of color  aerial images in invariant color models. IEEE Transactions on Geoscience and Remote Sensing 44, 1661–1671.](https://ieeexplore.ieee.org/document/1634729)

## Utilisation du script

Les codes de fonctionnement sont dans `shadow_mask.py` , pour faciliter l'utilisation, je vous propose 2 scripts comme exemples: `shadow_mask_rgb.py` et `shadow_mask_rgb_nir.py`.

Pour utiliser le script, désigner un répertoire d'entrée contenant des images ainsi qu'un répertoire de sortie.  A défaut de répertoire de sortie, le script ne fait que de seuillage global.

`shadow_mask_rgb.py`: le script pour traiter les images RVB

```  
python .\shadow_mask_rgb.py input=\InputImage ext=.jp2 bits=8 jump=2 sub=10 hsteq=False output=\OutputResults 
```
- `input`= nom du répertoire d'entrée.
- `ext`=  extension des images dans le répertoire d'entrée, défaut=.*
- `bits`= profondeur de couleur,  8 ou 16, défaut=8
- `jump`= intervalle pour la création de list d'image pour le seuillage global. Le seuillage global n'a pas besoin de lire toutes les images, donner un intervalle>1 permet de gagner du temps. défaut=1
- `sub`= un autre intervalle pour le seuillage global. Le seuillage global n'a pas besoin de lire tous les pixels d'une image, donner un intervalle>1 permet de gagner du temps. défaut=10 
- `hsteq`= option pour le seuillage global. Certaines images en 16bits brute ont une plage de dynamique restreinte, `hsteq=True` applique une égalisation histogramme sur  la luminosité `I` afin d'améliorer le résultat de seuillage d'histogramme. défaut=False
- `output`= nom du répertoire de sortie. A défaut de répertoire de sortie, le script ne fait que de seuillage global.



`shadow_mask_rgb_nir.py`: le script pour traiter les images RVB + PIR
```  
python .\shadow_mask_rgb_nir.py input=\InputImage threshold_input=\ShresholdInputImage ext_rgb=-RVB.jp2 ext_nir=-PIR.jp2 bits=8 jump=2 sub=10 hsteq=False method=nagao output=\OutputResults 
```
- `input`= nom du répertoire d'entrée. Les images RVB sont stockés dans le sous-répertoire `\RVB` et les images PIR sont stockés dans le sous-répertoire `\PIR`
- `threshold_input`=nom du répertoire d'entrée pour le seuillage global. Les images RVB sont stockés dans le sous-répertoire `\RVB` et les images PIR sont stockés dans le sous-répertoire `\PIR` . A défaut, `threshold_input=input` 
- `ext_rgb` et `ext_nir` =  extension des images RVB et PIR, **<font color=#FF0000>Attention</font>** les noms d'image RVB et PIR doivent être identiques sauf leur extension, par exemple `nom-RVB.jp2`  dans le répertoire `\InputImage\RVB\` et `nom-PIR.jp2`  dans le répertoire `\InputImage\PIR\`. Cela permet au programme de repérer le couple d'images RVB/PIR.  défaut=.*
- `bits`= profondeur de couleur,  8 ou 16, défaut=8
- `jump`= intervalle pour la création de list d'image pour le seuillage global. Le seuillage global n'a pas besoin de lire toutes les images, donner un intervalle>1 permet de gagner du temps. Si `threshold_input` est donné, `jump` est forcé à 1. défaut=1
- `sub`= un autre intervalle pour le seuillage global. Le seuillage global n'a pas besoin de lire tous les pixels d'une image, donner un intervalle>1 permet de gagner du temps. default=10 
- `hsteq`= option pour le seuillage global. Certaines images en 16bits brute ont une plage de dynamique restreinte, `hsteq=True` applique une égalisation histogramme sur  la luminosité `I` afin d'améliorer le résultat de seuillage d'histogramme. défaut=False
- `method`= option pour sélectionner la méthode de seuillage global. Il dispose les options `nagao` et `tsai`, défaut=nagao
- `output`= nom du répertoire de sortie. A défaut de répertoire de sortie, le script ne fait que de seuillage global.


## Résultats
Dans le répertoire de sortie, vous trouverez: 
- masked_nom.jpg:  Image de départ en 8 bits (quelque soit sa profondeur de couleur d'origine) et les pixels d'ombre sont masqués en rouge. Le nom d'image `nom` de départ est conservé.
- mask_nom.jpg:  Masque d'ombre binaire obtenu, les pixels d'ombre ont la valeur 0 et les restes ont la valeur 255.

## Discussion

Le seuillage global avec une liste d'images construite par jump n'est peut être pas la méthode la plus efficace, surtout s'il existe de scènes seulement présentées dans 1 ou 2 images. Dans le cas de seuillage global RVB+PIR, il faut penser à construire une liste d'images sélectionnées par l'utilisateur pour le seuillage global.

# Créateur 
Manchun Lei - https://www.umr-lastig.fr/manchun-lei/
