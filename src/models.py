from pydantic import BaseModel, EmailStr
from pydantic import validator, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import re
import html

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class BotStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"

# --- Request Models ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    
    @validator('email')
    def validate_email(cls, v):
        email_str = str(v).lower().strip()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_str):
            raise ValueError('Invalid email format')
        return email_str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        if len(v) > 128:
            raise ValueError('Password too long')
        # Check for at least one letter and one number
        if not re.search(r'[A-Za-z]', v) or not re.search(r'\d', v):
            raise ValueError('Password must contain at least one letter and one number')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        # Sanitize HTML
        v = html.escape(v.strip())
        if len(v) < 2:
            raise ValueError('Full name must be at least 2 characters')
        if len(v) > 100:
            raise ValueError('Full name too long')
        # Only allow letters, spaces, and common name characters
        if not re.match(r'^[a-zA-ZğüşıöçĞÜŞİÖÇ\s\-\.\']+$', v):
            raise ValueError('Full name contains invalid characters')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    @validator('email')
    def validate_email(cls, v):
        return str(v).lower().strip()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 1:
            raise ValueError('Password is required')
        if len(v) > 128:
            raise ValueError('Password too long')
        return v

class PasswordReset(BaseModel):
    email: str
    
    @validator('email')
    def validate_email(cls, v):
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @validator('token')
    def validate_token(cls, v):
        # Only allow alphanumeric and safe characters
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Invalid token format')
        if len(v) < 10 or len(v) > 200:
            raise ValueError('Invalid token length')
        return v
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        if not re.search(r'[A-Za-z]', v) or not re.search(r'\d', v):
            raise ValueError('Password must contain at least one letter and one number')
        if len(v) > 128:
            raise ValueError('Password too long')
        return v

class APIKeysUpdate(BaseModel):
    api_key: str
    api_secret: str
    is_testnet: bool = False
    
    @validator('api_key', 'api_secret')
    def validate_api_credentials(cls, v):
        # Remove any whitespace
        v = v.strip()
        if len(v) < 10 or len(v) > 200:
            raise ValueError('API credential length must be between 10-200 characters')
        # Only allow alphanumeric and safe characters for API keys
        if not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError('API credentials contain invalid characters')
        return v

class BotControl(BaseModel):
    action: str
    symbol: Optional[str] = None
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['start', 'stop']:
            raise ValueError('Action must be either "start" or "stop"')
        return v
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if v is None:
            return v
        v = v.upper().strip()
        if len(v) < 3 or len(v) > 20:
            raise ValueError('Symbol length must be between 3-20 characters')
        # Only allow valid trading pair format
        if not re.match(r'^[A-Z]{2,10}USDT$', v):
            raise ValueError('Invalid symbol format. Must be like BTCUSDT')
        return v

class BotSettings(BaseModel):
    order_size_usdt: float = 25.0
    leverage: int = 10
    stop_loss_percent: float = 4.0
    take_profit_percent: float = 8.0
    timeframe: str = "15m"
    
    @validator('order_size_usdt')
    def validate_order_size(cls, v):
        if v < 10.0 or v > 1000.0:
            raise ValueError('Order size must be between 10-1000 USDT')
        return v
    
    @validator('leverage')
    def validate_leverage(cls, v):
        if v < 1 or v > 20:
            raise ValueError('Leverage must be between 1-20')
        return v
    
    @validator('stop_loss_percent')
    def validate_stop_loss(cls, v):
        if v < 1.0 or v > 10.0:
            raise ValueError('Stop loss must be between 1-10%')
        return v
    
    @validator('take_profit_percent')
    def validate_take_profit(cls, v):
        if v < 2.0 or v > 20.0:
            raise ValueError('Take profit must be between 2-20%')
        return v
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        if v not in ['1m', '5m', '15m', '1h', '4h']:
            raise ValueError('Timeframe must be one of: 1m, 5m, 15m, 1h, 4h')
        return v

class PaymentNotification(BaseModel):
    user_email: EmailStr
    message: Optional[str] = None
    
    @validator('message')
    def validate_message(cls, v):
        if v is None:
            return v
        # Sanitize HTML and limit length
        v = html.escape(v.strip())
        if len(v) > 500:
            raise ValueError('Message too long')
        return v

# --- Response Models ---
class UserData(BaseModel):
    uid: str
    email: str
    full_name: str
    password_hash: str
    role: UserRole = UserRole.USER
    subscription_status: SubscriptionStatus = SubscriptionStatus.TRIAL
    trial_end_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    is_blocked: bool = False
    api_key_encrypted: Optional[str] = None
    api_secret_encrypted: Optional[str] = None
    is_testnet: bool = False

class TradeData(BaseModel):
    trade_id: str
    user_uid: str
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: float
    price: float
    timestamp: datetime
    profit_loss: Optional[float] = None
    status: str = "OPEN"  # "OPEN", "CLOSED", "CANCELLED"

class PaymentRequest(BaseModel):
    request_id: str
    user_uid: str
    user_email: str
    amount_usdt: float
    status: str = "PENDING"  # "PENDING", "APPROVED", "REJECTED"
    created_at: datetime
    processed_at: Optional[datetime] = None
    admin_notes: Optional[str] = None