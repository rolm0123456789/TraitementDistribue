#!/usr/bin/env python3
"""Utilitaires d'affichage terminal pour les démos du TP2 (hashage)."""

from __future__ import annotations

import math
import shutil
import sys
from collections.abc import Sequence

# Force stdout/stderr to UTF-8 to handle box-drawing, emojis, and accents on Windows/all platforms
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Couleurs ANSI ────────────────────────────────────────────────────────────

_USE_COLOR = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


class C:
    RESET = "\033[0m" if _USE_COLOR else ""
    BOLD = "\033[1m" if _USE_COLOR else ""
    DIM = "\033[2m" if _USE_COLOR else ""
    RED = "\033[91m" if _USE_COLOR else ""
    GREEN = "\033[92m" if _USE_COLOR else ""
    YELLOW = "\033[93m" if _USE_COLOR else ""
    BLUE = "\033[94m" if _USE_COLOR else ""
    MAGENTA = "\033[95m" if _USE_COLOR else ""
    CYAN = "\033[96m" if _USE_COLOR else ""
    WHITE = "\033[97m" if _USE_COLOR else ""
    GRAY = "\033[90m" if _USE_COLOR else ""


_NODE_COLORS = [C.CYAN, C.GREEN, C.YELLOW, C.MAGENTA, C.BLUE, C.RED, C.WHITE]


def couleur_noeud(index: int) -> str:
    return _NODE_COLORS[index % len(_NODE_COLORS)]


def c(text: str, *styles: str) -> str:
    if not styles or not _USE_COLOR:
        return text
    return "".join(styles) + text + C.RESET


# ── Cadres & titres ──────────────────────────────────────────────────────────

def titre(texte: str, sous: str = "") -> None:
    largeur = min(72, max(60, shutil.get_terminal_size((72, 24)).columns - 2))
    print()
    print(c("╔" + "═" * (largeur - 2) + "╗", C.BOLD, C.CYAN))
    print(c("║", C.BOLD, C.CYAN) + c(f"  {texte}".ljust(largeur - 2), C.BOLD) + c("║", C.BOLD, C.CYAN))
    if sous:
        print(c("║", C.BOLD, C.CYAN) + c(f"  {sous}".ljust(largeur - 2), C.DIM) + c("║", C.BOLD, C.CYAN))
    print(c("╚" + "═" * (largeur - 2) + "╝", C.BOLD, C.CYAN))
    print()


def section(texte: str) -> None:
    print(c(f"  ▸ {texte}", C.BOLD, C.BLUE))
    print(c("  " + "─" * 56, C.DIM))


def ok(texte: str) -> None:
    print(c(f"  ✓ {texte}", C.GREEN))


def warn(texte: str) -> None:
    print(c(f"  ! {texte}", C.YELLOW))


def info(texte: str) -> None:
    print(c(f"  → {texte}", C.CYAN))


def event(texte: str) -> None:
    print(c(f"  ◆ {texte}", C.BOLD, C.MAGENTA))


# ── Barres ───────────────────────────────────────────────────────────────────

def barre(valeur: float, maximum: float, largeur: int = 28, color: str = C.CYAN) -> str:
    if maximum <= 0:
        return ""
    n = max(0, min(largeur, int(round(valeur / maximum * largeur))))
    return c("█" * n, color) + c("░" * (largeur - n), C.DIM)


def barre_pct(pct: float, largeur: int = 30, color: str = C.CYAN) -> str:
    return barre(pct, 100.0, largeur, color)


# ── Cercle / anneau ASCII ────────────────────────────────────────────────────

def _angle_vers_xy(angle: float, cx: float, cy: float, rx: float, ry: float) -> tuple[float, float]:
    """angle en radians, 0 = haut (12h), sens horaire."""
    x = cx + rx * math.sin(angle)
    y = cy - ry * math.cos(angle)
    return x, y


def dessiner_cercle(
    points: Sequence[tuple[float, str, str | None]],
    *,
    ring_size: int = 2**32,
    titre_cercle: str = "Anneau de hachage [0, 2³²)",
    rayon: int = 11,
    legende: Sequence[tuple[str, str, str]] | None = None,
    cles_echantillon: Sequence[tuple[float, str]] | None = None,
    labels_exterieurs: bool = True,
) -> None:
    """
    Dessine un vrai cercle ASCII avec des points positionnés angulairement.

    points : liste de (position_sur_anneau, symbole, couleur)
    cles_echantillon : (position, symbole) pour marquer des clés
    """
    # Aspect ratio ~2 (caractères plus hauts que larges)
    rx = float(rayon * 2)
    ry = float(rayon)
    # Marge pour labels extérieurs
    pad = 6 if labels_exterieurs else 2
    width = int(rx * 2 + pad * 2 + 3)
    height = int(ry * 2 + pad + 3)
    cx = width / 2.0
    cy = height / 2.0

    grid: list[list[str]] = [[" " for _ in range(width)] for _ in range(height)]
    colors: list[list[str | None]] = [[None for _ in range(width)] for _ in range(height)]
    # Priorité : 0=vide, 1=contour, 2=clé, 3=nœud, 4=label
    prio: list[list[int]] = [[0 for _ in range(width)] for _ in range(height)]

    def put(x: float, y: float, ch: str, col: str | None = None, priority: int = 1) -> None:
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < width and 0 <= yi < height and priority >= prio[yi][xi]:
            grid[yi][xi] = ch
            colors[yi][xi] = col
            prio[yi][xi] = priority

    # 1) Contour du cercle (ellipse)
    for i in range(0, 360, 2):
        a = math.radians(i)
        x, y = _angle_vers_xy(a, cx, cy, rx, ry)
        put(x, y, "·", C.DIM, 1)

    # 2) Ticks cardinaux (0, ¼, ½, ¾)
    for frac in (0.0, 0.25, 0.5, 0.75):
        a = frac * 2 * math.pi
        x1, y1 = _angle_vers_xy(a, cx, cy, rx * 0.90, ry * 0.90)
        x2, y2 = _angle_vers_xy(a, cx, cy, rx * 1.00, ry * 1.00)
        put(x1, y1, "│" if frac in (0.0, 0.5) else "─", C.GRAY, 2)
        put(x2, y2, "│" if frac in (0.0, 0.5) else "─", C.GRAY, 2)

    # 3) Clés échantillon (anneau intérieur)
    if cles_echantillon:
        for pos, _sym in cles_echantillon:
            angle = (pos % ring_size) / ring_size * 2 * math.pi
            x, y = _angle_vers_xy(angle, cx, cy, rx * 0.78, ry * 0.78)
            put(x, y, "∙", C.GRAY, 2)

    # 4) Nœuds sur le cercle (●) + label lettre à l'extérieur
    for pos, sym, col in points:
        angle = (pos % ring_size) / ring_size * 2 * math.pi
        x, y = _angle_vers_xy(angle, cx, cy, rx, ry)
        # Point sur l'anneau
        marker = "★" if sym == "★" else "●"
        put(x, y, marker, col, 4)

        if labels_exterieurs:
            # Label à l'extérieur (lettre ou ★)
            lx, ly = _angle_vers_xy(angle, cx, cy, rx + 3.5, ry + 1.8)
            put(lx, ly, sym, col, 5)

    # 5) Centre (positions entières pour éviter les collisions de round half-even)
    icx, icy = int(round(cx)), int(round(cy))
    put(float(icx), float(icy), "↻", C.DIM, 3)
    label_c = "horaire"
    start_x = icx - len(label_c) // 2
    for i, ch in enumerate(label_c):
        put(float(start_x + i), float(icy + 1), ch, C.DIM, 3)

    # Marqueurs 0 / ½ en texte
    put(cx, cy - ry - 1.5, "0", C.DIM, 2)
    put(cx, cy + ry + 1.5, "½", C.DIM, 2)

    # Rendu
    print(c(f"  {titre_cercle}", C.BOLD))
    print()
    for y in range(height):
        parts: list[str] = []
        # trim trailing spaces for cleaner look but keep structure
        row = grid[y]
        last = width - 1
        while last > 0 and row[last] == " ":
            last -= 1
        for x in range(last + 1):
            ch = grid[y][x]
            col = colors[y][x]
            if ch == " ":
                parts.append(" ")
            elif col:
                bold = C.BOLD if prio[y][x] >= 4 else ""
                parts.append(c(ch, col, bold) if bold else c(ch, col))
            else:
                parts.append(ch)
        print("  " + "".join(parts))

    if legende:
        print()
        print(c("  Légende :", C.DIM))
        for sym, label, col in legende:
            print(f"    {c(sym, col, C.BOLD)}  {label}")


def dessiner_anneau_noeuds(
    positions: Sequence[tuple[int, str]],
    *,
    ring_size: int = 2**32,
    charges: dict[str, int] | None = None,
    total_cles: int = 0,
    cles_pos: Sequence[int] | None = None,
    nouveau: str | None = None,
    titre_cercle: str = "Répartition sur l'anneau",
) -> None:
    """Affiche l'anneau avec les nœuds positionnés + légende des charges."""
    noms: list[str] = []
    for _, nom in positions:
        if nom not in noms:
            noms.append(nom)

    points = []
    legende = []
    for pos, nom in positions:
        idx = noms.index(nom)
        col = couleur_noeud(idx)
        if nouveau and nom == nouveau:
            sym = "★"
        else:
            sym = chr(ord("A") + idx) if idx < 26 else "●"
        points.append((float(pos), sym, col))

        charge_txt = ""
        if charges is not None:
            ch = charges.get(nom, 0)
            pct = (ch / total_cles * 100) if total_cles else 0
            charge_txt = f"  ·  {ch} clés ({pct:.1f} %)"
        pos_pct = pos / ring_size * 100
        marque = c("  ← NOUVEAU", C.YELLOW, C.BOLD) if nouveau and nom == nouveau else ""
        legende.append((sym, f"{nom}  @ {pos_pct:5.1f} %{charge_txt}{marque}", col))

    echantillon = None
    if cles_pos:
        echantillon = [(float(p), "∙") for p in cles_pos[:80]]

    dessiner_cercle(
        points,
        ring_size=ring_size,
        titre_cercle=titre_cercle,
        rayon=11,
        legende=legende,
        cles_echantillon=echantillon,
        labels_exterieurs=True,
    )


def jauge_comparaison(label_a: str, val_a: float, label_b: str, val_b: float, unite: str = "%") -> None:
    m = 100.0 if unite.strip() == "%" else max(val_a, val_b, 1)
    print(f"    {c(label_a.ljust(18), C.RED)} {barre(val_a, m, 28, C.RED)}  {val_a:.1f}{unite}")
    print(f"    {c(label_b.ljust(18), C.GREEN)} {barre(val_b, m, 28, C.GREEN)}  {val_b:.1f}{unite}")


def tableau(headers: Sequence[str], rows: Sequence[Sequence[str]], aligns: str | None = None) -> None:
    aligns = aligns or ("l" * len(headers))
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            # largeur sans codes ANSI
            plain = _strip_ansi(str(cell))
            widths[i] = max(widths[i], len(plain))

    def fmt(cell: str, i: int) -> str:
        plain = _strip_ansi(str(cell))
        pad = widths[i] - len(plain)
        if aligns[i] == "r":
            return " " * pad + str(cell)
        return str(cell) + " " * pad

    head = "  " + " │ ".join(c(fmt(h, i), C.BOLD) for i, h in enumerate(headers))
    sep = "  " + "─┬─".join("─" * w for w in widths)
    print(head)
    print(c(sep, C.DIM))
    for row in rows:
        print("  " + " │ ".join(fmt(str(cell), i) for i, cell in enumerate(row)))


def _strip_ansi(s: str) -> str:
    import re
    return re.sub(r"\033\[[0-9;]*m", "", s)
