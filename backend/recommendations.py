"""
GROQ-based recommendation generator for alerts.
"""
import json
from .llm_client import get_groq_client

MODEL = "llama-3.1-8b-instant"  # fast + concise for runbooks

SYSTEM = (
    "You are a telecom reliability SRE assistant. Be short, specific, and actionable. "
    "Output a one-sentence hypothesis, then 3–5 numbered steps. Prefer steps on RAN, PRB/throughput, QoS, backhaul, paging, and customer comms."
)

FALLBACK = (
    "Hypothesis: CHI drop likely due to congestion or partial outage across one or more cells.\n"
    "1) Inspect top PRB/throughput offenders; rebalance traffic.\n"
    "2) Verify backhaul and core KPIs; reroute if saturation detected.\n"
    "3) Push customer SMS with ETA + mitigations.\n"
    "4) Temporarily raise QoS for critical services; throttle background traffic.\n"
    "5) Open/attach incident and assign on-call for triage within 30 min."
)


def groq_recommendations(context: dict) -> str:
    """
    Generate recommendations using GROQ.
    
    context example:
    {
      'region': 'Dallas',
      'current_chi': 36.4,
      'prev_chi': 70.6,
      'topics': ['outage','down','slow'],
      'kpi': {'latency_ms': 180, 'throughput_mbps': 4.2, 'prb_util': 0.92},
      'time': '2025-11-09 17:28'
    }
    """
    client = get_groq_client()
    
    # Format context nicely for the prompt
    context_str = f"""Region: {context.get('region', 'Unknown')}
Current CHI: {context.get('current_chi', 0):.1f}
Previous CHI: {context.get('prev_chi', 'N/A')}
Topics: {', '.join(context.get('topics', [])) if context.get('topics') else 'None specified'}
KPI Data: {json.dumps(context.get('kpi', {}), indent=2)}
Time: {context.get('time', 'N/A')}"""
    
    prompt = (
        "Generate cause + steps for the incident below.\n"
        "Return:\n"
        "Hypothesis: <one sentence>\n"
        "1) <step>\n2) <step>\n3) <step>\n4) <step> (optional)\n5) <step> (optional)\n\n"
        f"Incident Details:\n{context_str}"
    )
    resp = client.chat.completions.create(
        model=MODEL, 
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}
        ]
    )
    return resp.choices[0].message.content.strip()


def get_recommendations(context: dict) -> tuple[str, str]:
    """
    Returns (text, source) where source ∈ {'groq','fallback'}.
    """
    try:
        text = groq_recommendations(context)
        # Validate that we got actual content (not empty)
        if text and len(text.strip()) > 10:
            return text, "groq"
        else:
            print(f"[DEBUG] GROQ returned empty/invalid response, using fallback")
            return FALLBACK, "fallback"
    except Exception as e:
        import traceback
        print(f"[DEBUG] GROQ recommendations failed: {e}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return FALLBACK, "fallback"

