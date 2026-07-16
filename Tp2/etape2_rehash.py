#!/usr/bin/env python3
"""
Étape 2 — Le rehash : mesurer ce qui bouge quand N → N+1.

Objectif :
  - Placer K clés avec N nœuds, puis avec N+1
  - Compter les clés qui changent de nœud
  - Montrer que ~ N/(N+1) des clés bougent (~80 % pour N=4)

Usage :
  python etape2_rehash.py
  python etape2_rehash.py demo
"""

from __future__ import annotations

from etape1_hash_naif import generer_cles, placer
from affichage import (
    C,
    barre,
    barre_pct,
    c,
    couleur_noeud,
    event,
    info,
    ok,
    section,
    tableau,
    titre,
    warn,
)


def compter_deplacements(
    cles: list[str],
    n_avant: int,
    n_apres: int,
) -> tuple[int, float, dict[str, tuple[int, int]]]:
    """
    Compare le placement avant/après.
    Retourne (nb_déplacées, taux, détail des clés qui bougent).
    """
    place_avant = placer(cles, n_avant)
    place_apres = placer(cles, n_apres)

    deplacees: dict[str, tuple[int, int]] = {}
    for cle in cles:
        a, b = place_avant[cle], place_apres[cle]
        if a != b:
            deplacees[cle] = (a, b)

    total = len(cles)
    nb = len(deplacees)
    taux = nb / total if total else 0.0
    return nb, taux, deplacees


def taux_theorique(n: int) -> float:
    """Avec h % N, environ N/(N+1) des clés changent de nœud quand on passe à N+1."""
    return n / (n + 1)


def _schema_rehash(n: int, n2: int, taux: float) -> None:
    print(c("  Avant                          Après", C.DIM))
    print(
        c(f"  ┌ N = {n} nœuds ┐", C.CYAN)
        + "     "
        + c("rehash", C.YELLOW, C.BOLD)
        + "     "
        + c(f"┌ N = {n2} nœuds ┐", C.MAGENTA)
    )
    print(
        c("  │  h % N     │", C.CYAN)
        + c("  ─────────►  ", C.YELLOW)
        + c("│  h % (N+1)  │", C.MAGENTA)
    )
    print(
        c("  └────────────┘", C.CYAN)
        + "                "
        + c("└──────────────┘", C.MAGENTA)
    )
    print()
    print(
        f"  {c('Presque tout le keyspace est recalculé', C.BOLD, C.RED)}"
        f"  →  {c(f'{taux*100:.0f} % des clés bougent', C.RED, C.BOLD)}"
    )
    print()


def afficher_demo(n: int = 4, k: int = 10_000) -> None:
    n2 = n + 1
    titre("ÉTAPE 2 — Rehash", f"Mesurer le chaos quand N passe de {n} à {n2}")

    print(f"  Paramètres :  N = {c(str(n), C.BOLD)} → {c(str(n2), C.BOLD, C.MAGENTA)}"
          f"  ·  K = {c(f'{k:,}'.replace(',', ' '), C.BOLD, C.CYAN)} clés")
    print()

    cles = generer_cles(k)
    nb, taux, deplacees = compter_deplacements(cles, n, n2)
    attendu = taux_theorique(n)

    _schema_rehash(n, n2, taux)

    section("Résultats du rebalancement")
    print(f"    Clés déplacées   : {c(f'{nb:,} / {k:,}'.replace(',', ' '), C.BOLD, C.RED)}")
    print(f"    Taux mesuré      : {c(f'{taux * 100:5.2f} %', C.BOLD, C.RED)}  {barre_pct(taux * 100, 28, C.RED)}")
    print(f"    Taux théorique   : {c(f'{attendu * 100:5.2f} %', C.BOLD)}  {c(f'(N/(N+1) = {n}/{n2})', C.DIM)}")
    print(f"    Écart            : {abs(taux - attendu) * 100:5.2f} points")
    print()

    # Barre visuelle "restent / bougent"
    restent = 100.0 - taux * 100
    section("Répartition du destin des clés")
    print(f"    {c('Restent en place', C.GREEN)}  {barre_pct(restent, 36, C.GREEN)}  {restent:5.1f} %")
    print(f"    {c('Changent de nœud', C.RED)}  {barre_pct(taux * 100, 36, C.RED)}  {taux * 100:5.1f} %")
    print()

    section("Exemples de déplacements (10 premières clés)")
    for i, (cle, (a, b)) in enumerate(deplacees.items()):
        if i >= 10:
            break
        ca, cb = couleur_noeud(a), couleur_noeud(b)
        print(
            f"    {c(cle.ljust(12), C.DIM)}  "
            f"{c(f'nœud {a}', ca)}  "
            f"{c('──►', C.YELLOW)}  "
            f"{c(f'nœud {b}', cb)}"
        )
    print()

    section("Taux de déplacement pour d'autres valeurs de N")
    rows = []
    for n_test in (2, 3, 4, 5, 8, 16, 32):
        _, t, _ = compter_deplacements(cles, n_test, n_test + 1)
        th = taux_theorique(n_test)
        bar = barre_pct(t * 100, 16, C.RED if t > 0.7 else C.YELLOW)
        rows.append((
            str(n_test),
            str(n_test + 1),
            f"{t * 100:5.2f} %",
            f"{th * 100:5.2f} %",
            bar,
        ))
    tableau(
        ("N", "N+1", "mesuré", "théorique", "visualisation"),
        rows,
        aligns="rrrrr",
    )
    print()

    ok("Avec le modulo, ajouter UN seul nœud déplace ~ N/(N+1) des clés.")
    warn("Inacceptable pour un cache ou un stockage distribué (recopie massive).")
    info("Solution : hash cohérent (étape 3) — seul un arc voisin bouge.")
    print()


def main() -> None:
    afficher_demo(n=4, k=10_000)


if __name__ == "__main__":
    main()
