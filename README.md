# SPY

SPY est un outil pour vos recherches durant des CTFS ou de l'investigation qui vous renvoie tous les profils existant avec le pseudo que vous avez mis.

## Installation

1. Cloner le dépôt.
2. Installer les dépendances :
   ```sh
   pip install -r requirements.txt
   ```

## Utilisation

```sh
python username_search.py <pseudo> 
```

Le script vérifie une liste de sites connus et génère un PDF contenant les URLs où le pseudo existe. Les sites qui renvoient une erreur 404 sont ignorés.

Le programme lit désormais les modèles d'URL depuis un fichier externe (par défaut `sites.txt`) afin de faciliter l'ajout de dizaines de sites.

* Créez ou éditez `site.txt` avec un gabarit par ligne, par exemple `https://github.com/{username}`.
* Lancez le script en passant un autre fichier si nécessaire : `python username_search.py <pseudo> -s autre_liste.txt`.

Vous pouvez toujours utiliser la liste intégrée si le fichier n'est pas trouvé, mais il est plus pratique de maintenir
un fichier séparé contenant "tout plein de sites".
