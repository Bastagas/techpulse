# Auto-retry Oracle ARM — guide pas-à-pas

> Le script `auto_retry.py` interroge l'API Oracle Cloud en boucle toutes les 45 s pour essayer de créer ton instance ARM Ampere. Notification macOS quand ça passe.

**Temps setup : ~15 min** · **Ensuite le script tourne seul pendant des heures**.

---

## Pourquoi l'auto-retry ?

Oracle Cloud Free Tier ARM Ampere = ressource très demandée. "Out of host capacity" apparaît souvent parce que tous les serveurs ARM d'une région sont saturés. **Les capacities se libèrent en permanence** (instances supprimées, essais abandonnés…) mais l'attente peut être aléatoire (30 min à 24 h).

Solution : un script qui retente toutes les 45 s jusqu'à ce que ça passe. Tu peux laisser tourner en arrière-plan.

---

## Prérequis

- Compte Oracle Cloud actif ✓ (déjà fait)
- OCI SDK Python installé : `deploy/oracle/.venv/` (déjà fait par Claude)
- OCI CLI pour la config auth : on l'installe ci-dessous

---

## Étape 1 · Installer l'OCI CLI

Le plus simple sur macOS :

```bash
brew install oci-cli
```

Alternative (si brew pose problème) :

```bash
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
```

Vérifier :

```bash
oci --version
```

---

## Étape 2 · Configurer l'authentification OCI

### 2.1 Lancer le wizard

```bash
oci setup config
```

Le wizard te pose plusieurs questions. Prépare 2 onglets dans ton navigateur :
- **Onglet 1** : Oracle Cloud Console → Profil utilisateur (icône en haut à droite)
- **Onglet 2** : Oracle Cloud Console → Tenancy info

### 2.2 Répondre aux questions

| Question | Où trouver la réponse |
|---|---|
| `Enter a location for your config` | Appuie Entrée (accepte `~/.oci/config`) |
| `Enter a user OCID` | **Profil utilisateur** (coin haut-droit de la console) → copie l'OCID affiché sous ton nom |
| `Enter a tenancy OCID` | **Profil → Tenancy info** → copie l'OCID de la tenancy |
| `Enter a region` | Ta région, ex : `eu-frankfurt-1` ou `eu-marseille-1` (doit matcher celle où tu as essayé de créer l'instance) |
| `Do you want to generate a new API Signing RSA key pair?` | **Y** |
| `Enter a directory for your keys to be created` | Entrée (accepte `~/.oci`) |
| `Enter a name for your key` | Entrée (accepte `oci_api_key`) |
| `Enter a passphrase` | Entrée (laisse vide — pas de passphrase) |

À la fin, le wizard affiche le chemin de la **clé publique** :

```
Public key written to: /Users/bastagas/.oci/oci_api_key_public.pem
```

**Copie-la** :

```bash
cat ~/.oci/oci_api_key_public.pem
```

### 2.3 Uploader la clé publique sur Oracle

1. Oracle Cloud Console → **Profil utilisateur** (coin haut-droit)
2. Onglet **API Keys** → bouton **Add API Key**
3. Choisir **Paste public key**
4. Coller le contenu entier (y compris `-----BEGIN PUBLIC KEY-----` et `-----END PUBLIC KEY-----`)
5. **Add**

Oracle affiche un **fingerprint** après l'ajout. Il doit matcher celui dans `~/.oci/config`.

### 2.4 Tester l'auth

```bash
oci iam region list --output table
```

Si tu vois la liste des régions Oracle, **l'auth marche** 🎉. Sinon regarde les messages d'erreur pour corriger.

---

## Étape 3 · Récupérer les OCIDs de ton projet

Tu as besoin de 4 OCIDs pour remplir `instance.config.yaml`.

### 3.1 Compartment OCID

- Oracle Console → **Identity & Security** → **Compartments**
- Le compartment **root** = celui du tenancy (si tu n'en as pas créé d'autre)
- Copie son OCID (colonne OCID → bouton "Copy")

### 3.2 Availability Domain

- Oracle Console → **Governance** → **Limits, Quotas and Usage** OU via OCI CLI :

```bash
oci iam availability-domain list --output table
```

Format retourné : `cXzI:EU-FRANKFURT-1-AD-1`. **Copie celui complet** (avec le préfixe tenancy).

### 3.3 Subnet OCID

- Oracle Console → **Networking** → **Virtual Cloud Networks**
- Clique sur le VCN créé lors de ta première tentative (nommé `vcn-xxxxxxxx-xx-xx`)
- Onglet **Subnets** → clique sur le subnet public (celui avec Access Type = public)
- Copie l'**OCID du subnet**

### 3.4 Image OCID (Canonical Ubuntu 22.04 Minimal aarch64)

**Méthode A — via OCI CLI** (plus rapide) :

```bash
oci compute image list \
  --compartment-id <ton-compartment-ocid> \
  --operating-system "Canonical Ubuntu" \
  --operating-system-version "22.04 Minimal aarch64" \
  --sort-by TIMECREATED --sort-order DESC \
  --limit 1 \
  --query "data[0].id" --raw-output
```

Copie l'OCID retourné.

**Méthode B — via Oracle Console** (visuelle) :

- Recommence le "Create instance"
- Change image → **Canonical Ubuntu 22.04 Minimal aarch64**
- À ce stade, **NE CLIQUE PAS** "Create". Ouvre un devtools navigateur (F12) pour inspecter la requête réseau et copier l'imageId.
- OU annule et fais la méthode A à la place.

### 3.5 SSH public key

Le contenu de `~/.ssh/oracle_techpulse.key.pub` (la clé téléchargée pendant la première tentative Oracle) :

```bash
cat ~/Downloads/ssh-key-*.key.pub
```

Si tu n'as pas la clé publique mais seulement la privée, dérive-la :

```bash
ssh-keygen -y -f ~/.ssh/oracle_techpulse.key
```

---

## Étape 4 · Remplir instance.config.yaml

```bash
cd ~/Documents/MOI/Fac1/Facfac/fac1/Cours/Cours\ /Master/M2/Projet\ outils\ M2\ giles\ michel\ roger
cp deploy/oracle/instance.config.example.yaml deploy/oracle/instance.config.yaml
nano deploy/oracle/instance.config.yaml
```

Remplace tous les `xxxxxx...` par les vraies valeurs récupérées à l'étape 3. Sauvegarde.

---

## Étape 5 · Lancer le script auto-retry

```bash
deploy/oracle/.venv/bin/python deploy/oracle/auto_retry.py
```

Tu verras :

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TechPulse — Auto-retry Oracle ARM Ampere
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Config OCI chargée (région eu-frankfurt-1)
✓ Shape : VM.Standard.A1.Flex · 4 OCPU · 24 GB
✓ AD : cXzI:EU-FRANKFURT-1-AD-1
  [15:42:30] attempt 1 (0s) → Out of host capacity
  [15:43:15] attempt 2 (45s) → Out of host capacity
  [15:44:00] attempt 3 (1m30s) → Out of host capacity
  ...
```

**Laisse tourner.** Tu peux minimiser le terminal, faire autre chose.

Quand ça passe (typiquement entre 30 min et 3 h), tu vois :

```
  🎉 INSTANCE CRÉÉE ! (après 47 tentatives, 35m15s)
  ID       : ocid1.instance.oc1.eu-frankfurt-1....
  Nom      : techpulse
  État     : PROVISIONING
  Shape    : VM.Standard.A1.Flex
```

Et une **notification macOS** apparaît avec un son "Glass".

---

## Étape 6 · Après création de l'instance

1. Retour sur Oracle Cloud Console → **Compute → Instances** → attends que l'instance passe en **Running** (vert, ~2 min)
2. Copie l'**IP publique**
3. Reprends le guide principal **[ORACLE.md](ORACLE.md) à partir de l'étape 3** (connexion SSH)

---

## Tester plusieurs AD en parallèle

Si ta région a plusieurs availability domains (Frankfurt en a 3), tu peux lancer **3 scripts en parallèle**, un par AD, pour tripler tes chances.

Dans 3 terminaux différents, duplique `instance.config.yaml` :

```bash
cp deploy/oracle/instance.config.yaml deploy/oracle/instance-ad1.yaml
cp deploy/oracle/instance.config.yaml deploy/oracle/instance-ad2.yaml
cp deploy/oracle/instance.config.yaml deploy/oracle/instance-ad3.yaml
```

Édite chacun avec AD-1, AD-2, AD-3. Puis lance :

```bash
# Terminal 1
CONFIG=deploy/oracle/instance-ad1.yaml deploy/oracle/.venv/bin/python deploy/oracle/auto_retry.py

# Terminal 2 (nouvel onglet)
CONFIG=deploy/oracle/instance-ad2.yaml deploy/oracle/.venv/bin/python deploy/oracle/auto_retry.py

# Terminal 3
CONFIG=deploy/oracle/instance-ad3.yaml deploy/oracle/.venv/bin/python deploy/oracle/auto_retry.py
```

*Note : le script lit `instance.config.yaml` par défaut — pour utiliser un autre chemin il faut patcher `CONFIG_FILE` dans le script. Pour l'instant, duplique + renomme + relance.*

---

## Troubleshooting

| Erreur | Cause | Fix |
|---|---|---|
| `~/.oci/config introuvable` | Étape 2 pas faite | `oci setup config` |
| HTTP 401 / 403 | Clé API pas uploadée | Étape 2.3 |
| HTTP 400 + "quota exceeded" | Tu as déjà 4 OCPU ou 24 GB en cours | Supprime les instances précédentes |
| HTTP 400 + "invalid parameter" | Un OCID est wrong | Vérifie `instance.config.yaml` |
| `oci.exceptions.ConfigFileNotFound` | Fichier config corrompu | Supprime `~/.oci/config` et recommence étape 2 |

---

## Arrêt du script

`Ctrl+C` dans le terminal. Le script affiche un récap (tentatives, durée totale, dernière erreur).
