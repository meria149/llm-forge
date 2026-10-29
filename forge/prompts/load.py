"""Chargement des gabarits `forge/prompts/*.md` (bloc B1).

Un gabarit = front-matter YAML (id, version, modeles_testes, variables, score_moyen, notes)
+ un corps Markdown découpé en sections `## Titre` (Rôle, Tâche, Contexte, Contraintes,
Format, Critère de réussite, Exemple…).

    from forge.prompts import load_prompt
    p = load_prompt("resume-papier")
    texte = p.render(texte="...", public="...", longueur="150 mots")
    texte_sans_role = p.render(drop=["Rôle"], texte=..., ...)   # ablation

Seules les variables déclarées dans `variables` sont substituées (`{nom}`) : les autres
accolades (exemples JSON, code) restent intactes.
"""

from __future__ import annotations

import pathlib
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Iterable

import yaml

PROMPTS_DIR = pathlib.Path(__file__).resolve().parent
_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.S)
_SECTION = re.compile(r"^## +(.+?)\s*$", re.M)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s.strip().lower()


@dataclass
class Prompt:
    id: str
    meta: dict[str, Any]
    body: str
    path: pathlib.Path | None = None
    sections: list[tuple[str, str]] = field(default_factory=list)  # (titre, contenu)

    @property
    def variables(self) -> list[str]:
        return list(self.meta.get("variables") or [])

    def section_names(self) -> list[str]:
        return [t for t, _ in self.sections]

    def render(self, drop: Iterable[str] = (), **values: Any) -> str:
        """Rend le gabarit. `drop` = titres de sections à retirer (ablation, insensible aux accents)."""
        missing = [v for v in self.variables if v not in values]
        if missing:
            raise KeyError(f"Variables manquantes pour '{self.id}' : {missing}")
        dropped = {_norm(d) for d in drop}
        unknown = dropped - {_norm(t) for t in self.section_names()}
        if unknown:
            raise KeyError(f"Sections inconnues dans '{self.id}' : {sorted(unknown)}")
        if self.sections:
            head = self.body[: _SECTION.search(self.body).start()] if _SECTION.search(self.body) else ""
            parts = [head.rstrip()] if head.strip() else []
            for title, content in self.sections:
                if _norm(title) in dropped:
                    continue
                parts.append(f"## {title}\n{content.strip()}")
            text = "\n\n".join(parts)
        else:
            text = self.body
        for name in self.variables:
            text = text.replace("{" + name + "}", str(values[name]))
        return text.strip() + "\n"


def parse_prompt(raw: str, path: pathlib.Path | None = None) -> Prompt:
    m = _FM.match(raw)
    if not m:
        raise ValueError(f"Front-matter YAML absent : {path}")
    meta = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    matches = list(_SECTION.finditer(body))
    sections = []
    for i, mt in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections.append((mt.group(1), body[mt.end():end]))
    for key in ("id", "version", "variables"):
        if key not in meta:
            raise ValueError(f"Clé '{key}' manquante dans le front-matter de {path}")
    return Prompt(id=meta["id"], meta=meta, body=body, path=path, sections=sections)


def load_prompt(prompt_id: str, directory: pathlib.Path = PROMPTS_DIR) -> Prompt:
    path = directory / f"{prompt_id}.md"
    return parse_prompt(path.read_text(encoding="utf-8"), path)


def list_prompts(directory: pathlib.Path = PROMPTS_DIR) -> list[Prompt]:
    return [parse_prompt(p.read_text(encoding="utf-8"), p) for p in sorted(directory.glob("*.md"))
            if not p.name.startswith("_")]
