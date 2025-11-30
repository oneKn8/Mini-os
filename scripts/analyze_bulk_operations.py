"""
Analyze token usage for bulk/repetitive operations.
"""

def count_tokens_estimate(text: str) -> int:
    """Rough estimate: 1 token ≈ 4 chars."""
    return len(text) // 4


def analyze_bulk_email_scenario():
    """Analyze bulk email sending scenario."""
    print("\n" + "="*60)
    print("BULK EMAIL SCENARIO: Send 50 personalized emails")
    print("="*60 + "\n")

    # Components
    system_prompt = 721
    conversation_history = 100  # Just the request
    tool_schemas = 200  # Only email tools
    user_context = 75

    # Email list (50 recipients with context)
    sample_recipient = """
    {
        "name": "John Doe",
        "email": "john@example.com",
        "company": "Acme Corp",
        "last_interaction": "2024-01-10",
        "context": "Discussed Q4 roadmap, needs follow-up on API integration"
    }
    """
    tokens_per_recipient = count_tokens_estimate(sample_recipient)
    num_recipients = 50
    recipient_list_tokens = tokens_per_recipient * num_recipients

    # Email template
    template = """
    Subject: Follow-up: {topic}

    Hi {name},

    Thanks for our discussion about {context}. I wanted to follow up on...

    [3 paragraph email with personalization]

    Best regards
    """
    template_tokens = count_tokens_estimate(template)

    # Tool results (50 email drafts created)
    sample_result = """
    {
        "id": "draft_123",
        "to": "john@example.com",
        "subject": "Follow-up: API Integration",
        "body": "Hi John, Thanks for our discussion...",
        "status": "drafted",
        "metadata": {...}
    }
    """
    tokens_per_result = count_tokens_estimate(sample_result)
    total_results_tokens = tokens_per_result * num_recipients

    # Calculate total
    baseline = system_prompt + conversation_history + tool_schemas + user_context
    data_tokens = recipient_list_tokens + template_tokens + total_results_tokens

    total = baseline + data_tokens

    print(f"Baseline (system + context):        {baseline:>6} tokens")
    print(f"  System prompt:                    {system_prompt:>6} tokens")
    print(f"  Conversation history:             {conversation_history:>6} tokens")
    print(f"  Tool schemas:                     {tool_schemas:>6} tokens")
    print(f"  User context:                     {user_context:>6} tokens")
    print()
    print(f"Bulk Operation Data:               {data_tokens:>6} tokens")
    print(f"  Recipient list (50 people):      {recipient_list_tokens:>6} tokens")
    print(f"  Email template:                   {template_tokens:>6} tokens")
    print(f"  Tool results (50 drafts):        {total_results_tokens:>6} tokens")
    print()
    print(f"{'TOTAL':40} {total:>6} tokens")
    print()

    # Context window limits
    print("="*60)
    print("CONTEXT WINDOW LIMITS")
    print("="*60 + "\n")

    models = {
        "GPT-4": 8192,
        "GPT-4 Turbo": 128000,
        "Claude 3.5 Sonnet": 200000,
        "Llama 3.1 70B": 128000,
    }

    for model, limit in models.items():
        fits = "✓" if total <= limit else "✗"
        utilization = (total / limit) * 100
        print(f"{model:20} {limit:>7} tokens  {fits}  ({utilization:>5.1f}% used)")

    print()

    # Recommendations
    print("="*60)
    print("PROBLEM & SOLUTION")
    print("="*60 + "\n")

    print(f"❌ NAIVE APPROACH: {total:,} tokens")
    print("   → Exceeds GPT-4 base limit (8K)")
    print("   → Single LLM call with all data")
    print("   → Waits for all 50 operations to finish")
    print()

    print("✅ SMART APPROACH: Streaming + Batching")
    print()

    # Smart approach calculation
    batch_size = 10
    num_batches = num_recipients // batch_size

    tokens_per_batch = (
        baseline +
        (tokens_per_recipient * batch_size) +  # 10 recipients
        template_tokens +
        (tokens_per_result * batch_size)  # 10 results
    )

    print(f"1. Split into {num_batches} batches of {batch_size} emails")
    print(f"   Tokens per batch: {tokens_per_batch:,} tokens")
    print(f"   Total across batches: {tokens_per_batch * num_batches:,} tokens")
    print()

    print("2. Stream results progressively:")
    print("   → Batch 1: Draft 10 emails (emit progress)")
    print("   → Batch 2: Draft 10 emails (emit progress)")
    print("   → ... continue ...")
    print("   → Don't hold all results in context")
    print()

    print("3. Summarize instead of full details:")
    print("   Before: 50 full email drafts in context")
    print("   After: Summary (\"50 emails drafted successfully\")")
    print(f"   Savings: {total_results_tokens:,} → 50 tokens ({total_results_tokens/50:.0f}x reduction)")
    print()

    optimized_total = baseline + recipient_list_tokens + template_tokens + 50
    print(f"✅ OPTIMIZED TOTAL: {optimized_total:,} tokens")
    print(f"   Reduction: {total:,} → {optimized_total:,} ({total/optimized_total:.1f}x)")
    print()

    return {
        "naive": total,
        "optimized": optimized_total,
        "batch_size": batch_size,
        "tokens_per_batch": tokens_per_batch,
    }


def analyze_other_bulk_scenarios():
    """Analyze other repetitive scenarios."""
    print("="*60)
    print("OTHER BULK SCENARIOS")
    print("="*60 + "\n")

    scenarios = {
        "Bulk calendar events (20 meetings)": {
            "description": "Schedule 20 recurring meetings",
            "recipients": 20,
            "tokens_per_item": 150,
            "result_tokens_per_item": 200,
        },
        "Mass inbox processing (100 emails)": {
            "description": "Categorize/prioritize 100 emails",
            "recipients": 100,
            "tokens_per_item": 200,
            "result_tokens_per_item": 100,
        },
        "Batch data export (500 records)": {
            "description": "Export 500 database records",
            "recipients": 500,
            "tokens_per_item": 100,
            "result_tokens_per_item": 150,
        },
    }

    baseline = 721 + 100 + 200 + 75  # ~1100 tokens

    for scenario, config in scenarios.items():
        count = config["recipients"]
        input_tokens = count * config["tokens_per_item"]
        output_tokens = count * config["result_tokens_per_item"]
        naive_total = baseline + input_tokens + output_tokens

        # Optimized: batch + summarize
        batch_size = 10 if count <= 100 else 50
        summarized_output = count  # 1 token per item in summary
        optimized_total = baseline + input_tokens + summarized_output

        print(f"{scenario}")
        print(f"  Items: {count}")
        print(f"  Naive: {naive_total:,} tokens")
        print(f"  Optimized: {optimized_total:,} tokens")
        print(f"  Reduction: {naive_total/optimized_total:.1f}x")
        print()


if __name__ == "__main__":
    results = analyze_bulk_email_scenario()
    analyze_other_bulk_scenarios()

    print("="*60)
    print("KEY TAKEAWAYS")
    print("="*60 + "\n")

    print("1. BULK OPERATIONS NEED DIFFERENT STRATEGY")
    print("   → Can't fit all data + results in context")
    print("   → Must use streaming/batching")
    print()

    print("2. TOKEN BUDGET BY OPERATION TYPE:")
    print("   • Simple query:        1,500-2,000 tokens")
    print("   • Multi-tool query:    3,000-4,500 tokens")
    print("   • Bulk operation:     10,000-50,000+ tokens (batched)")
    print()

    print("3. OPTIMIZATION TECHNIQUES:")
    print("   ✓ Batch processing (10-50 items per batch)")
    print("   ✓ Result streaming (don't accumulate all)")
    print("   ✓ Result summarization (stats, not details)")
    print("   ✓ Progress events (show what's happening)")
    print()

    print("4. WHEN TO USE EACH:")
    print("   • Standard queries: Full context (3-4K tokens)")
    print("   • Bulk operations: Batched + streamed (unlimited)")
    print()
