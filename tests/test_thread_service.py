from apps.api.app.settings import Settings
from apps.api.app.threads.service import extract_deterministic_fields, merge_thread_extraction


def test_is_external_false_when_all_domains_internal() -> None:
    payload = {
        "participants": [
            {"email": "alice@internal.test"},
            {"email": "bob@corp.local"},
        ]
    }
    settings = Settings(internal_domain_allowlist=("internal.test", "corp.local"))

    result = extract_deterministic_fields(payload, settings=settings)

    assert result["is_external"] is False


def test_is_external_true_when_any_domain_external() -> None:
    payload = {
        "participants": [
            {"email": "alice@internal.test"},
            {"email": "vendor@example.org"},
        ]
    }
    settings = Settings(internal_domain_allowlist=("internal.test",))

    result = extract_deterministic_fields(payload, settings=settings)

    assert result["is_external"] is True


def test_attachment_extraction_and_flag() -> None:
    payload = {
        "attachments": [{"name": "contract.pdf"}],
        "messages": [
            {
                "attachments": [
                    {"filename": "  screenshot.png  "},
                    "contract.pdf",
                    "",
                ]
            }
        ],
    }

    result = extract_deterministic_fields(payload, settings=Settings())

    assert result["has_attachments"] is True
    assert result["attachment_names"] == ["contract.pdf", "screenshot.png"]


def test_vip_matching_for_email_and_domain() -> None:
    payload = {
        "messages": [
            {
                "from": "ceo@vip.example",
                "to": ["staff@internal.test"],
                "cc": [{"email": "board.member@company.tld"}],
            }
        ]
    }
    settings = Settings(vip_list=("ceo@vip.example", "@company.tld"))

    result = extract_deterministic_fields(payload, settings=settings)

    assert result["vip_hit"] is True


def test_deterministic_fields_override_llm_values() -> None:
    payload = {
        "participants": ["employee@internal.test", "partner@external.test"],
        "attachments": ["agenda.docx"],
    }
    settings = Settings(internal_domain_allowlist=("internal.test",), vip_list=("ceo@corp.local",))

    llm_fields = {
        "summary": "hello",
        "is_external": False,
        "has_attachments": False,
        "vip_hit": True,
        "attachment_names": [],
    }

    merged = merge_thread_extraction(payload, llm_fields, settings=settings)

    assert merged["summary"] == "hello"
    assert merged["is_external"] is True
    assert merged["has_attachments"] is True
    assert merged["vip_hit"] is False
    assert merged["attachment_names"] == ["agenda.docx"]
