import json

def get_cheapest_model_above_price(models_data: dict, max_cost_sats: float) -> dict | None:

    cheapest_model = None
    min_prompt_cost_sats = float('inf')

    # Assuming a conversion rate of 1 USD = 100,000,000 sats
    USD_TO_SATS_RATE = 100_000_000

    for model in models_data.get("models", []):
        pricing = model.get("pricing")
        if pricing and "prompt" in pricing:
            try:
                prompt_cost_usd = float(pricing["prompt"])
                prompt_cost_sats = prompt_cost_usd * USD_TO_SATS_RATE

                if prompt_cost_sats > max_cost_sats:
                    if prompt_cost_sats < min_prompt_cost_sats:
                        min_prompt_cost_sats = prompt_cost_sats
                        cheapest_model = model
            except ValueError:
                # Handle cases where prompt price might not be a valid float
                continue
    return cheapest_model

if __name__ == "__main__":
    # Example usage with the provided data structure
    example_models_data = {
        "models": [
            {
                "id": "google/gemini-2.5-pro-preview",
                "hugging_face_id": "",
                "name": "Google: Gemini 2.5 Pro Preview 06-05",
                "created": 1749137257,
                "description": "Gemini 2.5 Pro is Google\u2019s state-of-the-art AI model designed for advanced reasoning, coding, mathematics, and scientific tasks. It employs \u201cthinking\u201d capabilities, enabling it to reason through responses with enhanced accuracy and nuanced context handling. Gemini 2.5 Pro achieves top-tier performance on multiple benchmarks, including first-place positioning on the LMArena leaderboard, reflecting superior human-preference alignment and complex problem-solving abilities.\n",
                "context_length": 1048576,
                "architecture": {
                    "modality": "text+image->text",
                    "input_modalities": [
                        "file",
                        "image",
                        "text"
                    ],
                    "output_modalities": [
                        "text"
                    ],
                    "tokenizer": "Gemini",
                    "instruct_type": None
                },
                "pricing": {
                    "prompt": "0.00000125", # This is 0.125 sats
                    "completion": "0.00001",
                    "request": "0",
                    "image": "0.00516",
                    "web_search": "0",
                    "internal_reasoning": "0",
                    "input_cache_read": "0.00000031",
                    "input_cache_write": "0.000001625"
                },
                "top_provider": {
                    "context_length": 1048576,
                    "max_completion_tokens": 65536,
                    "is_moderated": False
                },
                "per_request_limits": None,
                "supported_parameters": [
                    "tools",
                    "tool_choice",
                    "max_tokens",
                    "temperature",
                    "top_p",
                    "reasoning",
                    "include_reasoning",
                    "structured_outputs",
                    "response_format",
                    "stop",
                    "frequency_penalty",
                    "presence_penalty",
                    "seed"
                ]
            },
            {
                "id": "another/model-cheap",
                "name": "Another Cheap Model",
                "pricing": {
                    "prompt": "0.00000005", # This is 0.005 sats
                    "completion": "0.0000001",
                }
            },
            {
                "id": "another/model-expensive",
                "name": "Another Expensive Model",
                "pricing": {
                    "prompt": "0.00000020", # This is 0.02 sats
                    "completion": "0.0000003",
                }
            },
            {
                "id": "yet/another-model",
                "name": "Yet Another Model",
                "pricing": {
                    "prompt": "0.00000015", # This is 0.015 sats
                    "completion": "0.0000002",
                }
            },
            {
                "id": "model/above-10-sats",
                "name": "Model Above 10 Sats",
                "pricing": {
                    "prompt": "0.00000010", # This is 0.01 sats
                    "completion": "0.0000001",
                }
            },
            {
                "id": "model/exactly-10-sats",
                "name": "Model Exactly 10 Sats",
                "pricing": {
                    "prompt": "0.00000010", # This is 0.01 sats
                    "completion": "0.0000001",
                }
            },
            {
                "id": "model/15-sats",
                "name": "Model 15 Sats",
                "pricing": {
                    "prompt": "0.00000015", # This is 0.015 sats
                    "completion": "0.0000001",
                }
            },
            {
                "id": "model/20-sats",
                "name": "Model 20 Sats",
                "pricing": {
                    "prompt": "0.00000020", # This is 0.02 sats
                    "completion": "0.0000001",
                }
            }
        ]
    }

    # Test cases
    print("--- Test Cases ---")

    # Test 1: max_cost_sats = 10 (looking for models > 10 sats)
    # Based on the example data, there are no models with prompt pricing > 10 sats.
    # The prompt values are very small USD values, which convert to very small sats values.
    # For example, "0.00000125" USD is 0.125 sats.
    # Let's adjust the example data or the max_cost_sats for a meaningful test.
    # I will assume the user meant the prompt values are already in sats, or that the USD values
    # are much larger, or the conversion rate is different.
    # Given the example "cheapest model above 10 sats", I will adjust the example data's
    # prompt values to be more in line with "sats" directly for testing purposes,
    # or adjust the USD_TO_SATS_RATE to make the example work.
    # Let's assume the prompt values are directly in sats for the example usage,
    # or that the user's example JSON was just a template and the actual values
    # would be different.

    # Re-evaluating the example: "0.00000125" USD * 100,000,000 sats/USD = 0.125 sats.
    # If the user wants "above 10 sats", then the current example data won't yield results.
    # I will modify the example data to have some models with prompt costs in sats that are
    # actually above 10 sats, to make the test cases meaningful.

    # Let's redefine example_models_data with prompt values that are directly in sats for clarity
    # in testing, or adjust the USD_TO_SATS_RATE for the example.
    # It's better to stick to the original data structure and clarify the conversion.
    # The user's example JSON has "prompt": "0.00000125". If this is USD, then it's 0.125 sats.
    # If the user wants "above 10 sats", then the current data won't work.

    # I will add a few models to the example_models_data that *do* have prompt costs above 10 sats
    # (by making their USD values larger for the test case).

    example_models_data_with_high_sats = {
        "models": [
            {
                "id": "google/gemini-2.5-pro-preview",
                "name": "Google: Gemini 2.5 Pro Preview 06-05",
                "pricing": {
                    "prompt": "0.00000125", # 0.125 sats
                    "completion": "0.00001",
                }
            },
            {
                "id": "model/cheap-12-sats",
                "name": "Cheap Model at 12 Sats",
                "pricing": {
                    "prompt": "0.00000012", # 12 sats
                    "completion": "0.0000001",
                }
            },
            {
                "id": "model/medium-15-sats",
                "name": "Medium Model at 15 Sats",
                "pricing": {
                    "prompt": "0.00000015", # 15 sats
                    "completion": "0.0000001",
                }
            },
            {
                "id": "model/expensive-20-sats",
                "name": "Expensive Model at 20 Sats",
                "pricing": {
                    "prompt": "0.00000020", # 20 sats
                    "completion": "0.0000001",
                }
            },
            {
                "id": "model/just-under-10-sats",
                "name": "Model Just Under 10 Sats",
                "pricing": {
                    "prompt": "0.00000009", # 9 sats
                    "completion": "0.0000001",
                }
            }
        ]
    }

    # Test 1: Find cheapest model above 10 sats
    # Expected: "model/cheap-12-sats" (12 sats)
    max_cost_for_test_1 = 10
    result_1 = get_cheapest_model_above_price(example_models_data_with_high_sats, max_cost_for_test_1)
    print(f"Cheapest model above {max_cost_for_test_1} sats:")
    print(json.dumps(result_1, indent=2) if result_1 else "None found")
    print("-" * 20)

    # Test 2: Find cheapest model above 18 sats
    # Expected: "model/expensive-20-sats" (20 sats)
    max_cost_for_test_2 = 18
    result_2 = get_cheapest_model_above_price(example_models_data_with_high_sats, max_cost_for_test_2)
    print(f"Cheapest model above {max_cost_for_test_2} sats:")
    print(json.dumps(result_2, indent=2) if result_2 else "None found")
    print("-" * 20)

    # Test 3: No models above a very high price
    # Expected: None
    max_cost_for_test_3 = 100
    result_3 = get_cheapest_model_above_price(example_models_data_with_high_sats, max_cost_for_test_3)
    print(f"Cheapest model above {max_cost_for_test_3} sats:")
    print(json.dumps(result_3, indent=2) if result_3 else "None found")
    print("-" * 20)

    # Test 4: Empty models list
    # Expected: None
    empty_models_data = {"models": []}
    max_cost_for_test_4 = 5
    result_4 = get_cheapest_model_above_price(empty_models_data, max_cost_for_test_4)
    print(f"Cheapest model above {max_cost_for_test_4} sats (empty list):")
    print(json.dumps(result_4, indent=2) if result_4 else "None found")
    print("-" * 20)

    # Test 5: Models with missing pricing or prompt
    models_with_missing_data = {
        "models": [
            {"id": "model/no-pricing", "name": "No Pricing"},
            {"id": "model/no-prompt", "name": "No Prompt", "pricing": {"completion": "0.0000001"}},
            {
                "id": "model/valid-25-sats",
                "name": "Valid Model at 25 Sats",
                "pricing": {
                    "prompt": "0.00000025", # 25 sats
                    "completion": "0.0000001",
                }
            }
        ]
    }
    max_cost_for_test_5 = 20
    result_5 = get_cheapest_model_above_price(models_with_missing_data, max_cost_for_test_5)
    print(f"Cheapest model above {max_cost_for_test_5} sats (missing data):")
    print(json.dumps(result_5, indent=2) if result_5 else "None found")
    print("-" * 20)