#!/usr/bin/env python3
"""
Étape 4 — Nœuds virtuels (vnodes) pour lisser la charge.

Objectif :
  - Semer V répliques (vnodes) par nœud physique sur l'anneau
  - Mapper chaque vnode → nœud réel
  - Mesurer l'équilibrage (écart-type) en fonction de V

Usage :
  python etape4_vnodes.py
  python etape4_vnodes.py demo
"""

from __future__ import annotations

import bisect
import hashlib
from collections import Counter

from etape1_hash_naif import generer_cles
from etape3_anneau import RING_SIZE, taux_deplacement
from affichage import (
    C,
    barre,
    barre_pct,
    c,
    couleur_noeud,
    dessiner_cercle,
    event,
    info,
    ok,
    section,
    tableau,
    titre,
    warn,
)

V_DEFAUT = 150


def hash_ring(valeur: str) -> int:
    digest = hashlib.md5(valeur.encode("utf-8")).hexdigest()
    return int(digest, 16) % RING_SIZE


class AnneauVnodes:
    """Anneau de hachage cohérent avec nœuds virtuels."""

    def __init__(self, v: int = V_DEFAUT) -> None:
        if v < 1:
            raise ValueError("V (nombre de vnodes par nœud) doit être ≥ 1")
        self.v = v
        self._positions: list[int] = []
        self._pos_vers_noeud: dict[int, str] = {}
        self._noeuds: set[str] = set()

    def ajouter(self, noeud: str) -> list[int]:
        if noeud in self._noeuds:
            return [p for p, n in self._pos_vers_noeud.items() if n == noeud]
        positions: list[int] = []
        for i in range(self.v):
            pos = hash_ring(f"{noeud}#{i}")
            while pos in self._pos_vers_noeud:
                pos = (pos + 1) % RING_SIZE
            bisect.insort(self._positions, pos)
            self._pos_vers_noeud[pos] = noeud
            positions.append(pos)
        self._noeuds.add(noeud)
        return positions

    def retirer(self, noeud: str) -> bool:
        if noeud not in self._noeuds:
            return False
        a_supprimer = [p for p, n in self._pos_vers_noeud.items() if n == noeud]
        for pos in a_supprimer:
            del self._pos_vers_noeud[pos]
            idx = bisect.bisect_left(self._positions, pos)
            if idx < len(self._positions) and self._positions[idx] == pos:
                self._positions.pop(idx)
        self._noeuds.discard(noeud)
        return True

    def noeud_pour(self, cle: str) -> str:
        if not self._positions:
            raise RuntimeError("Anneau vide : aucun nœud")
        h = hash_ring(cle)
        idx = bisect.bisect_left(self._positions, h)
        if idx == len(self._positions):
            idx = 0
        return self._pos_vers_noeud[self._positions[idx]]

    def placer(self, cles: list[str]) -> dict[str, str]:
        return {cle: self.noeud_pour(cle) for cle in cles}

    def positions_detail(self) -> list[tuple[int, str]]:
        return [(p, self._pos_vers_noeud[p]) for p in self._positions]

    @property
    def nb_vnodes(self) -> int:
        return len(self._positions)

    def __len__(self) -> int:
        return len(self._noeuds)


def ecart_type(valeurs: list[float]) -> float:
    if not valeurs:
        return 0.0
    m = sum(valeurs) / len(valeurs)
    return (sum((x - m) ** 2 for x in valeurs) / len(valeurs)) ** 0.5


def mesurer_equilibrage(
    noeuds: list[str],
    cles: list[str],
    v: int,
) -> tuple[dict[str, int], float, float]:
    anneau = AnneauVnodes(v=v)
    for n in noeuds:
        anneau.ajouter(n)
    placement = anneau.placer(cles)
    charges_d = Counter(placement.values())
    charges = {n: charges_d.get(n, 0) for n in noeuds}
    vals = list(charges.values())
    std = ecart_type([float(x) for x in vals])
    moyenne = sum(vals) / len(vals) if vals else 0.0
    cv = (std / moyenne * 100) if moyenne else 0.0
    return charges, std, cv


def _schema_vnodes(v: int) -> None:
    print(c("  Chaque nœud physique est semé en V points sur l'anneau :", C.DIM))
    print()
    print(
        f"    {c('nœud A', C.CYAN, C.BOLD)}  →  "
        + c(" · ".join(f"A#{i}" for i in range(min(4, v))), C.CYAN)
        + (c(" · …", C.CYAN) if v > 4 else "")
        + c(f"  ({v} vnodes)", C.DIM)
    )
    print(
        f"    {c('nœud B', C.GREEN, C.BOLD)}  →  "
        + c(" · ".join(f"B#{i}" for i in range(min(4, v))), C.GREEN)
        + (c(" · …", C.GREEN) if v > 4 else "")
        + c(f"  ({v} vnodes)", C.DIM)
    )
    print(
        f"    {c('nœud C', C.YELLOW, C.BOLD)}  →  "
        + c(" · ".join(f"C#{i}" for i in range(min(4, v))), C.YELLOW)
        + (c(" · …", C.YELLOW) if v > 4 else "")
        + c(f"  ({v} vnodes)", C.DIM)
    )
    print()
    print(c("  Plus V est grand → arcs plus petits et plus homogènes → charge lissée.", C.DIM))
    print()


def _dessiner_vnodes_sur_cercle(
    anneau: AnneauVnodes,
    noeuds: list[str],
    charges: dict[str, int],
    k: int,
    titre_cercle: str,
    max_points: int = 90,
) -> None:
    """Affiche un cercle avec un échantillon de vnodes colorés par nœud réel."""
    detail = anneau.positions_detail()
    # Sous-échantillonner si trop de vnodes pour rester lisible
    step = max(1, len(detail) // max_points)
    sample = detail[::step]

    points = []
    for pos, nom in sample:
        idx = noeuds.index(nom) if nom in noeuds else 0
        col = couleur_noeud(idx)
        sym = chr(ord("A") + idx) if idx < 26 else "●"
        points.append((float(pos), sym, col))

    legende = []
    for i, nom in enumerate(noeuds):
        col = couleur_noeud(i)
        sym = chr(ord("A") + i) if i < 26 else "●"
        ch = charges.get(nom, 0)
        pct = ch / k * 100 if k else 0
        nb_v = sum(1 for _, n in detail if n == nom)
        legende.append((sym, f"{nom}  ·  {nb_v} vnodes  ·  {ch} clés ({pct:.1f} %)", col))

    dessiner_cercle(
        points,
        ring_size=RING_SIZE,
        titre_cercle=titre_cercle,
        rayon=12,
        legende=legende,
    )


def afficher_demo(n: int = 5, k: int = 20_000) -> None:
    titre("ÉTAPE 4 — Nœuds virtuels", "Lisser la charge avec V répliques par nœud physique")

    print(f"  Paramètres :  N = {c(str(n), C.BOLD, C.CYAN)} nœuds"
          f"  ·  K = {c(f'{k:,}'.replace(',', ' '), C.BOLD, C.CYAN)} clés"
          f"  ·  V défaut = {c(str(V_DEFAUT), C.BOLD, C.YELLOW)}")
    print()
    _schema_vnodes(V_DEFAUT)

    noeuds = [f"nœud-{i}" for i in range(n)]
    cles = generer_cles(k)

    # ── Tableau d'équilibrage selon V ────────────────────────────────────────
    valeurs_v = [1, 5, 20, 50, 100, 150, 200]
    section("Équilibrage selon V (écart-type de la charge)")
    resultats: dict[int, tuple[dict[str, int], float, float]] = {}
    rows = []
    max_cv = 0.0
    for v in valeurs_v:
        charges, std, cv = mesurer_equilibrage(noeuds, cles, v)
        resultats[v] = (charges, std, cv)
        max_cv = max(max_cv, cv)
        vals = list(charges.values())
        rows.append((
            str(v),
            str(v * n),
            f"{std:8.1f}",
            f"{cv:6.2f} %",
            f"{min(vals)} / {max(vals)}",
            barre_pct(cv, 14, C.RED if cv > 20 else (C.YELLOW if cv > 8 else C.GREEN)),
        ))
    tableau(
        ("V", "vnodes", "σ charge", "CV %", "min / max", "déséquilibre"),
        rows,
        aligns="rrrrlr",
    )
    print()
    print(c("  CV % = coefficient de variation (σ / moyenne). Plus c’est bas, mieux c’est.", C.DIM))
    print()

    # ── Courbe ASCII CV vs V ─────────────────────────────────────────────────
    section("Courbe CV % en fonction de V")
    max_cv_plot = max(cv for _, _, cv in resultats.values()) or 1
    for v in valeurs_v:
        _, _, cv = resultats[v]
        col = C.RED if cv > 20 else (C.YELLOW if cv > 8 else C.GREEN)
        print(f"    V={v:3d}  {barre(cv, max_cv_plot, 36, col)}  {cv:6.2f} %")
    print()

    # ── Cercles V=1 vs V=150 ─────────────────────────────────────────────────
    for v in (1, V_DEFAUT):
        charges, std, cv = resultats[v]
        event(f"Anneau avec V = {v}  (σ = {std:.1f}, CV = {cv:.2f} %)")
        print()
        anneau = AnneauVnodes(v=v)
        for noeud in noeuds:
            anneau.ajouter(noeud)
        label = (
            f"V = {v} — un point par nœud (déséquilibré)"
            if v == 1
            else f"V = {v} — {v * n} vnodes (charge lissée)"
        )
        _dessiner_vnodes_sur_cercle(anneau, noeuds, charges, k, label)
        print()

        section(f"Détail de charge V={v}")
        moyenne = k / n
        max_c = max(charges.values())
        for i, noeud in enumerate(noeuds):
            col = couleur_noeud(i)
            count = charges[noeud]
            pct = count / k * 100
            b = barre(count, max_c * 1.05, 24, col)
            print(
                f"    {c(noeud.ljust(10), col, C.BOLD)} {count:5d}  ({pct:5.1f} %)  "
                f"{b}  {c(f'Δ={count - moyenne:+.0f}', C.DIM)}"
            )
        print(f"    → σ = {c(f'{std:.1f}', C.BOLD)}  ·  CV = {c(f'{cv:.2f} %', C.BOLD)}")
        print()

    # ── Ajout d'un nœud ──────────────────────────────────────────────────────
    event(f"Ajout d'un 6e nœud avec V={V_DEFAUT}")
    print()
    anneau = AnneauVnodes(v=V_DEFAUT)
    for noeud in noeuds:
        anneau.ajouter(noeud)
    place_avant = anneau.placer(cles)
    nouveau = f"nœud-{n}"
    anneau.ajouter(nouveau)
    place_apres = anneau.placer(cles)
    taux = taux_deplacement(place_avant, place_apres)
    charges_apres = dict(Counter(place_apres.values()))

    print(f"    Clés déplacées : {c(f'{int(taux * k)} / {k}', C.BOLD, C.YELLOW)}  "
          f"({c(f'{taux * 100:.2f} %', C.YELLOW, C.BOLD)})")
    print(f"    Attendu ≈ 1/(N+1) = {100 / (n + 1):.2f} %  "
          f"{c('(mais en petits arcs lissés)', C.DIM)}")
    print()

    section("Anneau après ajout (échantillon de vnodes)")
    print()
    noeuds2 = noeuds + [nouveau]
    _dessiner_vnodes_sur_cercle(
        anneau,
        noeuds2,
        charges_apres,
        k,
        f"Après ajout de {nouveau}  ·  V={V_DEFAUT}",
    )
    print()

    ok("Plus V est grand, plus la charge est uniforme.")
    ok("Un ajout/retrait ne touche que de petits arcs (déplacement fin).")
    info("C'est le modèle utilisé par Dynamo, Cassandra et Riak en production.")
    warn("Trop de vnodes → anneau lourd en mémoire ; le compromis usuel est ~150.")
    print()


def main() -> None:
    afficher_demo(n=5, k=20_000)


if __name__ == "__main__":
    main()
