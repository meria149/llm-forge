"""Tests sans réseau de la bibliothèque de gabarits (bloc B1)."""

from forge.prompts import list_prompts, load_prompt
from forge.prompts.load import parse_prompt

REQUIRED = {"id", "version", "modeles_testes", "variables", "score_moyen", "notes"}


def test_dix_gabarits_avec_front_matter_complet():
    prompts = list_prompts()
    assert len(prompts) >= 10
    for p in prompts:
        assert REQUIRED <= set(p.meta), p.id
        assert p.path.stem == p.id
        for v in p.variables:
            assert "{" + v + "}" in p.body, (p.id, v)


def test_render_substitue_et_garde_les_accolades_json():
    p = load_prompt("extraire-json")
    out = p.render(texte="DOC", schema="SCHEMA", consignes_champs="REGLES")
    assert "DOC" in out and "SCHEMA" in out and "REGLES" in out
    assert '{"projets": [' in out  # l'exemple JSON n'est pas interprété comme variable


def test_ablation_retire_une_section():
    p = load_prompt("resume-papier")
    vals = dict(texte="T", public="P", objectif="O", longueur="L")
    full = p.render(**vals)
    sans_role = p.render(drop=["role"], **vals)  # insensible aux accents
    assert "## Rôle" in full and "## Rôle" not in sans_role
    assert "## Tâche" in sans_role


def test_variable_manquante():
    p = parse_prompt("---\nid: x\nversion: 1\nvariables: [a]\n---\n## Tâche\n{a}\n")
    try:
        p.render()
    except KeyError:
        return
    raise AssertionError("KeyError attendu")
