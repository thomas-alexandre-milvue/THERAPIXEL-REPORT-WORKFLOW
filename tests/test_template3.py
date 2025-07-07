import pathlib
import convert_docx_to_md as conv

HERE = pathlib.Path(__file__).parent
DOCX = (
    HERE.parent
    / "3. Report Generator"
    / "b. Templates"
    / "DOCX Source"
    / "TEMPLATE 3 - BILAN SENOLOGIQUE SUSPECT.docx"
)
EXPECTED = HERE / "expected_template3.md"


def test_template3_conversion(tmp_path):
    """Template-3 converts byte-for-byte to the expected Markdown."""
    produced = conv.convert(str(DOCX))

    # 1️⃣  Byte-for-byte equality
    expected_text = EXPECTED.read_text(encoding="utf-8")
    assert produced == expected_text

    # 2️⃣  Sanity-check a couple of critical accents
    for needle in ("BILAN SÉNOLOGIQUE", "Échographie", "dépistage"):
        assert needle in produced, f"Missing accent-ed word: {needle}"

    # 3️⃣  Ensure no escaped brackets slipped through
    assert r"\[" not in produced and r"\]" not in produced
