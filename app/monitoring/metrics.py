"""Prometheus metrics collection.

All metric names use 'cs_agent_' prefix for namespace consistency.
"""

from prometheus_client import Counter, Histogram, Gauge

# --- Counters ---

REQUEST_COUNT = Counter(
    "cs_agent_requests_total",
    "Total requests processed",
    ["method", "endpoint", "status"],
)

chat_requests_total = Counter(
    "cs_agent_chat_requests_total",
    "Total chat requests",
    ["channel", "process_type"],
)

auto_processed_total = Counter(
    "cs_agent_auto_processed_total",
    "Total auto-processed inquiries",
    ["category"],
)

escalation_total = Counter(
    "cs_agent_escalation_total",
    "Total escalated inquiries",
    ["category"],
)

classification_total = Counter(
    "cs_agent_classification_total",
    "Total classification requests",
    ["complexity", "category"],
)

cost_saved_total = Counter(
    "cs_agent_cost_saved_total",
    "Total cost saved (won)",
)

# --- Histograms ---

REQUEST_LATENCY = Histogram(
    "cs_agent_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
)

response_time_seconds = Histogram(
    "cs_agent_response_time_seconds",
    "Response time in seconds",
    ["process_type"],
)

faq_search_duration_seconds = Histogram(
    "cs_agent_faq_search_duration_seconds",
    "FAQ search latency in seconds",
)

# --- Gauges ---

AUTO_RATE_GAUGE = Gauge(
    "cs_agent_auto_rate",
    "Auto-processing rate (%)",
)

ESCALATION_RATE_GAUGE = Gauge(
    "cs_agent_escalation_rate",
    "Escalation rate (%)",
)

FAQ_COUNT_GAUGE = Gauge(
    "cs_agent_faq_count",
    "FAQ knowledge base size",
)

daily_saved_cost = Gauge(
    "cs_agent_daily_saved_cost",
    "Daily saved cost (won)",
)
