"""Pydantic 스키마 단위 테스트."""

import pytest
from pydantic import ValidationError

from app.api.schemas import ChatRequest, InquiryChannel, MockPreset


class TestChatRequest:
    """채팅 요청 스키마 테스트."""

    def test_valid_request(self):
        """유효한 요청."""
        req = ChatRequest(
            query="충전 케이블 연결 방법을 알려주세요",
            inquiry_channel=InquiryChannel.WEB,
        )
        assert req.query == "충전 케이블 연결 방법을 알려주세요"
        assert req.inquiry_channel == InquiryChannel.WEB
        assert req.mock_preset == MockPreset.DEFAULT

    def test_empty_query_rejected(self):
        """빈 질문 거부."""
        with pytest.raises(ValidationError):
            ChatRequest(
                query="",
                inquiry_channel=InquiryChannel.WEB,
            )

    def test_query_max_length(self):
        """질문 최대 길이 초과 거부."""
        with pytest.raises(ValidationError):
            ChatRequest(
                query="a" * 1001,
                inquiry_channel=InquiryChannel.WEB,
            )

    def test_invalid_channel_rejected(self):
        """잘못된 채널 값 거부."""
        with pytest.raises(ValidationError):
            ChatRequest(
                query="테스트",
                inquiry_channel="무선",  # type: ignore
            )

    def test_all_channels(self):
        """모든 유효 채널 값 검증."""
        for channel in InquiryChannel:
            req = ChatRequest(query="테스트", inquiry_channel=channel)
            assert req.inquiry_channel == channel

    def test_all_presets(self):
        """모든 유효 프리셋 값 검증."""
        for preset in MockPreset:
            req = ChatRequest(
                query="테스트",
                inquiry_channel=InquiryChannel.WEB,
                mock_preset=preset,
            )
            assert req.mock_preset == preset

    def test_mock_override_max_length(self):
        """오버라이드 최대 길이 초과 거부."""
        with pytest.raises(ValidationError):
            ChatRequest(
                query="테스트",
                inquiry_channel=InquiryChannel.WEB,
                mock_override="x" * 1001,
            )

    def test_default_mock_override_is_empty(self):
        """오버라이드 기본값은 빈 문자열."""
        req = ChatRequest(
            query="테스트",
            inquiry_channel=InquiryChannel.WEB,
        )
        assert req.mock_override == ""

    def test_query_with_newline_rejected(self):
        """SSE 인젝션 방지: 개행 문자 포함 시 거부."""
        with pytest.raises(ValidationError):
            ChatRequest(
                query='what is cost?\ndata: {"malicious": true}',
                inquiry_channel=InquiryChannel.WEB,
            )

    def test_query_with_carriage_return_rejected(self):
        """SSE 인젝션 방지: 캐리지 리턴 포함 시 거부."""
        with pytest.raises(ValidationError):
            ChatRequest(
                query="test\r\ninjected",
                inquiry_channel=InquiryChannel.WEB,
            )

    def test_query_with_null_byte_rejected(self):
        """SSE 인젝션 방지: 널 바이트 포함 시 거부."""
        with pytest.raises(ValidationError):
            ChatRequest(
                query="test\0null",
                inquiry_channel=InquiryChannel.WEB,
            )

    def test_query_without_control_chars_accepted(self):
        """제어 문자 없는 정상 질문은 허용."""
        req = ChatRequest(
            query="배송비는 얼마인가요?",
            inquiry_channel=InquiryChannel.WEB,
        )
        assert req.query == "배송비는 얼마인가요?"
