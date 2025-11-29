from langgraph.graph import StateGraph, END, START
from langchain_core.rate_limiters import InMemoryRateLimiter
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools import get_rendered_html, download_file, post_request, get_request, run_code, add_dependencies, transcribe_audio, analyze_with_gemini
from tools.aipipe_client import get_api_key, get_base_url
from typing import TypedDict, Annotated, List, Any
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
import os
from dotenv import load_dotenv
load_dotenv()

EMAIL = os.getenv("EMAIL")
SECRET = os.getenv("SECRET")
AIPIPE_API_KEY = get_api_key()  # Validates and gets Aipipe API key
AIPIPE_BASE_URL = get_base_url()
RECURSION_LIMIT = 5000
# -------------------------------------------------
# STATE
# -------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]


TOOLS = [run_code, get_rendered_html, download_file, post_request, get_request, add_dependencies, transcribe_audio, analyze_with_gemini]


# -------------------------------------------------
# AIPIPE/OPENROUTER LLM (Primary - for reasoning and code generation)
# -------------------------------------------------
rate_limiter = InMemoryRateLimiter(
    requests_per_second=9/60,  
    check_every_n_seconds=1,  
    max_bucket_size=9  
)
llm_aipipe = ChatOpenAI(
    model="openai/gpt-5-nano",  # Much cheaper than Claude (~60x cheaper!)
    openai_api_key=AIPIPE_API_KEY,
    openai_api_base=AIPIPE_BASE_URL,
    rate_limiter=rate_limiter
).bind_tools(TOOLS)

# -------------------------------------------------
# GEMINI LLM (Fallback - when Aipipe fails or rate limited)
# -------------------------------------------------
from langchain_google_genai import ChatGoogleGenerativeAI
import time

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    # Use rate limiter for Gemini too (15 RPM free tier = 1 request per 4 seconds)
    gemini_rate_limiter = InMemoryRateLimiter(
        requests_per_second=1/5,  # 1 request every 5 seconds (safer than 4)
        check_every_n_seconds=1,
        max_bucket_size=3
    )
    llm_gemini = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=GOOGLE_API_KEY,
        rate_limiter=gemini_rate_limiter,
        max_retries=5  # Retry up to 5 times on rate limit errors
    ).bind_tools(TOOLS)
else:
    llm_gemini = None

# Primary LLM (will fallback to Gemini on errors)
llm = llm_aipipe   


# -------------------------------------------------
# SYSTEM PROMPT
# -------------------------------------------------
SYSTEM_PROMPT = f"""
You are an autonomous quiz-solving agent with DUAL AI CAPABILITIES + AUTOMATIC FALLBACK.

YOUR ARCHITECTURE:
- YOU (Primary: Aipipe/OpenRouter openai gpt-5-nano): Handle reasoning, code generation, text analysis
- FALLBACK (Gemini): Automatically takes over if Aipipe hits rate/token limits
- GEMINI TOOLS (via tools): Handle multimodal tasks (audio, images, videos, PDFs)

Your job is to:
1. Load the quiz page from the given URL.
2. Extract ALL instructions, required parameters, submission rules, and the submit endpoint.
3. Solve the task exactly as required (choose the right tool/capability automatically).
4. Submit the answer ONLY to the endpoint specified to post or submit on the current page (never make up URLs ) 
5. Read the server response and:
   - If it contains a new quiz URL → fetch it immediately and continue.
   - If no new URL is present → return "END".

STRICT RULES — FOLLOW EXACTLY:

GENERAL RULES:
- NEVER stop early. Continue solving tasks until no new URL is provided.
- NEVER hallucinate URLs, endpoints, fields, values, or JSON structure.
- NEVER shorten or modify URLs. Always submit the full URL.
- NEVER get stuck in loops - if you've tried the same approach twice and it failed, CHANGE YOUR STRATEGY.
- ALWAYS inspect the server response before deciding what to do next.
- ALWAYS use the tools provided to fetch, scrape, download, render HTML, audio transcription, or send requests.
- If you receive an error response, READ THE ERROR MESSAGE and adjust your approach accordingly.
- When you encounter relative URLs in HTML (like src="file.mp3"), construct the full absolute URL correctly based on the page URL.

INTELLIGENT TOOL SELECTION (YOU choose automatically based on task):

WHEN TO USE GEMINI TOOLS (for things you CAN'T do):
- Audio files (.mp3, .wav, etc.) → 'transcribe_audio'
- Images (.png, .jpg, charts, graphs) → 'analyze_with_gemini'
- Videos (.mp4, .webm, etc.) → 'analyze_with_gemini'
- PDFs (text extraction) → 'analyze_with_gemini'
- Any visual/audio content you can't process → 'analyze_with_gemini'

WHEN TO USE YOUR OWN CAPABILITIES (Aipipe - things you CAN do):
- Text reasoning and analysis (you're great at this!)
- Math calculations and logic
- Code generation (Python, etc.)
- Planning and decision-making
- JSON/data parsing and manipulation

WHEN TO USE PYTHON EXECUTION TOOLS (for computational tasks):
- Data analysis: 'run_code' with pandas/numpy
- Visualization: 'run_code' with matplotlib/plotly (save to files)
- Statistical analysis: 'run_code' with scipy/statsmodels
- ML models: 'add_dependencies' first, then 'run_code' with scikit-learn
- Geo-spatial: 'add_dependencies' (geopandas), then 'run_code'
- Network analysis: 'add_dependencies' (networkx), then 'run_code'

OTHER TOOLS:
- Web scraping (JavaScript sites): 'get_rendered_html'
- API calls with headers: 'get_request' (GET) or 'post_request' (POST)
- Download files: 'download_file'
- Install packages: 'add_dependencies'

KEY INSIGHT: You have unlimited capabilities through tools!
- Can't see/hear? → Use Gemini tools
- Need to process data? → Write Python code with run_code
- Need a library? → Install it with add_dependencies
- YOU orchestrate everything intelligently!

TIME LIMIT RULES:
- Each quiz has a hard 3-minute limit.
- The server response includes a "delay" field indicating elapsed time.
- If your answer is wrong, retry again (if time permits).
- If time exceeds 3 minutes, try new quiz URL if provided otherwise stop.

STOPPING CONDITION:
- Only return "END" when a server response explicitly contains NO new URL.
- DO NOT return END under any other condition.

CRITICAL PAYLOAD RULES:
When you submit an answer, the payload "url" field MUST be a FULL URL, not a relative path.
answer should be in exact type (e.g. string, int, json object) as required by the server.

IMPORTANT: ALWAYS INCLUDE THE FOLLOWING IN EVERY SUBMISSION PAYLOAD:
- Your answer in the required format.
- The FULL URL of the current quiz page in the "url" field.
- secret and email for authentication.

ADDITIONAL INFORMATION YOU MUST INCLUDE WHEN REQUIRED:
- Email: {EMAIL}
- Secret: {SECRET}

YOUR JOB:
- Follow pages exactly.
- Extract data reliably.
- Choose the right tool/capability automatically.
- Never guess.
- Submit correct answers.
- Continue until no new URL.
- Then respond with: END
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages")
])

llm_with_prompt = prompt | llm


# -------------------------------------------------
# AGENT NODE (with automatic fallback)
# -------------------------------------------------
def agent_node(state: AgentState):
    """Agent node with automatic Aipipe → Gemini fallback on errors."""
    try:
        # Try Aipipe first
        result = llm_with_prompt.invoke({"messages": state["messages"]})
        return {"messages": state["messages"] + [result]}
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check if it's a rate limit or token limit error
        is_rate_limit = any(x in error_msg for x in [
            'rate limit', 'rate_limit', 'ratelimit',
            'too many requests', '429',
            'quota', 'limit exceeded', 'token limit'
        ])
        
        # If rate limited and Gemini is available, fallback to Gemini
        if is_rate_limit and llm_gemini is not None:
            print("\n⚠️  Aipipe rate limit - switching to Gemini (no wait, time is critical)...")
            
            try:
                # Create Gemini version of the prompt
                gemini_prompt = ChatPromptTemplate.from_messages([
                    ("system", llm_with_prompt.first.messages[0].prompt.template),
                    MessagesPlaceholder(variable_name="messages")
                ])
                llm_gemini_with_prompt = gemini_prompt | llm_gemini
                
                result = llm_gemini_with_prompt.invoke({"messages": state["messages"]})
                print("✅ Gemini succeeded")
                return {"messages": state["messages"] + [result]}
            except Exception as gemini_error:
                gemini_error_msg = str(gemini_error).lower()
                
                # If Gemini also rate limited, wait minimal time and retry once
                if '429' in gemini_error_msg or 'resource exhausted' in gemini_error_msg:
                    print(f"⚠️  Gemini also rate limited - waiting 2s for quick retry...")
                    time.sleep(2)  # Minimal wait to respect rate limit
                    
                    try:
                        result = llm_gemini_with_prompt.invoke({"messages": state["messages"]})
                        print("✅ Gemini retry successful")
                        return {"messages": state["messages"] + [result]}
                    except Exception as retry_error:
                        print(f"❌ Both APIs exhausted - cannot proceed")
                        raise
                else:
                    print(f"❌ Gemini fallback failed: {gemini_error}")
                    raise
        else:
            # Re-raise if not rate limit or Gemini not available
            print(f"❌ Aipipe error (no fallback): {e}")
            raise


# -------------------------------------------------
# GRAPH
# -------------------------------------------------
def route(state):
    last = state["messages"][-1]
    # support both objects (with attributes) and plain dicts
    tool_calls = None
    if hasattr(last, "tool_calls"):
        tool_calls = getattr(last, "tool_calls", None)
    elif isinstance(last, dict):
        tool_calls = last.get("tool_calls")

    if tool_calls:
        return "tools"
    # get content robustly
    content = None
    if hasattr(last, "content"):
        content = getattr(last, "content", None)
    elif isinstance(last, dict):
        content = last.get("content")

    if isinstance(content, str) and content.strip() == "END":
        return END
    if isinstance(content, list) and content[0].get("text").strip() == "END":
        return END
    return "agent"
graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(TOOLS))



graph.add_edge(START, "agent")
graph.add_edge("tools", "agent")
graph.add_conditional_edges(
    "agent",    
    route       
)

app = graph.compile()


# -------------------------------------------------
# RUN AGENT
# -------------------------------------------------
def run_agent(url: str) -> str:
    """Run the agent on a quiz URL until completion.
    
    The agent will continue solving quizzes until no new URL is found.
    When complete, it prints a summary and returns the final state.
    """
    print(f"\n{'='*60}")
    print(f"🚀 STARTING QUIZ AGENT")
    print(f"{'='*60}")
    print(f"Initial URL: {url}\n")
    
    final_state = app.invoke({
        "messages": [{"role": "user", "content": url}]},
        config={"recursion_limit": RECURSION_LIMIT},
    )
    
    print(f"\n{'='*60}")
    print(f"✅ ALL QUIZZES COMPLETED!")
    print(f"{'='*60}")
    print(f"Status: Agent returned 'END' - no more quiz URLs found")
    print(f"Total messages exchanged: {len(final_state.get('messages', []))}")
    print(f"{'='*60}\n")
    
    return final_state

