import json
import ssl
from dataclasses import dataclass
from urllib import error, request

import certifi

from app.core.config import settings
from app.db.models import IntegrationTable
from app.models.context import ContextBundleRecord
from app.services.integration_security_service import integration_security_service


@dataclass
class AgentProviderTurn:
    assistant_text: str
    external_session_ref: str | None = None


@dataclass
class AgentProviderStreamChunk:
    delta_text: str
    assistant_text: str
    external_session_ref: str | None = None
    done: bool = False


class AgentProviderService:
    def __init__(self) -> None:
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def start_session(
        self,
        integration: IntegrationTable,
        request_title: str,
        initial_prompt: str,
        transcript: list[dict[str, str]],
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ) -> AgentProviderTurn:
        provider = self._provider(integration)
        try:
            if provider == "openai":
                return self._openai_turn(integration, transcript, external_session_ref=None, context_bundle=context_bundle, available_tools=available_tools)
            if provider == "anthropic":
                return self._anthropic_turn(integration, transcript, external_session_ref=None, context_bundle=context_bundle, available_tools=available_tools)
            if provider == "microsoft":
                return self._microsoft_start_turn(integration, request_title, initial_prompt, context_bundle=context_bundle, available_tools=available_tools)
            return self._fallback_turn(integration.name, request_title, initial_prompt, context_bundle=context_bundle, available_tools=available_tools)
        except ValueError:
            if settings.agent_provider_fallback_mode == "simulate":
                return self._fallback_turn(integration.name, request_title, initial_prompt, context_bundle=context_bundle, available_tools=available_tools)
            raise

    def continue_session(
        self,
        integration: IntegrationTable,
        agent_label: str,
        transcript: list[dict[str, str]],
        latest_human_message: str,
        external_session_ref: str | None = None,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ) -> AgentProviderTurn:
        provider = self._provider(integration)
        try:
            if provider == "openai":
                return self._openai_turn(
                    integration,
                    transcript,
                    external_session_ref,
                    context_bundle=context_bundle,
                    available_tools=available_tools,
                )
            if provider == "anthropic":
                return self._anthropic_turn(
                    integration,
                    transcript,
                    external_session_ref,
                    context_bundle=context_bundle,
                    available_tools=available_tools,
                )
            if provider == "microsoft":
                return self._microsoft_continue_turn(
                    integration,
                    latest_human_message,
                    external_session_ref,
                    context_bundle=context_bundle,
                    available_tools=available_tools,
                )
            return self._fallback_continue_turn(
                agent_label,
                latest_human_message,
                external_session_ref,
                context_bundle=context_bundle,
                available_tools=available_tools,
            )
        except ValueError:
            if settings.agent_provider_fallback_mode == "simulate":
                return self._fallback_continue_turn(
                    agent_label,
                    latest_human_message,
                    external_session_ref,
                    context_bundle=context_bundle,
                    available_tools=available_tools,
                )
            raise

    def stream_start_session(
        self,
        integration: IntegrationTable,
        request_title: str,
        initial_prompt: str,
        transcript: list[dict[str, str]],
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ):
        provider = self._provider(integration)
        try:
            if provider == "openai":
                yield from self._openai_stream_turn(integration, transcript, external_session_ref=None, context_bundle=context_bundle, available_tools=available_tools)
                return
            if provider == "anthropic":
                yield from self._anthropic_stream_turn(integration, transcript, external_session_ref=None, context_bundle=context_bundle, available_tools=available_tools)
                return
            if provider == "microsoft":
                yield from self._microsoft_stream_start_turn(integration, request_title, initial_prompt, context_bundle=context_bundle, available_tools=available_tools)
                return
            yield from self._fallback_stream_turn(integration.name, request_title, initial_prompt, context_bundle=context_bundle, available_tools=available_tools)
        except ValueError:
            if settings.agent_provider_fallback_mode == "simulate":
                yield from self._fallback_stream_turn(integration.name, request_title, initial_prompt, context_bundle=context_bundle, available_tools=available_tools)
                return
            raise

    def stream_continue_session(
        self,
        integration: IntegrationTable,
        agent_label: str,
        transcript: list[dict[str, str]],
        latest_human_message: str,
        external_session_ref: str | None = None,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ):
        provider = self._provider(integration)
        try:
            if provider == "openai":
                yield from self._openai_stream_turn(
                    integration,
                    transcript,
                    external_session_ref,
                    context_bundle=context_bundle,
                    available_tools=available_tools,
                )
                return
            if provider == "anthropic":
                yield from self._anthropic_stream_turn(
                    integration,
                    transcript,
                    external_session_ref,
                    context_bundle=context_bundle,
                    available_tools=available_tools,
                )
                return
            if provider == "microsoft":
                yield from self._microsoft_stream_continue_turn(
                    integration,
                    latest_human_message,
                    external_session_ref,
                    context_bundle=context_bundle,
                    available_tools=available_tools,
                )
                return
            yield from self._fallback_stream_continue_turn(
                agent_label,
                latest_human_message,
                external_session_ref,
                context_bundle=context_bundle,
                available_tools=available_tools,
            )
        except ValueError:
            if settings.agent_provider_fallback_mode == "simulate":
                yield from self._fallback_stream_continue_turn(
                    agent_label,
                    latest_human_message,
                    external_session_ref,
                    context_bundle=context_bundle,
                    available_tools=available_tools,
                )
                return
            raise

    def _openai_turn(
        self,
        integration: IntegrationTable,
        transcript: list[dict[str, str]],
        external_session_ref: str | None = None,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ) -> AgentProviderTurn:
        api_key = integration_security_service.setting(integration, "api_key") or settings.agent_openai_api_key
        base_url = self._validated_provider_base_url(integration, settings.agent_openai_base_url, settings.integration_openai_allowed_hosts)
        model = self._setting(integration, "model") or settings.agent_openai_model
        if not api_key:
            return self._fallback_or_raise("OpenAI Codex")
        payload = {
            "model": model,
            "messages": self._contextualize_transcript(transcript, context_bundle, available_tools),
        }
        response = self._json_request(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            payload=payload,
        )
        choices = response.get("choices") or []
        content = ""
        if choices:
            message = choices[0].get("message") or {}
            raw_content = message.get("content")
            if isinstance(raw_content, str):
                content = raw_content
            elif isinstance(raw_content, list):
                parts = [item.get("text", "") for item in raw_content if isinstance(item, dict)]
                content = "".join(parts)
        if not content:
            raise ValueError("OpenAI adapter returned no assistant content")
        return AgentProviderTurn(assistant_text=content, external_session_ref=external_session_ref)

    def _openai_stream_turn(
        self,
        integration: IntegrationTable,
        transcript: list[dict[str, str]],
        external_session_ref: str | None = None,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ):
        api_key = integration_security_service.setting(integration, "api_key") or settings.agent_openai_api_key
        base_url = self._validated_provider_base_url(integration, settings.agent_openai_base_url, settings.integration_openai_allowed_hosts)
        model = self._setting(integration, "model") or settings.agent_openai_model
        if not api_key:
            yield from self._fallback_stream_turn("OpenAI Codex", "Governed Request", "Continue interactively")
            return
        payload = {
            "model": model,
            "messages": self._contextualize_transcript(transcript, context_bundle, available_tools),
            "stream": True,
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{base_url.rstrip('/')}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        full_text = ""
        try:
            with request.urlopen(req, context=self._ssl_context, timeout=300) as response:  # nosec B310 - provider base URL is validated against an allowlist
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    payload = json.loads(data)
                    choices = payload.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if isinstance(content, str) and content:
                        full_text += content
                        yield AgentProviderStreamChunk(
                            delta_text=content,
                            assistant_text=full_text,
                            external_session_ref=external_session_ref,
                        )
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ValueError(f"Provider request failed with {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise ValueError(f"Provider request failed: {exc.reason}") from exc
        if not full_text:
            raise ValueError("OpenAI adapter returned no assistant content")
        yield AgentProviderStreamChunk(
            delta_text="",
            assistant_text=full_text,
            external_session_ref=external_session_ref,
            done=True,
        )

    def _anthropic_turn(
        self,
        integration: IntegrationTable,
        transcript: list[dict[str, str]],
        external_session_ref: str | None = None,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ) -> AgentProviderTurn:
        api_key = integration_security_service.setting(integration, "api_key") or settings.agent_anthropic_api_key
        base_url = self._validated_provider_base_url(integration, settings.agent_anthropic_base_url, settings.integration_anthropic_allowed_hosts)
        model = self._setting(integration, "model") or settings.agent_anthropic_model
        if not api_key:
            return self._fallback_or_raise("Anthropic Claude Code")
        payload = {
            "model": model,
            "max_tokens": settings.agent_anthropic_max_tokens,
            "messages": self._contextualize_transcript(transcript, context_bundle, available_tools),
        }
        response = self._json_request(
            f"{base_url.rstrip('/')}/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            payload=payload,
        )
        parts = response.get("content") or []
        text_parts = [item.get("text", "") for item in parts if isinstance(item, dict) and item.get("type") == "text"]
        content = "".join(text_parts).strip()
        if not content:
            raise ValueError("Anthropic adapter returned no assistant content")
        return AgentProviderTurn(assistant_text=content, external_session_ref=external_session_ref)

    def _anthropic_stream_turn(
        self,
        integration: IntegrationTable,
        transcript: list[dict[str, str]],
        external_session_ref: str | None = None,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ):
        api_key = integration_security_service.setting(integration, "api_key") or settings.agent_anthropic_api_key
        base_url = self._validated_provider_base_url(integration, settings.agent_anthropic_base_url, settings.integration_anthropic_allowed_hosts)
        model = self._setting(integration, "model") or settings.agent_anthropic_model
        if not api_key:
            yield from self._fallback_stream_turn("Anthropic Claude Code", "Governed Request", "Continue interactively")
            return
        payload = {
            "model": model,
            "max_tokens": settings.agent_anthropic_max_tokens,
            "messages": self._contextualize_transcript(transcript, context_bundle, available_tools),
            "stream": True,
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{base_url.rstrip('/')}/messages",
            data=body,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        full_text = ""
        try:
            with request.urlopen(req, context=self._ssl_context, timeout=300) as response:  # nosec B310 - provider base URL is validated against an allowlist
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    payload = json.loads(data)
                    if payload.get("type") != "content_block_delta":
                        continue
                    delta = payload.get("delta") or {}
                    content = delta.get("text")
                    if isinstance(content, str) and content:
                        full_text += content
                        yield AgentProviderStreamChunk(
                            delta_text=content,
                            assistant_text=full_text,
                            external_session_ref=external_session_ref,
                        )
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ValueError(f"Provider request failed with {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise ValueError(f"Provider request failed: {exc.reason}") from exc
        if not full_text:
            raise ValueError("Anthropic adapter returned no assistant content")
        yield AgentProviderStreamChunk(
            delta_text="",
            assistant_text=full_text,
            external_session_ref=external_session_ref,
            done=True,
        )

    def _microsoft_start_turn(
        self,
        integration: IntegrationTable,
        request_title: str,
        initial_prompt: str,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ) -> AgentProviderTurn:
        token = integration_security_service.setting(integration, "access_token") or settings.agent_microsoft_copilot_token
        base_url = self._validated_provider_base_url(integration, settings.agent_microsoft_copilot_base_url, settings.integration_microsoft_allowed_hosts)
        if not token:
            return self._fallback_or_raise(integration.name)
        conversation = self._json_request(
            f"{base_url.rstrip('/')}/conversations",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            payload={},
        )
        conversation_id = str(
            conversation.get("id")
            or conversation.get("conversationId")
            or conversation.get("conversation_id")
            or ""
        )
        if not conversation_id:
            raise ValueError("Microsoft Copilot adapter did not return a conversation id")
        first_turn = self._microsoft_continue_turn(
            integration=integration,
            latest_human_message=self._contextualize_message(
                f"Request: {request_title}. {initial_prompt}",
                context_bundle,
                available_tools,
            ),
            external_session_ref=conversation_id,
            context_bundle=context_bundle,
            available_tools=available_tools,
        )
        return AgentProviderTurn(assistant_text=first_turn.assistant_text, external_session_ref=conversation_id)

    def _microsoft_stream_start_turn(
        self,
        integration: IntegrationTable,
        request_title: str,
        initial_prompt: str,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ):
        first_turn = self._microsoft_start_turn(
            integration,
            request_title,
            initial_prompt,
            context_bundle=context_bundle,
            available_tools=available_tools,
        )
        yield from self._chunk_text(first_turn.assistant_text, first_turn.external_session_ref)

    def _microsoft_continue_turn(
        self,
        integration: IntegrationTable,
        latest_human_message: str,
        external_session_ref: str | None,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ) -> AgentProviderTurn:
        token = integration_security_service.setting(integration, "access_token") or settings.agent_microsoft_copilot_token
        base_url = self._validated_provider_base_url(integration, settings.agent_microsoft_copilot_base_url, settings.integration_microsoft_allowed_hosts)
        if not token:
            return self._fallback_or_raise(integration.name)
        if not external_session_ref:
            raise ValueError("Microsoft Copilot session is missing an external conversation id")
        response = self._json_request(
            f"{base_url.rstrip('/')}/conversations/{external_session_ref}/chat",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            payload={
                "message": {
                    "role": "user",
                    "content": self._contextualize_message(latest_human_message, context_bundle, available_tools),
                }
            },
        )
        content = self._extract_microsoft_content(response)
        if not content:
            raise ValueError("Microsoft Copilot adapter returned no assistant content")
        return AgentProviderTurn(assistant_text=content, external_session_ref=external_session_ref)

    def _microsoft_stream_continue_turn(
        self,
        integration: IntegrationTable,
        latest_human_message: str,
        external_session_ref: str | None,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ):
        turn = self._microsoft_continue_turn(
            integration,
            latest_human_message,
            external_session_ref,
            context_bundle=context_bundle,
            available_tools=available_tools,
        )
        yield from self._chunk_text(turn.assistant_text, turn.external_session_ref)

    def _fallback_turn(
        self,
        integration_name: str,
        request_title: str,
        initial_prompt: str,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ) -> AgentProviderTurn:
        context_note = self._fallback_context_note(context_bundle, available_tools)
        return AgentProviderTurn(
            assistant_text=(
                f"{integration_name} session started for '{request_title}'. "
                f"I've received the initial assignment: {initial_prompt}. "
                "Before I proceed, confirm the desired output format, constraints, and any source-of-truth references I must follow."
                f"{context_note}"
            )
        )

    def _fallback_continue_turn(
        self,
        agent_label: str,
        latest_human_message: str,
        external_session_ref: str | None,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ) -> AgentProviderTurn:
        context_note = self._fallback_context_note(context_bundle, available_tools)
        return AgentProviderTurn(
            assistant_text=(
                f"{agent_label} received your guidance: {latest_human_message}. "
                "I can continue, but I may need another iterative response if constraints change or missing context is discovered."
                f"{context_note}"
            ),
            external_session_ref=external_session_ref,
        )

    def _fallback_stream_turn(
        self,
        integration_name: str,
        request_title: str,
        initial_prompt: str,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ):
        turn = self._fallback_turn(
            integration_name,
            request_title,
            initial_prompt,
            context_bundle=context_bundle,
            available_tools=available_tools,
        )
        yield from self._chunk_text(turn.assistant_text, turn.external_session_ref)

    def _fallback_stream_continue_turn(
        self,
        agent_label: str,
        latest_human_message: str,
        external_session_ref: str | None,
        context_bundle: ContextBundleRecord | None = None,
        available_tools: list[dict] | None = None,
    ):
        turn = self._fallback_continue_turn(
            agent_label,
            latest_human_message,
            external_session_ref,
            context_bundle=context_bundle,
            available_tools=available_tools,
        )
        yield from self._chunk_text(turn.assistant_text, turn.external_session_ref)

    def _fallback_or_raise(self, integration_name: str) -> AgentProviderTurn:
        if settings.agent_provider_fallback_mode == "simulate":
            return self._fallback_turn(integration_name, "Governed Request", "Continue interactively")
        raise ValueError(f"{integration_name} adapter is not configured")

    def _validated_provider_base_url(self, integration: IntegrationTable, default_base_url: str, allowed_hosts: list[str]) -> str:
        base_url = integration_security_service.setting(integration, "base_url") or default_base_url
        return integration_security_service.validate_outbound_target(
            base_url,
            allowed_hosts=allowed_hosts,
            allow_http_loopback=settings.integration_allow_http_loopback,
        )

    @staticmethod
    def _setting(integration: IntegrationTable, key: str) -> str | None:
        return integration_security_service.setting(integration, key)

    def _provider(self, integration: IntegrationTable) -> str | None:
        configured = self._setting(integration, "provider")
        if configured:
            return configured
        lowered = integration.name.lower()
        if "copilot" in lowered or "microsoft" in lowered:
            return "microsoft"
        if "codex" in lowered or "openai" in lowered:
            return "openai"
        if "claude" in lowered or "anthropic" in lowered:
            return "anthropic"
        return None

    @staticmethod
    def _extract_microsoft_content(response: dict) -> str:
        if isinstance(response.get("message"), dict):
            message = response["message"]
            if isinstance(message.get("content"), str):
                return message["content"]
            if isinstance(message.get("text"), str):
                return message["text"]
        for key in ("messages", "value"):
            items = response.get(key)
            if isinstance(items, list):
                for item in reversed(items):
                    if not isinstance(item, dict):
                        continue
                    role = str(item.get("role") or item.get("from") or "").lower()
                    if role not in {"assistant", "agent", "copilot", "bot"}:
                        continue
                    if isinstance(item.get("content"), str):
                        return item["content"]
                    if isinstance(item.get("text"), str):
                        return item["text"]
        return ""

    @staticmethod
    def _chunk_text(text: str, external_session_ref: str | None = None):
        words = text.split()
        full_text = ""
        for word in words:
            delta = word if not full_text else f" {word}"
            full_text += delta
            yield AgentProviderStreamChunk(
                delta_text=delta,
                assistant_text=full_text,
                external_session_ref=external_session_ref,
            )
        yield AgentProviderStreamChunk(
            delta_text="",
            assistant_text=full_text,
            external_session_ref=external_session_ref,
            done=True,
        )

    def _json_request(self, url: str, headers: dict[str, str], payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, context=self._ssl_context, timeout=60) as response:  # nosec B310 - provider base URL is validated against an allowlist
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ValueError(f"Provider request failed with {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise ValueError(f"Provider request failed: {exc.reason}") from exc

    def _contextualize_transcript(
        self,
        transcript: list[dict[str, str]],
        context_bundle: ContextBundleRecord | None,
        available_tools: list[dict] | None,
    ) -> list[dict[str, str]]:
        if context_bundle is None and not available_tools:
            return transcript
        return [{"role": "system", "content": self._build_context_instructions(context_bundle, available_tools)}, *transcript]

    def _contextualize_message(
        self,
        message: str,
        context_bundle: ContextBundleRecord | None,
        available_tools: list[dict] | None,
    ) -> str:
        instructions = self._build_context_instructions(context_bundle, available_tools)
        if not instructions:
            return message
        return f"{instructions}\n\nHuman guidance:\n{message}"

    def _build_context_instructions(
        self,
        context_bundle: ContextBundleRecord | None,
        available_tools: list[dict] | None,
    ) -> str:
        sections: list[str] = [
            "You are operating inside a governed agent session. Use only the authorized context and MCP capabilities below.",
            "Do not invent missing facts. If the governed context is insufficient, ask for clarification explicitly.",
        ]
        if context_bundle is not None:
            request_data = (context_bundle.contents or {}).get("request_data", {}) if isinstance(context_bundle.contents, dict) else {}
            workflow_state = (context_bundle.contents or {}).get("workflow_state", {}) if isinstance(context_bundle.contents, dict) else {}
            prior_decisions = (context_bundle.contents or {}).get("prior_decisions", []) if isinstance(context_bundle.contents, dict) else []
            relationship_graph = (context_bundle.contents or {}).get("relationship_graph", []) if isinstance(context_bundle.contents, dict) else []
            external_bindings = (context_bundle.contents or {}).get("external_bindings", []) if isinstance(context_bundle.contents, dict) else []
            sections.append(f"Context bundle id: {context_bundle.id} (version {context_bundle.version}, type {context_bundle.bundle_type}).")
            sections.append(
                "Governed request context: "
                + json.dumps(
                    {
                        "request_id": request_data.get("id"),
                        "title": request_data.get("title"),
                        "status": request_data.get("status"),
                        "priority": request_data.get("priority"),
                        "input_payload": request_data.get("input_payload", {}),
                        "workflow_state": workflow_state,
                        "prior_decision_count": len(prior_decisions),
                        "relationship_count": len(relationship_graph),
                        "external_bindings": external_bindings,
                    },
                    ensure_ascii=True,
                )
            )
            if context_bundle.policy_scope:
                sections.append(f"Policy scope: {json.dumps(context_bundle.policy_scope, ensure_ascii=True)}")
        if available_tools:
            tool_summary = [
                {
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "required_collaboration_mode": tool.get("required_collaboration_mode"),
                }
                for tool in available_tools
            ]
            sections.append(f"Authorized MCP capabilities: {json.dumps(tool_summary, ensure_ascii=True)}")
        return "\n".join(section for section in sections if section)

    def _fallback_context_note(self, context_bundle: ContextBundleRecord | None, available_tools: list[dict] | None) -> str:
        parts: list[str] = []
        if context_bundle is not None:
            parts.append(f" Governed context bundle {context_bundle.id} is attached.")
        if available_tools:
            parts.append(f" Authorized MCP capabilities: {', '.join(str(tool.get('name')) for tool in available_tools if tool.get('name'))}.")
        return "".join(parts)


agent_provider_service = AgentProviderService()
