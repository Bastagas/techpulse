#!/usr/bin/env python3
"""Auto-retry pour Oracle Cloud Always Free ARM Ampere.

Tente de créer l'instance en boucle, retry toutes les N secondes tant que
l'API retourne "Out of host capacity". Notification macOS à la réussite.

Usage :
    deploy/oracle/.venv/bin/python deploy/oracle/auto_retry.py

Configuration :
    1. ~/.oci/config configuré via : oci setup config (OCI CLI)
       OU via les variables d'env OCI_* (voir RETRY.md)
    2. deploy/oracle/instance.config.yaml rempli avec les OCIDs requis

Le script s'arrête dès qu'une instance est créée avec succès (et te notifie).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

try:
    import oci
    import yaml
except ImportError:
    sys.stderr.write(
        "Dépendances manquantes. Lance :\n"
        "  python3 -m venv deploy/oracle/.venv\n"
        "  deploy/oracle/.venv/bin/pip install oci pyyaml\n"
    )
    sys.exit(1)


CONFIG_FILE = Path(__file__).parent / "instance.config.yaml"
OCI_CONFIG_FILE = Path.home() / ".oci" / "config"


def load_oci_config() -> dict:
    """Charge la config OCI depuis ~/.oci/config."""
    if not OCI_CONFIG_FILE.exists():
        sys.exit(
            f"✗ {OCI_CONFIG_FILE} introuvable. Lance 'oci setup config' "
            "d'abord (voir RETRY.md étape 2)."
        )
    return oci.config.from_file(str(OCI_CONFIG_FILE), profile_name="DEFAULT")


def load_instance_config() -> dict:
    """Charge les OCIDs et paramètres de l'instance à créer."""
    if not CONFIG_FILE.exists():
        sys.exit(
            f"✗ {CONFIG_FILE} introuvable. Copie instance.config.example.yaml "
            "vers instance.config.yaml et remplis les OCIDs (voir RETRY.md étape 3)."
        )
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    required = [
        "compartment_id", "availability_domain", "subnet_id",
        "image_id", "ssh_public_key", "shape", "ocpus", "memory_gb",
    ]
    missing = [k for k in required if not cfg.get(k)]
    if missing:
        sys.exit(f"✗ Clés manquantes dans {CONFIG_FILE} : {missing}")
    return cfg


def build_launch_details(cfg: dict, compute_mgmt) -> oci.core.models.LaunchInstanceDetails:
    """Construit l'objet LaunchInstanceDetails pour l'appel API."""
    return oci.core.models.LaunchInstanceDetails(
        availability_domain=cfg["availability_domain"],
        compartment_id=cfg["compartment_id"],
        display_name=cfg.get("display_name", "techpulse"),
        shape=cfg["shape"],
        shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
            ocpus=float(cfg["ocpus"]),
            memory_in_gbs=float(cfg["memory_gb"]),
        ),
        create_vnic_details=oci.core.models.CreateVnicDetails(
            subnet_id=cfg["subnet_id"],
            assign_public_ip=cfg.get("assign_public_ip", True),
        ),
        source_details=oci.core.models.InstanceSourceViaImageDetails(
            image_id=cfg["image_id"],
            boot_volume_size_in_gbs=int(cfg.get("boot_volume_gb", 50)),
        ),
        metadata={"ssh_authorized_keys": cfg["ssh_public_key"].strip()},
    )


def notify(title: str, message: str) -> None:
    """Notification macOS native."""
    if sys.platform == "darwin":
        os.system(f'''osascript -e 'display notification "{message}" with title "{title}" sound name "Glass"' ''')
    print(f"\n🔔 {title}\n   {message}\n")


def format_duration(seconds: int) -> str:
    h, s = divmod(seconds, 3600)
    m, s = divmod(s, 60)
    if h:
        return f"{h}h{m:02d}m"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def main() -> int:
    print("━" * 60)
    print("  TechPulse — Auto-retry Oracle ARM Ampere")
    print("━" * 60)

    oci_config = load_oci_config()
    instance_config = load_instance_config()
    oci.config.validate_config(oci_config)

    print(f"✓ Config OCI chargée (région {oci_config['region']})")
    print(f"✓ Shape : {instance_config['shape']} · {instance_config['ocpus']} OCPU · {instance_config['memory_gb']} GB")
    print(f"✓ AD : {instance_config['availability_domain']}")

    compute = oci.core.ComputeClient(oci_config)
    interval = int(instance_config.get("retry_interval_seconds", 30))

    attempt = 0
    started_at = time.time()
    last_error = ""

    try:
        while True:
            attempt += 1
            elapsed = int(time.time() - started_at)

            try:
                details = build_launch_details(instance_config, compute)
                response = compute.launch_instance(details)
                instance = response.data

                # ─── Succès ! ────────────
                print()
                print("━" * 60)
                print(f"  🎉 INSTANCE CRÉÉE ! (après {attempt} tentatives, {format_duration(elapsed)})")
                print("━" * 60)
                print(f"  ID       : {instance.id}")
                print(f"  Nom      : {instance.display_name}")
                print(f"  État     : {instance.lifecycle_state}")
                print(f"  Shape    : {instance.shape}")
                print()
                print("  → Attends ~2 min que Oracle finalise (status 'Running'),")
                print("    puis récupère l'IP publique dans la console et SSH-toi dessus.")
                print()
                notify(
                    "TechPulse — Oracle OK !",
                    f"Instance créée après {attempt} essais. Va sur Oracle Cloud Console.",
                )
                return 0

            except oci.exceptions.ServiceError as exc:
                msg = exc.message or ""
                if "Out of host capacity" in msg or exc.status in (500, 429):
                    error_type = "out-of-capacity"
                    short_msg = "Out of host capacity"
                elif exc.status == 400:
                    # Limite free tier dépassée, ou config invalide
                    print(f"\n✗ Erreur 400 de l'API :\n{exc}\n")
                    print("Cause probable : OCIDs invalides ou tu dépasses le quota free tier.")
                    print("Vérifie ton instance.config.yaml.")
                    return 1
                elif exc.status == 401 or exc.status == 403:
                    print(f"\n✗ Authentification OCI échouée ({exc.status}).")
                    print("Vérifie ~/.oci/config et que ta clé API est bien uploadée sur Oracle.")
                    return 1
                else:
                    error_type = f"HTTP {exc.status}"
                    short_msg = msg[:80]

                # Print ligne compacte pour chaque attempt
                ts = time.strftime("%H:%M:%S")
                print(f"  [{ts}] attempt {attempt} ({format_duration(elapsed)}) → {short_msg}", flush=True)
                last_error = short_msg

            except Exception as exc:
                print(f"\n✗ Erreur inattendue : {type(exc).__name__} : {exc}")
                return 2

            # Retry après sommeil
            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\n⏹  Interrompu par l'utilisateur après {attempt} tentatives ({format_duration(elapsed)}).")
        print(f"  Dernière erreur : {last_error}")
        return 130


if __name__ == "__main__":
    sys.exit(main())
