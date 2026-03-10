from datetime import datetime


def search_query(query: str) -> str:
    current_month_year = datetime.now().strftime("%B %Y")
    prompt = f"""You are a helpful research assistant who is helping with literature review of a research idea. You will be provided with an search keyword from the user. Your task is to frame queries that would be used to search an academic search engine (semantic scholar)and retrieve relevant papers.

    it's currently {current_month_year}

    Here is the query:
    {query}
    ## Instruction:
    * Each query should not be more than 5 keywords. Please write the query in a similar fashion as a human would use search engine.
    * Please generate 5 search queries.
    * Please make sure to generate different search queries using a variety of key words so as to get maximum papers that could be cited.
    * In addition to the queries, also provide a reasoning for the generated queries.
    * Extract the relevant sentences from the abstract that justify your reasoning.
    * Put the extracted sentences in quotes and put them at the end of each of your reasonings.
    * Example reasoning:
    "The query is framed to get papers that discuss the method proposed in the abstract. The sentence 'The method proposed in this paper is similar to the one proposed in the query abstract.' is extracted from the abstract."
    * Please return a JSON with a key "queries" that has the list of queries and a "reasoning" key that has the reasoning for the queries.
    * Do not generate anything else apart from the JSON.
    * Use the web to search 

    ### Response:"""
    return prompt


def retrieval_summary_prompt(user_query: str, context_str: str) -> str:
    prompt = f"""You are an expert research assistant writing a detailed, in-depth academic literature review.

The user's research question is:
"{user_query}"

Below are relevant excerpts from research papers, each labeled with a citation number:

{context_str}

## Instructions:
- Write a thorough literature review that is AT LEAST 800 words long in the body text (excluding the References section).
- Structure the review with the following sections, each containing 2-4 substantive paragraphs:
  ## Introduction — frame the research area, why it matters, and what this review covers
  ## [Theme Section 1] — group related papers by a meaningful topic or sub-field
  ## [Theme Section 2] — another distinct theme with detailed discussion
  ## [Theme Section 3 if warranted] — further theme if papers support it
  ## Discussion — synthesise trends, compare approaches, highlight agreements and contradictions across papers
  ## Conclusion — summarise key takeaways and open problems
  ## References
- For each theme section: describe the problem being solved, the approach/method proposed, key results or benchmarks, and any limitations mentioned.
- Use inline footnote markers like [^1], [^2] every time you reference a specific paper's finding. Multiple citations per sentence are encouraged, e.g. "Recent models show X [^1][^3]."
- Be specific: name models, datasets, metrics, and numbers from the excerpts wherever available.
- Do NOT pad with generic statements. Every sentence must be grounded in the provided excerpts.
- End with a "## References" section listing each cited paper exactly as:
  [^N]: Title. Authors. Year. URL
- Return a JSON object with a single key "summary" whose value is the complete markdown string.
- Do not return anything outside the JSON.

### Response:"""
    return prompt


def needs_more_context_prompt(user_query: str, context_str: str, round_num: int) -> str:
    prompt = f"""You are a research assistant evaluating whether enough context has been gathered for a literature review.

The user's research question is:
"{user_query}"

You are on search round {round_num} of 3. Context gathered so far:

{context_str}

## Instructions:
- Judge honestly: is the current context sufficient to write a comprehensive, well-cited literature review on the user's question?
- Consider: Are there major sub-topics missing? Is recent work underrepresented? Are there too few papers?
- If the context is insufficient, set "needs_more_context" to true and provide ONE specific, focused additional search query (max 5 keywords).
- Optionally specify a year filter (year_min, year_max as integers) if the user's question implies a specific time window (e.g. "in 2025" → year_min: 2025). Use null if no year constraint is needed.
- If the context is sufficient, set "needs_more_context" to false and "additional_query" to null.
- Return ONLY a JSON object with exactly these keys:
  {{
    "needs_more_context": <true|false>,
    "additional_query": "<search query string>" | null,
    "year_min": <integer> | null,
    "year_max": <integer> | null
  }}

### Response:"""
    return prompt
