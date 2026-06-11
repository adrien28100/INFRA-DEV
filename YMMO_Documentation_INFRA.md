# Documentation Technique INFRA — Projet YMMO
**Groupe immobilier YMMO — Architecture réseau & sécurité**
*Bachelor 2 Informatique — UF INFRA & DEV*

---

## Table des matières

1. [Schéma d'architecture réseau](#1-schéma-darchitecture-réseau)
2. [Plan d'adressage IP](#2-plan-dadressage-ip)
3. [Politique de sécurité](#3-politique-de-sécurité)
4. [Plan de gestion des droits d'accès](#4-plan-de-gestion-des-droits-daccès)
5. [Guide de configuration des serveurs](#5-guide-de-configuration-des-serveurs)
6. [Plan de sauvegarde et de supervision](#6-plan-de-sauvegarde-et-de-supervision)
7. [Proposition d'une solution Cloud](#7-proposition-dune-solution-cloud)
8. [Guide de déploiement](#8-guide-de-déploiement)
9. [Liste du matériel et budgétisation](#9-liste-du-matériel-et-budgétisation)

---

## 1. Schéma d'architecture réseau

### Vue d'ensemble

```
                          INTERNET
                             |
                    ┌────────┴────────┐
                    │   Pare-feu HQ   │  (pfSense / FortiGate)
                    │  82.x.x.x (WAN) │
                    └────────┬────────┘
                             |
                    ┌────────┴────────┐
                    │   Routeur HQ    │  192.168.1.254
                    └────────┬────────┘
                             |
              ┌──────────────┼──────────────┐
              |              |              |
       ┌──────┴──────┐  ┌────┴────┐  ┌─────┴──────┐
       │  VLAN 10    │  │ VLAN 20 │  │  VLAN 30   │
       │  SERVEURS   │  │   DMZ   │  │ POSTES HQ  │
       │192.168.1.0/25│  │10.0.0.0/28│ │192.168.2.0/25│
       └──────┬──────┘  └────┬────┘  └─────┬──────┘
              |              |              |
      ┌───────┼──────┐    ┌──┴──┐    30 Postes Windows
      |       |      |    |Web  |    192.168.2.1–30
    [DC/AD] [FS] [BACKUP] [Serv]    1 Imprimante 192.168.2.100
    .1      .4    .7      10.0.0.1

                    ║  VPN IPSec Site-à-Site  ║
          ╔═════════╩═════════════════════════╩═════════╗
          ║     Concentrateur VPN HQ : 192.168.1.200    ║
          ╚══╤══════╤══════╤═════╤══════╤═══════════╤══╝
             |      |      |     |      |           |
          AGE-01 AGE-02 AGE-03 AGE-04 AGE-05  ... AGE-12
          Paris  Lyon  Marse  Tlse  Nice      Grenoble
       10.1.1.0 10.1.2.0 ...                  10.1.12.0
          /24     /24                              /24

  ┌─── Structure type d'une agence ────────────────────────┐
  │  Routeur agence (10.1.X.254)                           │
  │        |                                               │
  │  Commutateur 8 ports                                   │
  │    ├── 5 postes commerciaux  (10.1.X.1 – 10.1.X.5)   │
  │    ├── 1 imprimante réseau   (10.1.X.10)               │
  │    └── Tunnel VPN → HQ                                 │
  └────────────────────────────────────────────────────────┘
```

### Segmentation réseau (VLANs HQ)

| VLAN | Nom | Réseau | Utilisation |
|------|-----|--------|-------------|
| 10 | SERVEURS | 192.168.1.0/25 | DC, DNS, DHCP, FS, Backup |
| 20 | DMZ | 10.0.0.0/28 | Serveur Web, Reverse Proxy |
| 30 | POSTES_HQ | 192.168.2.0/25 | Postes utilisateurs siège |
| 40 | GESTION | 192.168.3.0/29 | Administration réseau |
| 50 | VPN | 172.16.0.0/24 | Tunnels VPN agences |

---

## 2. Plan d'adressage IP

### Siège social — Aix-en-Provence

#### VLAN 10 — Serveurs (192.168.1.0/25 — masque /25 = 255.255.255.128)

| Hôte | Adresse IP | Rôle |
|------|------------|------|
| Passerelle | 192.168.1.126 | Routeur (interface VLAN10) |
| SRV-DC01 | 192.168.1.1 | Contrôleur de domaine principal (AD DS) |
| SRV-DC02 | 192.168.1.2 | Contrôleur de domaine secondaire |
| SRV-DNS | 192.168.1.1 | DNS primaire (colocalisé sur DC01) |
| SRV-DHCP | 192.168.1.1 | DHCP (colocalisé sur DC01) |
| SRV-FS01 | 192.168.1.4 | Serveur de fichiers / DFS |
| SRV-BACKUP | 192.168.1.7 | Serveur de sauvegarde |
| SRV-DB01 | 192.168.1.10 | Serveur base de données (SQL Server) |
| SRV-WSUS | 192.168.1.11 | Mises à jour Windows (WSUS) |

#### VLAN 20 — DMZ (10.0.0.0/28 — masque /28 = 255.255.255.240)

| Hôte | Adresse IP | Rôle |
|------|------------|------|
| Passerelle | 10.0.0.14 | Pare-feu (interface DMZ) |
| SRV-WEB01 | 10.0.0.1 | Serveur Web (IIS / Nginx) |
| SRV-PROXY | 10.0.0.2 | Reverse Proxy (Nginx) |

#### VLAN 30 — Postes utilisateurs HQ (192.168.2.0/25)

| Plage | Attribution | Commentaire |
|-------|------------|-------------|
| 192.168.2.1 – 192.168.2.30 | Postes de travail | Assignés par DHCP |
| 192.168.2.100 | Imprimante HQ | IP fixe |
| 192.168.2.126 | Passerelle | Routeur |

#### VLAN 40 — Administration réseau (192.168.3.0/29)

| Hôte | Adresse IP |
|------|------------|
| Pare-feu (int.) | 192.168.3.1 |
| Switch manageable | 192.168.3.2 |
| Routeur HQ | 192.168.3.3 |

#### VLAN 50 — VPN (172.16.0.0/24)

| Hôte | Adresse IP |
|------|------------|
| Concentrateur VPN HQ | 172.16.0.1 |
| Endpoint agence 01 | 172.16.0.2 |
| Endpoint agence 02 | 172.16.0.3 |
| … | … |
| Endpoint agence 12 | 172.16.0.13 |

---

### Agences — Plan d'adressage

Chaque agence utilise le schéma **10.1.X.0/24** où X = numéro d'agence (1–12).

| Agence | Ville | Réseau | Passerelle | Postes | Imprimante |
|--------|-------|--------|------------|--------|-----------|
| AGE-01 | Paris | 10.1.1.0/24 | 10.1.1.254 | .1–.5 (DHCP) | 10.1.1.10 |
| AGE-02 | Lyon | 10.1.2.0/24 | 10.1.2.254 | .1–.5 (DHCP) | 10.1.2.10 |
| AGE-03 | Marseille | 10.1.3.0/24 | 10.1.3.254 | .1–.5 (DHCP) | 10.1.3.10 |
| AGE-04 | Toulouse | 10.1.4.0/24 | 10.1.4.254 | .1–.5 (DHCP) | 10.1.4.10 |
| AGE-05 | Nice | 10.1.5.0/24 | 10.1.5.254 | .1–.5 (DHCP) | 10.1.5.10 |
| AGE-06 | Nantes | 10.1.6.0/24 | 10.1.6.254 | .1–.5 (DHCP) | 10.1.6.10 |
| AGE-07 | Strasbourg | 10.1.7.0/24 | 10.1.7.254 | .1–.5 (DHCP) | 10.1.7.10 |
| AGE-08 | Montpellier | 10.1.8.0/24 | 10.1.8.254 | .1–.5 (DHCP) | 10.1.8.10 |
| AGE-09 | Bordeaux | 10.1.9.0/24 | 10.1.9.254 | .1–.5 (DHCP) | 10.1.9.10 |
| AGE-10 | Lille | 10.1.10.0/24 | 10.1.10.254 | .1–.5 (DHCP) | 10.1.10.10 |
| AGE-11 | Rennes | 10.1.11.0/24 | 10.1.11.254 | .1–.5 (DHCP) | 10.1.11.10 |
| AGE-12 | Grenoble | 10.1.12.0/24 | 10.1.12.254 | .1–.5 (DHCP) | 10.1.12.10 |

> **DHCP** : distribué depuis SRV-DC01 au siège via relais DHCP (ip helper-address) à travers le tunnel VPN.

---

## 3. Politique de sécurité

### 3.1 Politique de pare-feu (règles types)

#### Règles entrantes (WAN → LAN)

| Priorité | Source | Destination | Port/Proto | Action | Description |
|----------|--------|-------------|------------|--------|-------------|
| 1 | Any | 10.0.0.1 | TCP 80, 443 | ALLOW | Accès web public |
| 2 | VPN peers | 172.16.0.0/24 | UDP 500, 4500 | ALLOW | Négociation IPSec |
| 3 | Any | Any | Any | DENY | Blocage par défaut |

#### Règles inter-VLANs (HQ)

| Source | Destination | Port/Proto | Action | Justification |
|--------|-------------|------------|--------|---------------|
| VLAN30 (postes) | VLAN10 (serveurs) | TCP 445, 389, 636 | ALLOW | SMB, LDAP/S |
| VLAN30 | VLAN10 | TCP 3389 | DENY | Bloquer RDP utilisateurs |
| VLAN40 (admin) | Tous VLANs | Any | ALLOW | Administration SI |
| VLAN20 (DMZ) | VLAN10 | TCP 1433 | ALLOW | Web → DB |
| VLAN10 | VLAN20 | Any | DENY | Isolation DMZ |

#### Règles VPN → HQ

| Source | Destination | Port/Proto | Action |
|--------|-------------|------------|--------|
| 10.1.X.0/24 | 192.168.1.0/25 | TCP 445 | ALLOW (partage fichiers) |
| 10.1.X.0/24 | 192.168.1.1 | TCP/UDP 53 | ALLOW (DNS) |
| 10.1.X.0/24 | 192.168.1.0/25 | TCP 389, 636 | ALLOW (AD) |
| 10.1.X.0/24 | 10.0.0.1 | TCP 443 | ALLOW (app web interne) |
| 10.1.X.0/24 | Any | Any | DENY | Défaut |

### 3.2 Politique VPN IPSec Site-à-Site

| Paramètre | Valeur |
|-----------|--------|
| Protocole | IKEv2 |
| Chiffrement Phase 1 | AES-256 |
| Intégrité Phase 1 | SHA-256 |
| Groupe DH | Group 14 (2048 bits) |
| Durée de vie Phase 1 | 86 400 s (24h) |
| Chiffrement Phase 2 | AES-256 |
| Intégrité Phase 2 | SHA-256 |
| Durée de vie Phase 2 | 3 600 s (1h) |
| Authentification | Certificats PKI (ou Pre-Shared Key) |
| Mode | Tunnel |
| PFS | Activé (Group 14) |

### 3.3 Politique de mots de passe (GPO)

| Paramètre | Valeur |
|-----------|--------|
| Longueur minimale | 12 caractères |
| Complexité | Activée (Maj + Min + Chiffre + Spécial) |
| Historique | 10 derniers mots de passe |
| Âge maximum | 90 jours |
| Âge minimum | 1 jour |
| Verrouillage | 5 tentatives → verrouillage 15 min |
| MFA | Activé pour les comptes admin (Azure AD MFA) |

### 3.4 Politique de mise à jour

- **WSUS** (SRV-WSUS) déployé au siège
- Déploiement automatique des mises à jour critiques sous 72h
- Fenêtre de maintenance : dimanche 02h00 – 05h00
- Les agences reçoivent les mises à jour via VPN depuis WSUS

### 3.5 Politique antivirus / EDR

- Solution : **Windows Defender Antivirus** (intégré) + **Microsoft Defender for Endpoint** (EDR)
- Analyse complète hebdomadaire (samedi 03h00)
- Rapports centralisés via Microsoft 365 Defender ou SIEM local
- Isolation automatique des postes compromis

### 3.6 Chiffrement

| Composant | Méthode |
|-----------|---------|
| Disques serveurs | BitLocker (TPM 2.0) |
| Postes de travail | BitLocker To Go |
| Sauvegardes | Chiffrées AES-256 |
| Flux web | TLS 1.2 minimum (1.3 recommandé) |
| Échanges AD | LDAPS (port 636) |

---

## 4. Plan de gestion des droits d'accès

### 4.1 Structure Active Directory

```
Domaine : ymmo.local
│
├── OU=Siege
│   ├── OU=Direction
│   ├── OU=Informatique
│   ├── OU=Comptabilite
│   └── OU=Ressources_Humaines
│
├── OU=Agences
│   ├── OU=AGE-Paris
│   ├── OU=AGE-Lyon
│   ├── OU=AGE-Marseille
│   ├── … (12 agences)
│   └── OU=AGE-Grenoble
│
├── OU=Serveurs
│   ├── OU=Serveurs_HQ
│   └── OU=Serveurs_DMZ
│
└── OU=GroupesPolitiques
```

### 4.2 Groupes de sécurité

| Groupe AD | Membres | Description |
|-----------|---------|-------------|
| GRP_DirecteurGeneral | DG | Accès total applicatif |
| GRP_DirecteursAgence | Directeurs des 12 agences | Gestion agence + accès reporting |
| GRP_Commerciaux | Agents commerciaux (5×12=60) | Accès app immobilière en lecture/écriture |
| GRP_Comptabilite | Équipe compta siège | Accès ERP, fichiers finances |
| GRP_AdminSI | Équipe IT | Accès admin complet (postes + serveurs) |
| GRP_VPN_Agences | Tous comptes agences | Autorisation tunnel VPN |

### 4.3 Matrice des droits d'accès

| Ressource | Dir. Général | Dir. Agence | Commercial | Comptable | Admin SI |
|-----------|:---:|:---:|:---:|:---:|:---:|
| **Application web YMMO** | RW | RW (agence) | RW (agence) | R | RW |
| **Serveur de fichiers — Partagé** | RW | RW | R | R | RW |
| **Serveur de fichiers — Agence** | R | RW | RW | — | RW |
| **Serveur de fichiers — Direction** | RW | R | — | — | RW |
| **Serveur de fichiers — Compta** | R | — | — | RW | RW |
| **Active Directory (admin)** | — | — | — | — | RW |
| **Console serveurs / RDP** | — | — | — | — | RW |
| **VPN accès siège** | Oui | Oui | Oui | Oui | Oui |
| **WSUS / console SCCM** | — | — | — | — | RW |
| **Rapports statistiques** | RW | R (agence) | — | R | RW |
| **Imprimante** | Oui | Oui | Oui | Oui | Oui |

*R = Lecture seule | RW = Lecture/Écriture | — = Accès refusé*

### 4.4 GPO (Group Policy Objects)

| Nom GPO | OU cible | Paramètres principaux |
|---------|---------|----------------------|
| GPO_PasswordPolicy | Domaine entier | Politique mdp (voir §3.3) |
| GPO_LockScreen | Domaine entier | Verrouillage après 10 min |
| GPO_WallpaperYMMO | Domaine entier | Fond d'écran entreprise |
| GPO_FirewallPostes | Postes (tous OU) | Activer Windows Firewall, bloquer RDP entrant |
| GPO_NoUSB | Commerciaux | Désactiver stockage USB amovible |
| GPO_DriveMapping_Siege | OU=Siege | Montage \\SRV-FS01\Commun |
| GPO_DriveMapping_Agence | OU=Agences | Montage \\SRV-FS01\Agences\%AGE% |
| GPO_WSUS | Tous | Pointer vers SRV-WSUS |
| GPO_AdminLocal | OU=Informatique | Autoriser outils admin |

### 4.5 Modèle de moindre privilège

- Chaque utilisateur dispose **uniquement** des droits nécessaires à sa fonction
- Les comptes administrateurs IT ont un compte **séparé** pour les tâches d'administration (compte user normal + compte `prenom.nom.adm`)
- Revue des droits trimestrielle (audit des membres de groupes sensibles)
- Suppression immédiate des comptes en cas de départ (procédure RH → IT)

---

## 5. Guide de configuration des serveurs

### 5.1 Environnement

| Paramètre | Valeur |
|-----------|--------|
| OS serveurs | Windows Server 2022 Standard / Datacenter |
| Domaine | ymmo.local |
| Niveau fonctionnel AD | Windows Server 2022 |
| DNS interne | SRV-DC01 (192.168.1.1) |
| NTP | SRV-DC01 → time.windows.com |

---

### 5.2 SRV-DC01 — Contrôleur de domaine principal

**Étape 1 — Installation des rôles**
```powershell
# Installer AD DS, DNS, DHCP
Install-WindowsFeature -Name AD-Domain-Services, DNS, DHCP `
    -IncludeManagementTools

# Promouvoir en contrôleur de domaine
Install-ADDSForest `
    -DomainName "ymmo.local" `
    -DomainNetbiosName "YMMO" `
    -ForestMode "WinThreshold" `
    -DomainMode "WinThreshold" `
    -InstallDns:$true `
    -Force:$true
```

**Étape 2 — Configuration DHCP**
```powershell
# Créer l'étendue DHCP pour le siège (VLAN30)
Add-DhcpServerv4Scope `
    -Name "Postes_Siege" `
    -StartRange 192.168.2.1 `
    -EndRange 192.168.2.90 `
    -SubnetMask 255.255.255.128 `
    -LeaseDuration 8.00:00:00

Set-DhcpServerv4OptionValue -ScopeId 192.168.2.0 `
    -Router 192.168.2.126 `
    -DnsServer 192.168.1.1 `
    -DnsDomain "ymmo.local"

# Réservations IP pour les imprimantes
Add-DhcpServerv4Reservation `
    -ScopeId 192.168.2.0 `
    -IPAddress 192.168.2.100 `
    -ClientId "AA-BB-CC-DD-EE-FF" `
    -Description "Imprimante HQ"

# Étendues DHCP pour chaque agence (relai DHCP requis sur les routeurs agences)
# Exemple agence 01
Add-DhcpServerv4Scope `
    -Name "AGE-01_Paris" `
    -StartRange 10.1.1.1 `
    -EndRange 10.1.1.50 `
    -SubnetMask 255.255.255.0 `
    -LeaseDuration 8.00:00:00
```

**Étape 3 — Création de la structure OU**
```powershell
# Créer les UO principales
New-ADOrganizationalUnit -Name "Siege" -Path "DC=ymmo,DC=local"
New-ADOrganizationalUnit -Name "Agences" -Path "DC=ymmo,DC=local"
New-ADOrganizationalUnit -Name "Serveurs" -Path "DC=ymmo,DC=local"

# Sous-UO du siège
foreach ($dept in @("Direction","Informatique","Comptabilite","RH")) {
    New-ADOrganizationalUnit -Name $dept -Path "OU=Siege,DC=ymmo,DC=local"
}

# Sous-UO pour chaque agence
$agences = @("AGE-Paris","AGE-Lyon","AGE-Marseille","AGE-Toulouse",
             "AGE-Nice","AGE-Nantes","AGE-Strasbourg","AGE-Montpellier",
             "AGE-Bordeaux","AGE-Lille","AGE-Rennes","AGE-Grenoble")
foreach ($age in $agences) {
    New-ADOrganizationalUnit -Name $age -Path "OU=Agences,DC=ymmo,DC=local"
}
```

**Étape 4 — Groupes de sécurité**
```powershell
New-ADGroup -Name "GRP_AdminSI"         -GroupScope Global -Path "OU=Informatique,OU=Siege,DC=ymmo,DC=local"
New-ADGroup -Name "GRP_DirecteurGeneral" -GroupScope Global -Path "OU=Direction,OU=Siege,DC=ymmo,DC=local"
New-ADGroup -Name "GRP_Commerciaux"     -GroupScope Global -Path "OU=Agences,DC=ymmo,DC=local"
New-ADGroup -Name "GRP_DirecteursAgence"-GroupScope Global -Path "OU=Agences,DC=ymmo,DC=local"
New-ADGroup -Name "GRP_Comptabilite"    -GroupScope Global -Path "OU=Comptabilite,OU=Siege,DC=ymmo,DC=local"
New-ADGroup -Name "GRP_VPN_Agences"     -GroupScope Global -Path "OU=Agences,DC=ymmo,DC=local"
```

---

### 5.3 SRV-DC02 — Contrôleur de domaine secondaire

```powershell
# Sur DC02 — rejoindre le domaine existant
Install-WindowsFeature -Name AD-Domain-Services, DNS -IncludeManagementTools

Install-ADDSDomainController `
    -DomainName "ymmo.local" `
    -InstallDns:$true `
    -Credential (Get-Credential "YMMO\Administrator") `
    -Force:$true
```

---

### 5.4 SRV-FS01 — Serveur de fichiers (DFS)

```powershell
# Installer les rôles FS et DFS
Install-WindowsFeature -Name FS-FileServer, FS-DFS-Namespace, FS-DFS-Replication `
    -IncludeManagementTools

# Créer les dossiers partagés
$shares = @{
    "Commun"    = "D:\Partages\Commun"
    "Direction" = "D:\Partages\Direction"
    "Comptabilite" = "D:\Partages\Comptabilite"
}
foreach ($s in $shares.GetEnumerator()) {
    New-Item -ItemType Directory -Path $s.Value -Force
    New-SmbShare -Name $s.Key -Path $s.Value -FullAccess "YMMO\GRP_AdminSI"
}

# Partage par agence
foreach ($i in 1..12) {
    $path = "D:\Partages\Agences\AGE-$('{0:D2}' -f $i)"
    New-Item -ItemType Directory -Path $path -Force
    New-SmbShare -Name "AGE-$('{0:D2}' -f $i)" -Path $path
}
```

---

### 5.5 SRV-WEB01 — Serveur Web (DMZ)

```powershell
# Installer IIS avec les modules nécessaires
Install-WindowsFeature -Name Web-Server, Web-Asp-Net45, Web-Mgmt-Console `
    -IncludeManagementTools

# Ou utilisation de Nginx sous Windows / Linux (recommandé pour la prod)
# Voir guide déploiement §8
```

**Configuration HTTPS (TLS 1.3)**
```powershell
# Désactiver TLS 1.0 et 1.1
$regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols"
foreach ($proto in @("TLS 1.0","TLS 1.1","SSL 2.0","SSL 3.0")) {
    New-Item -Path "$regPath\$proto\Server" -Force | Out-Null
    Set-ItemProperty -Path "$regPath\$proto\Server" -Name "Enabled" -Value 0
}
```

---

### 5.6 SRV-DB01 — Serveur base de données

- **SGBD** : Microsoft SQL Server 2022 Express/Standard
- Instance : `YMMO-DB`
- Port : 1433 (accessible uniquement depuis VLAN 10 et DMZ)
- Authentification : Windows Authentication (intégration AD)
- Sauvegarde : SQL Server Agent — backup complet chaque nuit à 02h00

```sql
-- Créer la base de données applicative
CREATE DATABASE ymmo_db
    COLLATE French_CI_AS;
GO

-- Compte SQL pour l'application web
CREATE LOGIN ymmo_app WITH PASSWORD = 'P@ssw0rdY##o2024!';
CREATE USER ymmo_app FOR LOGIN ymmo_app;
ALTER ROLE db_datareader ADD MEMBER ymmo_app;
ALTER ROLE db_datawriter ADD MEMBER ymmo_app;
GO
```

---

## 6. Plan de sauvegarde et de supervision

### 6.1 Stratégie de sauvegarde — Règle 3-2-1

```
Règle 3-2-1 :
  3 copies des données
  ├── 2 supports différents (SRV-BACKUP local + NAS)
  └── 1 copie hors site (Azure Backup / offsite NAS)
```

### 6.2 Planning des sauvegardes

| Type | Fréquence | Heure | Rétention | Outil |
|------|-----------|-------|-----------|-------|
| Sauvegarde complète | Hebdomadaire (dim) | 01h00 | 4 semaines | Windows Server Backup |
| Sauvegarde incrémentale | Quotidienne (lun-sam) | 02h00 | 7 jours | Windows Server Backup |
| Snapshot VM | Quotidien | 03h00 | 7 jours | Hyper-V / VMware |
| Sauvegarde SQL | Quotidienne | 02h30 | 14 jours | SQL Server Agent |
| Sauvegarde GPO/AD | Hebdomadaire (dim) | 01h30 | 4 semaines | ntdsutil / PowerShell |
| Réplication hors site | Quotidienne | 04h00 | 30 jours | Azure Backup |

### 6.3 Script de sauvegarde AD (PowerShell)

```powershell
# Sauvegarde de l'état du système AD
$backupPath = "\\SRV-BACKUP\Backups\AD\$(Get-Date -Format 'yyyyMMdd')"
New-Item -ItemType Directory -Path $backupPath -Force
wbadmin start systemstatebackup -backupTarget:$backupPath -quiet

# Export GPO
$gpoPath = "\\SRV-BACKUP\Backups\GPO\$(Get-Date -Format 'yyyyMMdd')"
New-Item -ItemType Directory -Path $gpoPath -Force
Backup-GPO -All -Path $gpoPath
```

### 6.4 Plan de supervision (monitoring)

**Outil recommandé : Zabbix 6 LTS** (open-source, gratuit)
Alternative commerciale : PRTG Network Monitor

#### Hôtes surveillés

| Hôte | Métriques surveillées | Alerte si |
|------|----------------------|-----------|
| SRV-DC01/02 | CPU, RAM, disque, services AD/DNS/DHCP | CPU > 85% / Disque > 90% / Service down |
| SRV-FS01 | Espace disque, partages SMB, débit | Disque > 85% |
| SRV-DB01 | Connexions SQL, transactions/s, taille DB | Connexions > 100 / Disque > 80% |
| SRV-WEB01 | HTTP 200/500 ratio, temps de réponse | Temps > 2s / Erreurs 5xx > 1% |
| Routeur HQ | Bande passante, latence, BGP/VPN | Perte paquets > 2% |
| Tunnels VPN (×12) | État tunnel IPSec, latence agence | Tunnel DOWN → alerte critique |
| Tous postes | Connexion domaine, antivirus à jour | Antivirus > 7 jours |

#### Niveaux d'alerte

| Niveau | Couleur | Action |
|--------|---------|--------|
| Information | Bleu | Log uniquement |
| Avertissement | Orange | Email à l'équipe IT |
| Critique | Rouge | SMS + Email + appel astreinte |
| Catastrophe | Violet | Procédure PRA déclenchée |

#### Tableau de bord Zabbix

```
Métriques clés visibles en temps réel :
- État des 12 tunnels VPN
- Disponibilité des services critiques (AD, DNS, Web, DB)
- Charge CPU/RAM des serveurs
- Espace disque restant
- Nombre de postes connectés au domaine
- Alertes actives
```

### 6.5 Plan de reprise d'activité (PRA)

| Scénario | RTO (objectif reprise) | RPO (perte données max) | Action |
|----------|----------------------|------------------------|--------|
| Panne d'un DC | 15 min | 0 (DC secondaire) | Basculement auto sur DC02 |
| Panne serveur fichiers | 4h | 24h | Restore depuis SRV-BACKUP |
| Panne site HQ | 4h | 24h | Activation site Azure (Cloud) |
| Corruption DB | 2h | 24h | Restore SQL depuis backup |
| Ransomware | 8h | 24h | Isolation + restore hors ligne |

---

## 7. Proposition d'une solution Cloud

### 7.1 Justification du Cloud

YMMO dispose de 12 agences nationales, d'une plateforme web accessible aux clients et d'une croissance prévisible. Le Cloud offre :
- **Haute disponibilité** : SLA 99,9% Azure
- **Scalabilité** : montée en charge lors des pics immobiliers
- **Sécurité** : certifications ISO 27001, HDS
- **Réduction des coûts matériels** à moyen terme

### 7.2 Architecture Cloud retenue : Microsoft Azure

Choix justifié par l'intégration native avec **Windows Server**, **Active Directory** et l'écosystème Microsoft déjà en place.

```
                    ┌──────────────────────────────────┐
                    │         Microsoft Azure           │
                    │                                   │
                    │  ┌─────────────┐  ┌───────────┐  │
                    │  │ Azure AD    │  │  Azure    │  │
                    │  │ (Entra ID)  │  │  Backup   │  │
                    │  └─────────────┘  └───────────┘  │
                    │                                   │
                    │  ┌─────────────┐  ┌───────────┐  │
                    │  │  Azure App  │  │  Azure    │  │
                    │  │  Service    │  │  SQL DB   │  │
                    │  │ (Web YMMO)  │  │           │  │
                    │  └─────────────┘  └───────────┘  │
                    │                                   │
                    │  ┌─────────────────────────────┐ │
                    │  │   Azure Virtual Network      │ │
                    │  │   (10.2.0.0/16)              │ │
                    │  │   VPN Gateway ↔ HQ VPN       │ │
                    │  └─────────────────────────────┘ │
                    └──────────────────────────────────┘
                               ↑ VPN Site-to-Site
                    ┌──────────┴──────────┐
                    │    Siège HQ         │
                    │    Aix-en-Provence  │
                    └─────────────────────┘
```

### 7.3 Services Azure utilisés

| Service Azure | Usage | Tarif mensuel estimé |
|--------------|-------|---------------------|
| **Azure AD (Entra ID) P1** | SSO, MFA, synchronisation AD | ~6 €/utilisateur/mois |
| **Azure Backup** | Sauvegarde hors site des serveurs | ~30 €/mois (1 To) |
| **Azure App Service (B2)** | Hébergement application web YMMO | ~55 €/mois |
| **Azure SQL Database (S2)** | Base de données production | ~75 €/mois |
| **Azure VPN Gateway (Basic)** | Tunnel VPN HQ ↔ Azure | ~27 €/mois |
| **Azure Monitor / Log Analytics** | Supervision centralisée | ~20 €/mois |
| **Azure Files** | Partage fichiers Cloud (DR) | ~20 €/mois (500 Go) |
| **TOTAL estimé** | | **~233 €/mois** |

### 7.4 Synchronisation AD → Azure AD

```powershell
# Installation d'Azure AD Connect sur SRV-DC01
# Télécharger depuis : https://www.microsoft.com/en-us/download/details.aspx?id=47594
# Configuration assistée :
# - Synchronisation de ymmo.local → tenant Azure
# - Activer Password Hash Sync (authentification hybride)
# - Activer SSO transparent
# - Filtrer les OU à synchroniser (pas les comptes de service)
```

### 7.5 Politique de données Cloud

- Toutes les données hébergées dans la région **France Centre** (Paris)
- Conformité **RGPD** : pas de transfert hors UE
- Chiffrement au repos : AES-256 (géré par Azure)
- Chiffrement en transit : TLS 1.3
- Clés de chiffrement : Azure Key Vault (gestion YMMO)

---

## 8. Guide de déploiement

### 8.1 Ordre de déploiement

```
Phase 1 — Infrastructure de base HQ (Semaine 1)
  ├── 1.1 Installation physique (serveurs, switches, routeur, pare-feu)
  ├── 1.2 Configuration réseau HQ (VLANs, routage inter-VLAN)
  ├── 1.3 Installation Windows Server 2022 sur SRV-DC01
  ├── 1.4 Promotion DC01 (AD DS, DNS, DHCP)
  └── 1.5 Déploiement GPO de base

Phase 2 — Services HQ (Semaine 2)
  ├── 2.1 Déploiement SRV-DC02 (redondance)
  ├── 2.2 Déploiement SRV-FS01 (partages fichiers, DFS)
  ├── 2.3 Déploiement SRV-BACKUP (politique de sauvegarde)
  ├── 2.4 Déploiement SRV-DB01 (SQL Server)
  └── 2.5 Déploiement SRV-WEB01 (DMZ)

Phase 3 — Connexion agences (Semaine 3)
  ├── 3.1 Configuration pare-feu (règles VPN IPSec)
  ├── 3.2 Déploiement routeurs agences (1 par agence)
  ├── 3.3 Configuration tunnels VPN HQ ↔ Agences (x12)
  ├── 3.4 Test de connectivité et de latence
  └── 3.5 Jonction domaine des postes agences

Phase 4 — Supervision & Cloud (Semaine 4)
  ├── 4.1 Déploiement Zabbix sur SRV-BACKUP
  ├── 4.2 Configuration Azure AD Connect
  ├── 4.3 Activation Azure Backup
  ├── 4.4 Déploiement application web (Azure App Service)
  └── 4.5 Tests d'intégration complets

Phase 5 — Recette & Formation (Semaine 5)
  ├── 5.1 Tests utilisateurs finaux
  ├── 5.2 Formation administrateurs SI
  ├── 5.3 Formation utilisateurs
  └── 5.4 Mise en production
```

### 8.2 Configuration routeur agence (exemple Cisco/pfSense)

```
# Configuration IPSec sur routeur agence (exemple pfSense / CLI Cisco)

# Phase 1 IKEv2
crypto ikev2 proposal YMMO-IKE
  encryption aes-cbc-256
  integrity sha256
  group 14

crypto ikev2 policy YMMO-POL
  proposal YMMO-IKE

crypto ikev2 keyring YMMO-KEYRING
  peer HQ-YMMO
    address <IP_WAN_SIEGE>
    pre-shared-key <PSK_SECRET>

# Phase 2 IPSec
crypto ipsec transform-set YMMO-TS esp-aes 256 esp-sha256-hmac
  mode tunnel

# Access-list trafic intéressant (agence 01 ↔ siège)
ip access-list extended VPN-ACL
  permit ip 10.1.1.0 0.0.0.255 192.168.1.0 0.0.0.255
  permit ip 10.1.1.0 0.0.0.255 192.168.2.0 0.0.0.255

# Crypto map
crypto map YMMO-MAP 10 ipsec-isakmp
  set peer <IP_WAN_SIEGE>
  set transform-set YMMO-TS
  match address VPN-ACL

# Appliquer sur interface WAN
interface GigabitEthernet0/0
  crypto map YMMO-MAP
```

### 8.3 Jonction d'un poste au domaine

```powershell
# Sur le poste Windows 10/11 (agence ou siège)
# Prérequis : DNS pointant sur 192.168.1.1

# Rejoindre le domaine
Add-Computer -DomainName "ymmo.local" `
    -Credential (Get-Credential "YMMO\Administrator") `
    -Restart
```

### 8.4 Déploiement de l'application web YMMO

```bash
# Sur SRV-WEB01 (Linux/Nginx) ou Azure App Service
# Exemple déploiement via Git

git clone https://github.com/ymmo/ymmo-web.git /var/www/ymmo
cd /var/www/ymmo

# Variables d'environnement
cp .env.example .env
# Éditer .env : DB_HOST=192.168.1.10, DB_NAME=ymmo_db, etc.

# Installer les dépendances (Python/PHP/Node selon le stack)
pip install -r requirements.txt   # Python
# ou
composer install                   # PHP

# Configurer Nginx
cat > /etc/nginx/sites-available/ymmo <<'EOF'
server {
    listen 443 ssl http2;
    server_name ymmo.fr www.ymmo.fr;

    ssl_certificate     /etc/ssl/ymmo.fr.crt;
    ssl_certificate_key /etc/ssl/ymmo.fr.key;
    ssl_protocols       TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

nginx -t && systemctl reload nginx
```

---

## 9. Liste du matériel et budgétisation

### 9.1 Matériel — Siège social (Aix-en-Provence)

| Référence | Désignation | Qté | Prix unitaire HT | Total HT |
|-----------|-------------|-----|-----------------|----------|
| **Serveurs** | | | | |
| DELL PowerEdge T550 | Serveur tour (DC01/DC02) | 2 | 2 500 € | 5 000 € |
| DELL PowerEdge T350 | Serveur fichiers/backup | 1 | 1 800 € | 1 800 € |
| DELL PowerEdge R350 | Serveur Web (DMZ) | 1 | 2 200 € | 2 200 € |
| **Réseau** | | | | |
| FortiGate 80F | Pare-feu UTM | 1 | 1 200 € | 1 200 € |
| Cisco ISR 4321 | Routeur HQ | 1 | 1 800 € | 1 800 € |
| Cisco Catalyst 2960-X 24P | Switch manageable PoE (HQ) | 2 | 800 € | 1 600 € |
| **Stockage** | | | | |
| NAS Synology DS1522+ | NAS sauvegarde (5 baies) | 1 | 700 € | 700 € |
| Disques WD Red Pro 4To | Disques NAS | 5 | 120 € | 600 € |
| **Postes utilisateurs HQ** | | | | |
| Dell OptiPlex 7010 | PC de bureau | 30 | 700 € | 21 000 € |
| Ecran 24" Dell P2422H | Moniteurs | 30 | 180 € | 5 400 € |
| **Périphériques** | | | | |
| HP LaserJet Pro M428 | Imprimante réseau HQ | 1 | 350 € | 350 € |
| UPS APC SMT1500I | Onduleur rack serveurs | 2 | 600 € | 1 200 € |
| **Câblage** | | | | |
| Câbles RJ45 Cat6A | Lot câblage | 1 | 500 € | 500 € |
| Baie 19" 12U | Baie réseau | 1 | 300 € | 300 € |
| **Licences** | | | | |
| Windows Server 2022 Std | Licence OS serveur | 3 | 850 € | 2 550 € |
| SQL Server 2022 Standard | Licence DB | 1 | 1 400 € | 1 400 € |
| **Sous-total HQ** | | | | **47 600 €** |

### 9.2 Matériel — Agences (×12)

| Référence | Désignation | Qté/agence | Prix unitaire HT | Total (×12) HT |
|-----------|-------------|-----------|-----------------|----------------|
| Dell OptiPlex 3000 | PC de bureau commercial | 5 | 600 € | 36 000 € |
| Ecran 24" | Moniteurs | 5 | 150 € | 9 000 € |
| HP LaserJet Pro M15w | Imprimante réseau | 1 | 120 € | 1 440 € |
| Fortinet FortiGate 40F | Routeur/Pare-feu IPSec | 1 | 500 € | 6 000 € |
| Switch TP-Link 8 ports | Commutateur non-manageable | 1 | 60 € | 720 € |
| UPS APC BE600M2 | Onduleur poste | 1 | 80 € | 960 € |
| Câblage RJ45 Cat6 | Lot câblage par agence | 1 | 100 € | 1 200 € |
| **Sous-total agences** | | | | **55 320 €** |

### 9.3 Services Cloud (Azure) — Annuel

| Service | Coût mensuel | Coût annuel |
|---------|-------------|------------|
| Azure AD Entra ID P1 (90 users) | 540 € | 6 480 € |
| Azure Backup (1 To) | 30 € | 360 € |
| Azure App Service B2 | 55 € | 660 € |
| Azure SQL Database S2 | 75 € | 900 € |
| Azure VPN Gateway Basic | 27 € | 324 € |
| Azure Monitor | 20 € | 240 € |
| Azure Files 500 Go | 20 € | 240 € |
| **Total Cloud annuel** | | **9 204 €** |

### 9.4 Récapitulatif budgétaire

| Poste | Montant HT |
|-------|-----------|
| Matériel siège | 47 600 € |
| Matériel agences (×12) | 55 320 € |
| Cloud Azure (an 1) | 9 204 € |
| Installation / intégration (prestataire) | 8 000 € |
| Formation utilisateurs | 2 000 € |
| **TOTAL HT** | **122 124 €** |
| TVA 20% | 24 424 € |
| **TOTAL TTC** | **146 548 €** |

> **Note :** Les coûts Cloud Azure sont récurrents annuellement (~9 200 €/an). Le matériel a une durée d'amortissement de 5 ans.

### 9.5 ROI et justification

| Critère | Sans solution | Avec solution YMMO |
|---------|--------------|---------------------|
| Gestion des fichiers | Clés USB / email | Partage centralisé sécurisé |
| Accès agences | VPN artisanal ou absent | VPN IPSec managé, sécurisé |
| Continuité de service | Aucune (SPOF) | DC redondant + Azure DR |
| Conformité RGPD | Non garantie | Conforme (Azure France) |
| Supervision | Aucune | Zabbix + Azure Monitor |

---

## Annexes

### Annexe A — Récapitulatif des adresses IP critiques

| Hôte | Adresse IP | Rôle |
|------|-----------|------|
| SRV-DC01 | 192.168.1.1 | DC principal, DNS, DHCP |
| SRV-DC02 | 192.168.1.2 | DC secondaire |
| SRV-FS01 | 192.168.1.4 | Serveur fichiers |
| SRV-BACKUP | 192.168.1.7 | Sauvegarde + Zabbix |
| SRV-DB01 | 192.168.1.10 | Base de données SQL |
| SRV-WEB01 | 10.0.0.1 | Serveur web (DMZ) |
| Pare-feu HQ | 192.168.1.253 | Filtrage réseau |
| Routeur HQ | 192.168.1.254 | Passerelle |
| VPN Concentrateur | 172.16.0.1 | Tunnels IPSec agences |

### Annexe B — Ports ouverts sur le pare-feu HQ

| Port | Protocole | Direction | Service |
|------|-----------|-----------|---------|
| 80, 443 | TCP | Entrant WAN | Site web YMMO public |
| 500, 4500 | UDP | Entrant WAN | IKEv2 / IPSec |
| 53 | TCP/UDP | Interne | DNS |
| 389, 636 | TCP | Interne | LDAP / LDAPS |
| 445 | TCP | Interne | SMB (fichiers) |
| 1433 | TCP | DMZ→Serveurs | SQL Server |
| 3389 | TCP | Admin uniquement | RDP (via VLAN40) |
| 443 | TCP | Sortant | Azure, WSUS |

### Annexe C — Contacts et responsabilités

| Rôle | Responsabilité |
|------|---------------|
| Administrateur SI | Gestion quotidienne AD, serveurs, VPN |
| Directeur SI | Validation des politiques de sécurité |
| Prestataire réseau | Maintenance matériel, interventions N3 |
| Microsoft (Support Azure) | Incidents Cloud critiques |

---

*Document réalisé dans le cadre du projet UF INFRA & DEV — Bachelor 2 Informatique Ynov*
*Version 1.0 — 2025*
