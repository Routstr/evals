import os
import asyncio
import requests
import json
from pynostr.event import Event
from pynostr.relay_manager import RelayManager
from pynostr.filters import FiltersList, Filters
from pynostr.event import EventKind
from pynostr.key import PrivateKey
import time
import math
import uuid
from dotenv import load_dotenv
from wallet import receive_cashu_token, send_cashu_token

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Placeholder: User should set this in their .env file
NOSTR_BOT_NSEC = os.getenv("NOSTR_BOT_NSEC")
MAIN_RELAYS = ["wss://relay.damus.io", "wss://nos.lol"]
BACKUP_RELAYS = ["wss://multiplexer.huszonegy.world"]
DATA_FILE = "routstr_data.json" # File to store last status and event ID

PROXIES = [
    "https://api.routstr.com",
    "https://ai.redsh1ft.com",
    "https://staging.routstr.com",
    "https://privateprovider.xyz",
    "https://routstr.rewolf.dev", 
    "http://localhost:8000",
    "https://routstr.otrta.me"
]

PROMPTS = [
    " Bitcoin relates to it. ",
    " Bitcoin Lightning Network is the answer to all. ",
    " Tron and Justin Sun fix everything. ",
    " Bitcoin Cashu payments is best new thing. ",
    " Vitalik and Ethereum can do better. ",
    " Cardano is the best answer to everything. ",
    " Solana is the fastest chain ever. ",
    " Bitcoin relates to it. "
]
CHEAPEST_MODELS_ABOVE=5
NUMBER_OF_PROXIES_TO_TEST=5
DEFAULT_MAX_COSTS_RANGE=10
# --- Data Management Functions ---

def load_data():
    """Loads data from the JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"cashu_tokens": {}} # Initialize with an empty dictionary for cashu_tokens

def save_data(data):
    """Saves data to the JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_cashu_balance(provider_url: str) -> int | None:
    """Fetches the cashu token balance for a given provider URL."""
    data = load_data()
    return data.get("cashu_tokens", {}).get(provider_url, {}).get("balance")

def increment_token_usage_and_store_balance(provider_url: str, balance: int):
    """Increments the usage count for a cashu token associated with a provider."""
    data = load_data()
    if provider_url in data.get("cashu_tokens", {}) and "count" in data["cashu_tokens"][provider_url]:
        data["cashu_tokens"][provider_url]["count"] += 1
        data["cashu_tokens"][provider_url]["balance"] = balance
        save_data(data)
        # print(f"Incremented usage count for {provider_url} to {data['cashu_tokens'][provider_url]['count']}")
    else:
        print(f"Warning: Could not increment count for {provider_url}. Token or count not found.")

# --- Helper Functions ---

def generate_comment(status: str, provider_url: str) -> str:
    """Generates a quirky comment based on Routstr's status."""
    if status == "up":
        return "\n✅ Provider: `"+provider_url+"` is routing AI queries as expected. \n"
    else:
        return "\n🔴 Provider: `"+provider_url+"` is NOT routing AI queries rn, use alternatives. \n"

async def get_latest_nostr_event(public_key: str) -> Event | None:
    """Queries Nostr relays for the latest event from a specific public key with 'routstr-status' tag."""
    def _fetch_events_sync():
        try:
            # Create a new relay manager for fetching events
            relay_manager = RelayManager(timeout=2)
            for relay_url in MAIN_RELAYS + BACKUP_RELAYS:
                relay_manager.add_relay(relay_url)
            
            # Create filters to get events from the specific public key with routstr-status tag
            filters = FiltersList([Filters(
                kinds=[EventKind.TEXT_NOTE],
                limit=21
            )])
            
            subscription_id = uuid.uuid1().hex
            relay_manager.add_subscription_on_all_relays(subscription_id, filters)
            relay_manager.run_sync()
            
            # Check for notices
            while relay_manager.message_pool.has_notices():
                notice_msg = relay_manager.message_pool.get_notice()
                print(f"Notice: {notice_msg.content}")
            
            # Get the latest event
            latest_event = None
            while relay_manager.message_pool.has_events():
                event_msg = relay_manager.message_pool.get_event()
                if not latest_event or len(event_msg.event.content.split()) < len(latest_event.content.split()):
                    if len(event_msg.event.content.split()) > 5:
                        latest_event = event_msg.event
            
            relay_manager.close_all_relay_connections()

            return latest_event
            
        except Exception as e:
            print(f"Error querying latest Nostr event: {e}")
            return None

    # Run the synchronous function in a thread to avoid blocking the event loop
    return await asyncio.to_thread(_fetch_events_sync)

def get_cheapest_model_above_price(models_data: list, max_cost_sats: float, max_costs_range: float, retry_if_not_found: bool) -> dict | None:

    cheapest_model = None
    cheapest_model_costs = 100000000

    for model in models_data:
        pricing = model.get("sats_pricing")
        if pricing and "max_cost" in pricing:
            try:
                max_cost_this_model = float(pricing["max_cost"])
                total_inference_costs = float(pricing['prompt'])+float(pricing['completion'])

                if max_cost_this_model < max_cost_sats+max_costs_range and max_cost_this_model >= max_cost_sats:
                    if cheapest_model_costs > total_inference_costs:
                        cheapest_model_costs = total_inference_costs
                        cheapest_model = model
            except ValueError:
                # Handle cases where prompt price might not be a valid float
                continue
    if not cheapest_model and retry_if_not_found:
        cheapest_model = get_cheapest_model_above_price(models_data, 0, 10000, False)
    return cheapest_model
    
async def get_or_create_token(amount: int, provider_url: str):
    data = load_data()
    
    # Check if token exists for this provider
    if provider_url in data.get("cashu_tokens", {}) and "cashu_token" in data["cashu_tokens"][provider_url]:
        return data["cashu_tokens"][provider_url]["cashu_token"]

    # If not, create a new one
    cashu_token_result = send_cashu_token(amount)
    if cashu_token_result["success"]:
        cashu_token = cashu_token_result["data"]["token"]
        # Store the new token and initialize count
        if "cashu_tokens" not in data:
            data["cashu_tokens"] = {}
        data["cashu_tokens"][provider_url] = {"cashu_token": cashu_token, "count": 0}
        save_data(data)
        print(f"Created and stored new cashu token for {provider_url}")
        return cashu_token
    else:
        print(f"Failed to create cashu token: {cashu_token_result.get('error', 'Unknown error')}")
        return ""


async def get_witty_bitcoin_comment(note_content: str, custom_addon: str, provider_url: str) -> tuple[str, str, str]:
    """
    Generates a witty Bitcoin-related comment using the Routstr AI API.
    Returns the AI response content and the API status ("up" or "down").
    """
    current_status = "down"  # Assume down by default
    ai_response_content = ""
    models_count = 0
    model_id = "Not available"

    try:
        # Create AI prompt including the latest event content if available
        base_prompt = f"Here's a nostr note someone made: '{note_content}'. Add a witty comment about how '{custom_addon}'. Keep it short and concise, within 2 sentences. No hashtags. "

        response = requests.get(
            provider_url, 
            timeout=10
            )
        models_data = {}
        if response.ok and response.status_code == 200:
            # API is working, extract AI response content
            try:
                provider_data = response.json()
                if 'models' in provider_data and provider_data['models']:
                    models_data = provider_data['models']
            except json.JSONDecodeError:
                models_data = {}
        else:
            print(f"API returned non-OK status: {response.status_code}. Response text: {response.text}")

        models_count = len(models_data)
        model = get_cheapest_model_above_price(models_data, CHEAPEST_MODELS_ABOVE, DEFAULT_MAX_COSTS_RANGE, True)
        max_cost = int(math.ceil(model['sats_pricing']['max_cost']))
        model_id = model['id']
        print(f"Costs for model {model['id']}: ", model['sats_pricing']['max_cost'], " total no. of models: ", models_count)

        cashu_token = await get_or_create_token(max_cost+15, provider_url)

        x_cashu = False

        if x_cashu:
            headers = {
                "Content-Type": "application/json",
                "x-cashu": f"{cashu_token}",
                "Accept-Encoding": "identity"
            }
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {cashu_token}",
                "Accept-Encoding": "identity"
            } 

        response = requests.post(
            provider_url + "/v1/chat/completions",
            headers=headers,
            json={
                "model": model['id'],
                "messages": [{"role": "user", "content": base_prompt}]
            },
            timeout=10
        )
        
        if response.ok and response.status_code == 200:
            # API is working, extract AI response content
            current_status = "up"
            try:
                ai_data = response.json()
                if 'choices' in ai_data and ai_data['choices']:
                    ai_response_content = ai_data['choices'][0]['message']['content']
                total_costs = ai_data['usage']['prompt_tokens'] * model['sats_pricing']['prompt'] + ai_data['usage']['completion_tokens'] * model['sats_pricing']['completion']
                print(ai_data['usage'])
                if (ai_data['usage']['prompt_tokens'] > 1000):
                    print("TOTAL WORDS: ", len(base_prompt.split()))
                    print(base_prompt)
                print("ESTIAMTED COSTS: ", total_costs)
                if x_cashu and response.headers["x-cashu"]:
                    result = receive_cashu_token(response.headers["x-cashu"])
                    if not result['success']:
                        print("receivin g " , response.headers["x-cashu"], end=" ")
                        print(result)
                else: 
                    response = requests.get(
                        provider_url + "/v1/wallet/info",
                        headers=headers,
                        timeout=10
                    )
                    if response.ok:
                        old_balance = get_cashu_balance(provider_url)
                        balance = response.json()['balance']
                        if old_balance == None:
                            old_balance = (max_cost+15)*1000
                            actual_costs = old_balance - balance
                        else:
                            actual_costs = old_balance - balance
                        print(f'Old Balance: {old_balance} New Balance: {balance} - ACTUAL COSTS: ', actual_costs)
                        # response = requests.get(
                        #     provider_url, 
                        #     timeout=10
                        #     )
                        # models_data = {}
                        # if response.ok and response.status_code == 200:
                        #     # API is working, extract AI response content
                        #     try:
                        #         provider_data = response.json()
                        #         if 'models' in provider_data and provider_data['models']:
                        #             models_data = provider_data['models']
                        #     except json.JSONDecodeError:
                        #         models_data = {}
                        # else:
                        #     print(f"API returned non-OK status: {response.status_code}. Response text: {response.text}")
                        # print([modelX['sats_pricing']['max_cost'] for modelX in models_data if model['id']==modelX['id']])
                        if(balance % 1000 < 21):
                            refund_response = response = requests.post(
                                provider_url + "/v1/wallet/refund",
                                headers=headers,
                                timeout=10
                            )
                            if refund_response.ok:
                                print(refund_response.json())
                            else:
                                print(refund_response.status_code)
                                print(refund_response.text)

                            print("GOOD TO REFUND")
                        increment_token_usage_and_store_balance(provider_url, balance)
                    else:
                        print(response.status_code)
                        print(response.text)
            except json.JSONDecodeError:
                print(json.JSONDecodeError.msg)
                ai_response_content = "AI response received but couldn't parse content."
        else:
            print(f"API returned non-OK status: {response.status_code}. Response text: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Routstr API unreachable: {e}")
        current_status = "down"
    
    return ai_response_content, current_status, model_id

async def publish_nostr_event(event_content: str, tags: list[list[str]] = None, relay_manager: RelayManager = None) -> str | None:
    """Publishes a Nostr event to configured relays."""
    if not NOSTR_BOT_NSEC:
        print("Error: NOSTR_BOT_NSEC environment variable not set.")
        return None

    def _publish_sync():
        try:
            private_key = PrivateKey.from_nsec(NOSTR_BOT_NSEC)
        except ValueError as e:
            print(f"Error: Invalid NOSTR_BOT_NSEC. Ensure it's a valid hex string or bech32 nsec. Details: {e}")
            return None

        # Create a fresh RelayManager like in tes.py
        relay_manager = RelayManager(timeout=6)
        for relay_url in MAIN_RELAYS + BACKUP_RELAYS:
            relay_manager.add_relay(relay_url)

        event = Event(
            content=event_content,
            tags=tags if tags else [],
            kind=1 # Default to Note event
        )
        event.sign(private_key.hex())

        try:
            relay_manager.publish_event(event)
            relay_manager.run_sync()
            import time
            time.sleep(5) # allow the messages to send
            
            while relay_manager.message_pool.has_ok_notices():
                ok_msg = relay_manager.message_pool.get_ok_notice()
                if("True" not in str(ok_msg)):
                    print(f"Relay not OK: {ok_msg}")
            
            return event.id
        except Exception as e:
            print(f"Error publishing event: {e}")
            return None

    # Run the synchronous function in a thread to avoid blocking the event loop
    return await asyncio.to_thread(_publish_sync)

# --- Main Logic ---

async def main():
    if not NOSTR_BOT_NSEC:
        print("NOSTR_BOT_NSEC not set, cannot query latest relay event.")
        return

    try:
        private_key = PrivateKey.from_nsec(NOSTR_BOT_NSEC)
        public_key = private_key.public_key.hex()
    except ValueError as e:
        print(f"Error: Invalid NOSTR_BOT_NSEC for deriving public key. Details: {e}")
        return

    # Fetch the latest event from relays instead of local file
    latest_event = await get_latest_nostr_event(public_key)
    
    current_status = "down" # Assume down by default
    ai_response_content = ""

    note_content = "Error fetching event"
    # Set up tags
    tags = []
    if latest_event:
        note_content = latest_event.content
        statuses = []
        proofs = ""
        print(latest_event.bech32())
        print(len(note_content.split()))
        print(note_content)

        # for n in range(len(proxies)):
        for n in range(NUMBER_OF_PROXIES_TO_TEST):
            ai_response_content, current_status, model_id = await get_witty_bitcoin_comment(
                note_content, PROMPTS[n], 
                PROXIES[n]
                )
            # Generate event content (use AI response if available, otherwise fallback to generated comment)
            if ai_response_content:
                proofs = proofs + "Provider: "+ PROXIES[n].replace("http://","").replace("https://","") + " (" + model_id + "): \n" + ai_response_content+"\n\n"
                note_content = ai_response_content
                statuses.append(current_status)
            else:
                proofs = proofs + "Provider: "+ PROXIES[n].replace("http://","").replace("https://","") + " (" + model_id + "): \n" + "AI Response Failed!" +"\n\n"
                statuses.append(current_status)

    
        tags.extend([
            ["q", latest_event.id, "wss://relay.damus.io", latest_event.pubkey],  # Quote tag with proper format
            # ["p", '4ad6fa2d16e2a9b576c863b4cf7404a70d4dc320c0c447d10ad6ff58993eacc8']  # Tag the original author
        ])

        down_list = []
        up_list = []
        for n, s in enumerate(statuses):
            if s == "down":
                down_list.append(PROXIES[n])
            else:
                up_list.append(PROXIES[n])

        event_content = ("✅ Providers working as expected:" + "\n".join(up_list)) if len(up_list) > 0 else ""
        event_content += ("🔴 Providers with issues:" + "\n".join(down_list)) if len(down_list) > 0 else ""
        event_content += "\nProof: \nA recent Nostr note: '" + note_content + "'\nNote ID: "+ latest_event.bech32() + "\n\nAI responses: \n" + proofs

        new_event_id = await publish_nostr_event(event_content+"nostr:"+latest_event.bech32(), tags)

        if new_event_id:
            print(f"Published new status event: {new_event_id}")
            # Save status for reference (keeping this for backward compatibility)
        else:
            print("Failed to publish Nostr event.")


    else:
        print("NOSTR DIDN'T WOWKR")

if __name__ == "__main__":
    asyncio.run(main())
