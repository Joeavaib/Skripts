from __future__ import annotations

from collections.abc import Iterable, Mapping

from apps.api.app.settings import Settings, get_settings

DETERMINISTIC_FIELDS = {"is_external", "has_attachments", "vip_hit", "attachment_names"}


def _safe_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    return []


def _extract_domain(email: str) -> str | None:
    if "@" not in email:
        return None
    return email.rsplit("@", 1)[-1].strip().lower()


def _extract_emails(thread_payload: Mapping[str, object]) -> list[str]:
    emails: list[str] = []

    def append_if_email(value: object) -> None:
        if isinstance(value, str) and "@" in value:
            emails.append(value.strip().lower())

    participants = _safe_list(thread_payload.get("participants"))
    for participant in participants:
        if isinstance(participant, Mapping):
            append_if_email(participant.get("email"))
        else:
            append_if_email(participant)

    messages = _safe_list(thread_payload.get("messages"))
    for message in messages:
        if not isinstance(message, Mapping):
            continue
        append_if_email(message.get("from"))
        for key in ("to", "cc", "bcc"):
            for recipient in _safe_list(message.get(key)):
                if isinstance(recipient, Mapping):
                    append_if_email(recipient.get("email"))
                else:
                    append_if_email(recipient)

    # Preserve order while deduplicating.
    return list(dict.fromkeys(emails))


def _extract_attachment_names_from_list(raw_attachments: Iterable[object]) -> list[str]:
    names: list[str] = []
    for attachment in raw_attachments:
        if isinstance(attachment, Mapping):
            name = attachment.get("name") or attachment.get("filename")
        else:
            name = attachment

        if isinstance(name, str):
            stripped = name.strip()
            if stripped:
                names.append(stripped)

    return names


def _extract_attachment_names(thread_payload: Mapping[str, object]) -> list[str]:
    names = _extract_attachment_names_from_list(_safe_list(thread_payload.get("attachments")))

    for message in _safe_list(thread_payload.get("messages")):
        if isinstance(message, Mapping):
            names.extend(
                _extract_attachment_names_from_list(_safe_list(message.get("attachments")))
            )

    return list(dict.fromkeys(names))


def _is_external(emails: list[str], internal_domains: set[str]) -> bool:
    if not emails:
        return False

    for email in emails:
        domain = _extract_domain(email)
        if domain is None:
            continue
        if domain not in internal_domains:
            return True
    return False


def _vip_hit(emails: list[str], vip_list: set[str]) -> bool:
    if not emails or not vip_list:
        return False

    email_set = set(emails)
    domain_set = {domain for domain in (_extract_domain(email) for email in emails) if domain}

    for candidate in vip_list:
        normalized = candidate.lower().strip()
        if not normalized:
            continue
        if "@" in normalized:
            if normalized in email_set:
                return True
            continue

        if normalized.startswith("@"):
            normalized = normalized[1:]

        if normalized in domain_set:
            return True

    return False


def extract_deterministic_fields(
    thread_payload: Mapping[str, object],
    settings: Settings | None = None,
) -> dict[str, object]:
    resolved_settings = settings or get_settings()
    emails = _extract_emails(thread_payload)
    attachment_names = _extract_attachment_names(thread_payload)

    internal_domains = set(resolved_settings.internal_domain_allowlist)
    vip_list = set(resolved_settings.vip_list)

    return {
        "is_external": _is_external(emails, internal_domains),
        "has_attachments": bool(attachment_names),
        "vip_hit": _vip_hit(emails, vip_list),
        "attachment_names": attachment_names,
    }


def merge_thread_extraction(
    thread_payload: Mapping[str, object],
    llm_fields: Mapping[str, object] | None,
    settings: Settings | None = None,
) -> dict[str, object]:
    """Merge LLM extraction with deterministic fields.

    Deterministic fields always overwrite LLM supplied values.
    """

    merged = dict(llm_fields or {})
    merged.update(extract_deterministic_fields(thread_payload, settings=settings))
    return merged
