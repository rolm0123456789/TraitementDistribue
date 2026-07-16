#!/usr/bin/env python3
"""
Étape 3 — Anneau cohérent (consistent hashing) avec bisect.

Objectif :
  - Placer nœuds et clés sur un anneau [0, 2³²)
  - Router : premier nœud ≥ h(clé) (sinon boucle sur le premier)
  - Ajout / retrait d'un nœud sans tout rehacher (≈ K/N déplacées)

Usage :
  python etape3_anneau.py
  python etape3_anneau.py demo
"""

from __future__ import annotations

import bisect
import hashlib
from collections import Counter

from etape1_hash_naif import generer_cles
from affichage import (
    C,
    barre,
    barre_pct,
    c,
    couleur_noeud,
    dessiner_anneau_noeuds,
    dessiner_cercle,
    event,
    info,
    jauge_comparaison,
    ok,
    section,
    titre,
    warn,
)

RING_SIZE = 2**32  # espace de hachage [0, 2^32)


def hash_ring(valeur: str) -> int:
    """Position sur l'anneau : h(valeur) mod 2^32."""
    digest = hashlib.md5(valeur.encode("utf-8")).hexdigest()
    return int(digest, 16) % RING_SIZE


class AnneauCoherent:
    """Anneau de hachage cohérent (un point par nœud physique)."""

    def __init__(self) -> None:
        self._positions: list[int] = []
        self._noeuds: dict[int, str] = {}

    def ajouter(self, noeud: str) -> int:
        """Ajoute un nœud sur l'anneau. Retourne sa position."""
        pos = hash_ring(noeud)
        while pos in self._noeuds and self._noeuds[pos] != noeud:
            pos = (pos + 1) % RING_SIZE
        if pos in self._noeuds:
            return pos
        bisect.insort(self._positions, pos)
        self._noeuds[pos] = noeud
        return pos

    def retirer(self, noeud: str) -> bool:
        """Retire un nœud. Retourne True s'il était présent."""
        a_supprimer = [p for p, n in self._noeuds.items() if n == noeud]
        if not a_supprimer:
            return False
        for pos in a_supprimer:
            del self._noeuds[pos]
            idx = bisect.bisect_left(self._positions, pos)
            if idx < len(self._positions) and self._positions[idx] == pos:
                self._positions.pop(idx)
        return True

    def noeud_pour(self, cle: str) -> str:
        """Premier nœud dont la position est ≥ h(clé) (boucle si besoin)."""
        if not self._positions:
            raise RuntimeError("Anneau vide : aucun nœud")
        h = hash_ring(cle)
        idx = bisect.bisect_left(self._positions, h)
        if idx == len(self._positions):
            idx = 0
        return self._noeuds[self._positions[idx]]

    def position_cle(self, cle: str) -> int:
        return hash_ring(cle)

    def placer(self, cles: list[str]) -> dict[str, str]:
        return {cle: self.noeud_pour(cle) for cle in cles}

    def positions(self) -> list[tuple[int, str]]:
        return [(p, self._noeuds[p]) for p in self._positions]

    def arc_sizes(self) -> dict[str, float]:
        """Fraction de l'anneau (0..1) gérée par chaque nœud (arc précédent → lui)."""
        if not self._positions:
            return {}
        result: dict[str, float] = {}
        m = len(self._positions)
        for i, pos in enumerate(self._positions):
            prev = self._positions[i - 1] if i > 0 else self._positions[-1]
            if i == 0:
                taille = (pos + RING_SIZE - prev) % RING_SIZE
                if taille == 0:
                    taille = RING_SIZE
            else:
                taille = pos - prev
            nom = self._noeuds[pos]
            result[nom] = result.get(nom, 0.0) + taille / RING_SIZE
        return result

    def __len__(self) -> int:
        return len(self._positions)


def taux_deplacement(avant: dict[str, str], apres: dict[str, str]) -> float:
    if not avant:
        return 0.0
    bougent = sum(1 for c in avant if avant[c] != apres.get(c))
    return bougent / len(avant)


def charge_par_noeud(placement: dict[str, str]) -> dict[str, int]:
    return dict(Counter(placement.values()))


def _schema_routage() -> None:
    print(c("  Routage sur l'anneau (sens horaire) :", C.DIM))
    print()
    print(c("          ╭── nœud ──╮", C.CYAN))
    print(c("         ╱           ╲", C.DIM))
    print(
        c("    nœud", C.GREEN)
        + c(" ●─────● h(clé) ", C.YELLOW)
        + c("───►", C.BOLD, C.YELLOW)
        + c(" 1er nœud ≥ h(clé)", C.BOLD)
    )
    print(c("         ╲           ╱", C.DIM))
    print(c("          ╰─────────╯", C.CYAN))
    print(c("     Si la clé est après le dernier nœud → boucle sur le premier.", C.DIM))
    print()


def _print_charges(noeuds: list[str], charges: dict[str, int], k: int, arcs: dict[str, float] | None = None) -> None:
    max_c = max(charges.values()) if charges else 1
    for i, noeud in enumerate(noeuds):
        col = couleur_noeud(i)
        count = charges.get(noeud, 0)
        pct = count / k * 100 if k else 0
        b = barre(count, max_c * 1.05, 26, col)
        arc_txt = ""
        if arcs is not None:
            arc_txt = c(f"  arc={arcs.get(noeud, 0)*100:5.1f}%", C.DIM)
        print(f"    {c(noeud.ljust(10), col, C.BOLD)} {count:5d}  ({pct:5.1f} %)  {b}{arc_txt}")


def afficher_demo(n: int = 4, k: int = 10_000) -> None:
    titre("ÉTAPE 3 — Anneau cohérent", "Routage par bisect sur [0, 2³²) · ajout/retrait local")

    print(f"  Paramètres :  N = {c(str(n), C.BOLD, C.CYAN)} nœuds"
          f"  ·  K = {c(f'{k:,}'.replace(',', ' '), C.BOLD, C.CYAN)} clés"
          f"  ·  espace = {c('2³²', C.BOLD)}")
    print()
    _schema_routage()

    noeuds = [f"nœud-{i}" for i in range(n)]
    anneau = AnneauCoherent()

    section("Placement des nœuds sur l'anneau")
    for i, noeud in enumerate(noeuds):
        pos = anneau.ajouter(noeud)
        col = couleur_noeud(i)
        pct = pos / RING_SIZE * 100
        print(
            f"    {c('+', C.GREEN)} {c(noeud, col, C.BOLD):s}  "
            f"position = {c(f'{pos:>10d}', C.DIM)}  "
            f"({c(f'{pct:5.2f} %', col)} de l'anneau)"
        )
    print()

    cles = generer_cles(k)
    placement = anneau.placer(cles)
    charges = charge_par_noeud(placement)
    arcs = anneau.arc_sizes()

    # Échantillon de positions de clés pour le dessin
    echantillon_pos = [hash_ring(cle) for cle in cles[:: max(1, k // 60)]]

    section("Anneau initial — nœuds & répartition")
    print()
    dessiner_anneau_noeuds(
        anneau.positions(),
        ring_size=RING_SIZE,
        charges=charges,
        total_cles=k,
        cles_pos=echantillon_pos,
        titre_cercle="Anneau cohérent — état initial (∙ = échantillon de clés)",
    )
    print()

    section(f"Charge mesurée ({k} clés)")
    _print_charges(noeuds, charges, k, arcs)
    print()
    warn("Avec peu de nœuds physiques, les arcs sont inégaux → charge déséquilibrée.")
    print()

    # ── Ajout d'un nœud ──────────────────────────────────────────────────────
    nouveau = f"nœud-{n}"
    event(f"Ajout de {nouveau} sur l'anneau")
    print()
    pos_new = anneau.ajouter(nouveau)
    placement2 = anneau.placer(cles)
    taux = taux_deplacement(placement, placement2)
    attendu = 1.0 / (n + 1)
    charges2 = charge_par_noeud(placement2)
    arcs2 = anneau.arc_sizes()

    print(f"    Position de {c(nouveau, C.BOLD, C.YELLOW)} : {pos_new}  "
          f"({pos_new / RING_SIZE * 100:.2f} %)")
    print(f"    Clés déplacées : {c(f'{int(taux * k)} / {k}', C.BOLD, C.YELLOW)}  "
          f"({c(f'{taux * 100:.2f} %', C.YELLOW, C.BOLD)})")
    print(f"    Attendu ≈ 1/(N+1) = {attendu * 100:.2f} %  "
          f"{c('(seul l’arc voisin est touché)', C.DIM)}")
    print()

    section("Anneau après ajout")
    print()
    dessiner_anneau_noeuds(
        anneau.positions(),
        ring_size=RING_SIZE,
        charges=charges2,
        total_cles=k,
        cles_pos=echantillon_pos,
        nouveau=nouveau,
        titre_cercle=f"Après ajout de {nouveau}  (★ = nouveau nœud)",
    )
    print()

    section("Charge après ajout")
    _print_charges(noeuds + [nouveau], charges2, k, arcs2)
    print()

    # ── Retrait ──────────────────────────────────────────────────────────────
    retire = noeuds[1]
    event(f"Retrait de {retire}")
    print()
    placement_avant_retrait = dict(placement2)
    # Sauvegarder positions avant retrait pour le cercle "qui récupère"
    anneau.retirer(retire)
    placement3 = anneau.placer(cles)
    taux_r = taux_deplacement(placement_avant_retrait, placement3)
    charges3 = charge_par_noeud(placement3)

    print(f"    Clés déplacées : {c(f'{int(taux_r * k)} / {k}', C.BOLD)}  "
          f"({taux_r * 100:.2f} %)")
    print(c("    ≈ charge du nœud retiré — les autres arcs restent intacts", C.DIM))
    print()

    section("Anneau après retrait")
    print()
    dessiner_anneau_noeuds(
        anneau.positions(),
        ring_size=RING_SIZE,
        charges=charges3,
        total_cles=k,
        cles_pos=echantillon_pos,
        titre_cercle=f"Après retrait de {retire}",
    )
    print()

    # ── Comparaison naïf vs cohérent ─────────────────────────────────────────
    from etape2_rehash import compter_deplacements, taux_theorique

    _, taux_naif, _ = compter_deplacements(cles, n, n + 1)

    section("Comparaison : hash naïf vs anneau (N → N+1)")
    print()
    jauge_comparaison(
        "Hash naïf (modulo)",
        taux_naif * 100,
        "Anneau cohérent",
        taux * 100,
        unite=" %",
    )
    print()
    print(f"    Théorique naïf    : {taux_theorique(n)*100:.1f} %")
    print(f"    Théorique anneau  : ~{attendu*100:.1f} %  (≈ 1/(N+1))")
    print()

    # Mini illustration de l'arc qui bouge
    section("Principe : seul l'arc voisin bouge")
    print()
    print(c("      Avant ajout              Après ajout de D", C.DIM))
    print(c("         A                        A", C.CYAN))
    print(c("        ╱ ╲                      ╱ ╲", C.DIM))
    print(c("       C   B                    C   B", C.CYAN))
    print(c("        ╲ ╱                      ╲ ╱", C.DIM))
    print(
        c("         ·                        ", C.DIM)
        + c("D", C.YELLOW, C.BOLD)
        + c("  ← seul l'arc A→D change", C.YELLOW)
    )
    print()
    print(c("    Seules les clés de l'arc entre le prédécesseur et D", C.DIM))
    print(c("    sont réassignées. Le reste du keyspace est intact.", C.DIM))
    print()

    ok("Ajout/retrait ne touche que l'arc voisin (≈ K/N), pas tout le keyspace.")
    warn("Charge encore irrégulière avec peu de nœuds → étape 4 (vnodes).")
    info("Les vnodes sement plusieurs points par machine pour lisser les arcs.")
    print()


def main() -> None:
    afficher_demo(n=4, k=10_000)


if __name__ == "__main__":
    main()
