"""Email-parsing subpackage.

Each module owns one slice of turning a raw RFC 5322 message into a typed
`ParsedEmail`: addresses/headers, authentication results, URLs, attachments, and
bodies. `parser.EmailParserService` composes them. Splitting it this way keeps
every piece independently testable and small enough to reason about.
"""

from app.services.parsing.parser import EmailParserService

__all__ = ["EmailParserService"]
