import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime


class CashuWalletClient:
    """
    Python client for interacting with Cashu token REST API endpoints.
    Provides functions to send, receive, and check balance of Cashu tokens.
    """
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        """
        Initialize the Cashu wallet client.
        
        Args:
            base_url: Base URL of the Cashu API server (default: http://localhost:3000)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            data: Request payload for POST requests
            
        Returns:
            Dict containing the API response
            
        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.base_url}/api{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    return {
                        'success': False,
                        'message': error_data.get('message', str(e)),
                        'timestamp': datetime.now().isoformat()
                    }
                except:
                    pass
            return {
                'success': False,
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def send_token(self, amount: int, mint_url: Optional[str] = None, unit: str = 'sat') -> Dict[str, Any]:
        """
        Generate a send token for a specified amount.
        
        Args:
            amount: Amount to send (must be positive integer)
            mint_url: Optional mint URL (uses default if not provided)
            unit: Token unit (default: 'sat')
            
        Returns:
            Dict containing:
                - success: bool
                - message: str
                - data: dict with token, amount, mintUrl, remainingBalance (if successful)
                - timestamp: str
        """
        if not isinstance(amount, int) or amount <= 0:
            return {
                'success': False,
                'message': 'Amount must be a positive integer',
                'timestamp': datetime.now().isoformat()
            }
        
        payload = {
            'amount': amount,
            'unit': unit
        }
        
        if mint_url:
            payload['mintUrl'] = mint_url
        
        return self._make_request('POST', '/send', payload)
    
    def receive_token(self, token: str, mint_url: Optional[str] = None, unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Import a Cashu token and add proofs to storage.
        
        Args:
            token: Cashu token string to import
            mint_url: Optional mint URL (uses default if not provided)
            unit: Optional token unit
            
        Returns:
            Dict containing:
                - success: bool
                - message: str
                - data: dict with importedAmount, balanceBefore, balanceAfter, mintUrl (if successful)
                - timestamp: str
        """
        if not token or not isinstance(token, str) or not token.strip():
            return {
                'success': False,
                'message': 'Valid token string is required',
                'timestamp': datetime.now().isoformat()
            }
        
        payload = {
            'token': token.strip()
        }
        
        if mint_url:
            payload['mintUrl'] = mint_url
        if unit:
            payload['unit'] = unit
        
        return self._make_request('POST', '/receive', payload)
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Get current balance from stored proofs.
        
        Returns:
            Dict containing:
                - success: bool
                - message: str
                - data: dict with balance, proofCount, unit (if successful)
                - timestamp: str
        """
        return self._make_request('GET', '/balance')


# Convenience functions for direct usage
def create_wallet_client(base_url: str = "http://localhost:3000") -> CashuWalletClient:
    """Create a new CashuWalletClient instance."""
    return CashuWalletClient(base_url)


def send_cashu_token(amount: int, mint_url: Optional[str] = None, unit: str = 'sat', 
                    base_url: str = "http://localhost:3000") -> Dict[str, Any]:
    """
    Convenience function to send a Cashu token.
    
    Args:
        amount: Amount to send
        mint_url: Optional mint URL
        unit: Token unit (default: 'sat')
        base_url: API base URL
        
    Returns:
        API response dict
    """
    client = CashuWalletClient(base_url)
    return client.send_token(amount, mint_url, unit)


def receive_cashu_token(token: str, mint_url: Optional[str] = None, unit: Optional[str] = None,
                       base_url: str = "http://localhost:3000") -> Dict[str, Any]:
    """
    Convenience function to receive a Cashu token.
    
    Args:
        token: Cashu token string
        mint_url: Optional mint URL
        unit: Optional token unit
        base_url: API base URL
        
    Returns:
        API response dict
    """
    client = CashuWalletClient(base_url)
    return client.receive_token(token, mint_url, unit)


def get_wallet_balance(base_url: str = "http://localhost:3000") -> Dict[str, Any]:
    """
    Convenience function to get wallet balance.
    
    Args:
        base_url: API base URL
        
    Returns:
        API response dict
    """
    client = CashuWalletClient(base_url)
    return client.get_balance()


# Example usage
if __name__ == "__main__":
    # Example of how to use the wallet client
    
    # Create a client instance
    wallet = CashuWalletClient("http://localhost:3000")
    
    # Check current balance
    balance_result = wallet.get_balance()
    print("Current balance:", balance_result)
    
    # Send tokens (example)
    # send_result = wallet.send_token(100)
    # print("Send result:", send_result)
    
    # Receive tokens (example)
    # receive_result = wallet.receive_token("cashuAeyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9...")
    # print("Receive result:", receive_result)
    
    # Using convenience functions
    # balance = get_wallet_balance()
    # send_result = send_cashu_token(50)
    # receive_result = receive_cashu_token("token_string_here")