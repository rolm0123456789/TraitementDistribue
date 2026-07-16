#!/usr/bin/env python3
"""
Étape 1 — Hash naïf : répartir K clés sur N nœuds avec h(clé) % N.

Objectif :
  - Placement déterministe (même clé → même nœud d'un run à l'autre)
  - Comptage de la charge par nœud

Usage :
  python etape1_hash_naif.py
  python etape1_hash_naif.py demo
"""

from __future__ import annotations

import hashlib
import sys
from collections import Counter

from affichage import (
    C,
    barre,
    c,
    couleur_noeud,
    info,
    ok,
    section,
    titre,
    warn,
)


def hash_stable(cle: str) -> int:
    """Hash cryptographique stable (md5). Ne pas utiliser hash() de Python."""
    digest = hashlib.md5(cle.encode("utf-8")).hexdigest()
    return int(digest, 16)


def noeud_pour(cle: str, n: int) -> int:
    """Retourne l'index du nœud responsable de la clé (0 .. n-1)."""
    if n <= 0:
        raise ValueError("N doit être strictement positif")
    return hash_stable(cle) % n


def placer(cles: list[str], n: int) -> dict[str, int]:
    """Associe chaque clé à un nœud."""
    return {cle: noeud_pour(cle, n) for cle in cles}


def charge_par_noeud(placement: dict[str, int], n: int) -> list[int]:
    """Retourne la liste des charges (nombre de clés) pour les nœuds 0..n-1."""
    compteur = Counter(placement.values())
    return [compteur.get(i, 0) for i in range(n)]


def generer_cles(k: int, prefix: str = "cle") -> list[str]:
    """Génère K clés déterministes."""
    return [f"{prefix}-{i:05d}" for i in range(k)]


def _ecart_type(valeurs: list[int | float]) -> float:
    if not valeurs:
        return 0.0
    m = sum(valeurs) / len(valeurs)
    return (sum((x - m) ** 2 for x in valeurs) / len(valeurs)) ** 0.5


def _schema_modulo(n: int) -> None:
    """Petit schéma ASCII : clé → md5 → modulo → nœud."""
    print(c("  ┌─────────┐     ┌──────────┐     ┌─────────┐     ┌────────┐", C.DIM))
    print(
        c("  │  clé    │", C.DIM)
        + " ──► "
        + c("│ md5(clé) │", C.CYAN)
        + " ──► "
        + c(f"│  h % {n}  │", C.YELLOW)
        + " ──► "
        + c("│ nœud i │", C.GREEN)
    )
    print(c("  └─────────┘     └──────────┘     └─────────┘     └────────┘", C.DIM))
    print(c("       stable d'un run à l'autre (pas hash() Python !)", C.DIM))
    print()


def afficher_demo(n: int = 4, k: int = 1000, echantillon: list[str] | None = None) -> None:
    titre("ÉTAPE 1 — Hash naïf", "Placement déterministe par h(clé) % N")

    print(f"  Paramètres :  N = {c(str(n), C.BOLD, C.CYAN)} nœuds"
          f"  ·  K = {c(str(k), C.BOLD, C.CYAN)} clés")
    print()
    _schema_modulo(n)

    fruits = echantillon or [
        "kiwi", "orange", "fraise", "prune",
        "cerise", "citron", "banane", "figue",
    ]

    # Grouper par nœud pour un rendu type "boîtes"
    groupes: dict[int, list[str]] = {i: [] for i in range(n)}
    section("Placement d'un échantillon de fruits")
    for fruit in fruits:
        idx = noeud_pour(fruit, n)
        h = hash_stable(fruit)
        groupes[idx].append(fruit)
        col = couleur_noeud(idx)
        print(
            f"    {c(fruit.ljust(10), C.BOLD)}  "
            f"{c('→', C.DIM)}  "
            f"{c(f'nœud {idx}', col, C.BOLD)}   "
            f"{c(f'(md5 % {n} = {h % n})', C.DIM)}"
        )
    print()

    section("Vue par nœud (échantillon)")
    for i in range(n):
        col = couleur_noeud(i)
        contenu = ", ".join(groupes[i]) if groupes[i] else c("∅", C.DIM)
        print(f"    {c(f'┌ nœud {i} ', col, C.BOLD)}{c('─' * 20, col)}")
        print(f"    {c('│', col)}  {contenu}")
        print(f"    {c('└' + '─' * 28, col)}")
    print()

    # Répartition sur K clés
    cles = generer_cles(k)
    placement = placer(cles, n)
    charges = charge_par_noeud(placement, n)
    moyenne = k / n
    std = _ecart_type(charges)

    section(f"Charge sur {k} clés (répartition globale)")
    max_c = max(charges) if charges else 1
    for i, count in enumerate(charges):
        col = couleur_noeud(i)
        pct = count / k * 100
        b = barre(count, max_c * 1.05, 28, col)
        print(
            f"    {c(f'nœud {i}', col, C.BOLD):s}  "
            f"{count:5d} clés  ({pct:5.1f} %)  {b}  "
            f"{c(f'Δ={count - moyenne:+.1f}', C.DIM)}"
        )
    print()
    print(f"    Moyenne attendue : {c(f'{moyenne:.1f}', C.BOLD)} clés / nœud")
    print(f"    Écart-type       : {c(f'{std:.2f}', C.BOLD)}")
    print(f"    Idéal (uniforme) : {c(f'{100/n:.1f} %', C.DIM)} par nœud")
    print()

    ok("Placement déterministe et ~uniforme sur beaucoup de clés.")
    warn("Mais tout repose sur N fixe — voir étape 2 si N change.")
    print()


def main() -> None:
    afficher_demo(n=4, k=1000)


if __name__ == "__main__":
    main()
