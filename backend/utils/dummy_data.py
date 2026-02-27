"""
Dummy data generator for Hisaab system
Generates realistic, temporally consistent data for demo purposes
"""

from faker import Faker
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
from models.transaction import Transaction, TransactionType, TransactionItem, PersonInfo, PaymentMode
from models.stock import StockItem, SupplierInfo, ConsumptionPattern, VelocityType
from models.customer import CustomerProfile, CustomerType, VisitFrequency, CreditBehavior, PurchasePattern

fake = Faker(['en_IN', 'ta_IN'])

# Tamil shop items
SHOP_ITEMS = [
    {"name": "samosa", "tamil": "சமோசா", "category": "snacks", "cost": 6, "price": 10, "shelf_life": 12},
    {"name": "chai", "tamil": "சாய்", "category": "beverages", "cost": 3, "price": 5, "shelf_life": 2},
    {"name": "biscuits", "tamil": "பிஸ்கட்", "category": "packaged", "cost": 15, "price": 20, "shelf_life": 720},
    {"name": "bread", "tamil": "ரொட்டி", "category": "bakery", "cost": 25, "price": 35, "shelf_life": 48},
    {"name": "milk", "tamil": "பால்", "category": "dairy", "cost": 45, "price": 55, "shelf_life": 24},
    {"name": "eggs", "tamil": "முட்டை", "category": "dairy", "cost": 5, "price": 7, "shelf_life": 168},
    {"name": "cold drink", "tamil": "குளிர்பானம்", "category": "beverages", "cost": 15, "price": 20, "shelf_life": 2160},
    {"name": "chips", "tamil": "சிப்ஸ்", "category": "snacks", "cost": 8, "price": 10, "shelf_life": 720},
    {"name": "rice", "tamil": "அரிசி", "category": "groceries", "cost": 40, "price": 50, "shelf_life": 2160},
    {"name": "oil", "tamil": "எண்ணெய்", "category": "groceries", "cost": 150, "price": 180, "shelf_life": 2160},
]

TAMIL_NAMES = [
    "Ramesh", "Kumar", "Lakshmi", "Priya", "Murugan", "Selvi", "Ravi", "Meena",
    "Ganesh", "Devi", "Suresh", "Kamala", "Vijay", "Radha", "Anand", "Saroja"
]

async def generate_stock_items(user_id: str, shop_id: str) -> List[StockItem]:
    """Generate initial stock items"""
    items = []
    
    for item_data in SHOP_ITEMS:
        stock_item = StockItem(
            name=item_data["name"],
            aliases=[item_data["tamil"], item_data["name"]],
            category=item_data["category"],
            current_stock=random.randint(50, 200),
            unit="piece" if item_data["category"] in ["snacks", "bakery"] else "unit",
            reorder_point=random.randint(20, 50),
            reorder_quantity=random.randint(100, 200),
            cost_price=item_data["cost"],
            selling_price=item_data["price"],
            margin_percent=((item_data["price"] - item_data["cost"]) / item_data["price"]) * 100,
            shelf_life_hours=item_data["shelf_life"],
            user_id=user_id,
            shop_id=shop_id
        )
        
        # Set consumption pattern
        stock_item.consumption_pattern.avg_daily = random.randint(20, 100)
        stock_item.consumption_pattern.peak_days = random.sample(
            ["saturday", "sunday", "friday"], k=random.randint(1, 2)
        )
        stock_item.consumption_pattern.peak_hours = ["17:00-20:00"]
        
        # Set velocity
        if stock_item.consumption_pattern.avg_daily > 60:
            stock_item.velocity = VelocityType.FAST
        elif stock_item.consumption_pattern.avg_daily > 30:
            stock_item.velocity = VelocityType.MEDIUM
        else:
            stock_item.velocity = VelocityType.SLOW
        
        # Add supplier info
        stock_item.supplier = SupplierInfo(
            name=f"{random.choice(['Kumar', 'Lakshmi', 'Ravi'])} {item_data['category'].title()} Suppliers",
            phone=fake.phone_number(),
            lead_time_hours=random.randint(2, 8),
            min_order=random.randint(50, 100),
            last_price=item_data["cost"]
        )
        
        items.append(stock_item)
    
    # Save all items
    for item in items:
        await item.save()
    
    return items

async def generate_customer_profiles(user_id: str, shop_id: str, count: int = 10) -> List[CustomerProfile]:
    """Generate customer profiles"""
    customers = []
    
    for _ in range(count):
        name = random.choice(TAMIL_NAMES)
        
        customer = CustomerProfile(
            name=name,
            phone=fake.phone_number() if random.random() > 0.3 else None,
            type=random.choice([CustomerType.REGULAR, CustomerType.OCCASIONAL, CustomerType.ONE_TIME]),
            first_seen=datetime.now() - timedelta(days=random.randint(30, 365)),
            last_seen=datetime.now() - timedelta(days=random.randint(0, 7)),
            visit_frequency=random.choice([VisitFrequency.DAILY, VisitFrequency.WEEKLY]),
            total_transactions=random.randint(10, 200),
            lifetime_value=random.randint(1000, 20000),
            user_id=user_id,
            shop_id=shop_id
        )
        
        # Credit behavior
        if random.random() > 0.5:  # 50% customers take credit
            outstanding = random.randint(0, 1000)
            customer.credit_behavior.total_credit_given = random.randint(1000, 5000)
            customer.credit_behavior.total_repaid = customer.credit_behavior.total_credit_given - outstanding
            customer.credit_behavior.outstanding = outstanding
            customer.credit_behavior.avg_repayment_days = random.randint(5, 30)
            customer.credit_behavior.risk_score = min(100, customer.credit_behavior.avg_repayment_days * 3)
            
            # Aging
            if outstanding > 0:
                customer.credit_behavior.aging.days_0_7 = random.randint(0, outstanding // 2)
                customer.credit_behavior.aging.days_8_14 = random.randint(0, outstanding // 3)
                customer.credit_behavior.aging.days_15_30 = outstanding - customer.credit_behavior.aging.days_0_7 - customer.credit_behavior.aging.days_8_14
        
        # Purchase pattern
        customer.purchase_pattern.favorite_items = random.sample(
            [item["name"] for item in SHOP_ITEMS], k=random.randint(2, 5)
        )
        customer.purchase_pattern.avg_basket_size = random.randint(30, 150)
        customer.purchase_pattern.preferred_time = random.choice(["morning", "afternoon", "evening"])
        
        # Tags
        if customer.type == CustomerType.REGULAR:
            customer.behavioral_tags.append("loyal")
        if customer.credit_behavior.risk_score < 50:
            customer.behavioral_tags.append("credit_worthy")
        
        customers.append(customer)
    
    # Save all customers
    for customer in customers:
        await customer.save()
    
    return customers

async def generate_transactions(
    user_id: str,
    shop_id: str,
    stock_items: List[StockItem],
    customers: List[CustomerProfile],
    days: int = 30,
    per_day: int = 20
) -> List[Transaction]:
    """Generate realistic transactions over time"""
    transactions = []
    
    for day in range(days):
        date = datetime.now() - timedelta(days=days - day)
        
        # More transactions on weekends
        daily_count = per_day
        if date.weekday() in [5, 6]:  # Saturday, Sunday
            daily_count = int(per_day * 1.4)
        
        for _ in range(daily_count):
            # Random time during business hours (6 AM - 10 PM)
            hour = random.randint(6, 22)
            minute = random.randint(0, 59)
            timestamp = date.replace(hour=hour, minute=minute)
            
            # Select random item
            item_data = random.choice(SHOP_ITEMS)
            quantity = random.randint(1, 20)
            
            # Transaction type (90% sales, 5% purchase, 5% other)
            rand = random.random()
            if rand < 0.90:
                trans_type = TransactionType.SALE
            elif rand < 0.95:
                trans_type = TransactionType.PURCHASE
            else:
                trans_type = random.choice([TransactionType.EXPENSE, TransactionType.FREEBIE, TransactionType.LOSS])
            
            # Payment mode
            if trans_type == TransactionType.SALE:
                payment_mode = random.choices(
                    [PaymentMode.CASH, PaymentMode.UPI, PaymentMode.CREDIT],
                    weights=[0.6, 0.3, 0.1]
                )[0]
            else:
                payment_mode = PaymentMode.CASH
            
            # Person (for credit transactions or regular customers)
            person = None
            if payment_mode == PaymentMode.CREDIT or random.random() > 0.7:
                customer = random.choice(customers)
                person = PersonInfo(
                    name=customer.name,
                    phone=customer.phone,
                    profile_id=customer.profile_id
                )
            
            transaction = Transaction(
                timestamp=timestamp,
                type=trans_type,
                items=[
                    TransactionItem(
                        item_name=item_data["name"],
                        normalized_name=item_data["name"].lower(),
                        quantity=quantity,
                        unit="piece",
                        unit_price=item_data["price"] if trans_type == TransactionType.SALE else item_data["cost"],
                        total=quantity * (item_data["price"] if trans_type == TransactionType.SALE else item_data["cost"]),
                        cost_price=item_data["cost"],
                        margin=item_data["price"] - item_data["cost"]
                    )
                ],
                total_amount=quantity * (item_data["price"] if trans_type == TransactionType.SALE else item_data["cost"]),
                payment_mode=payment_mode,
                person=person,
                confidence_score=100,
                source="dummy",
                original_input=f"Generated dummy transaction",
                language="tamil",
                user_id=user_id,
                shop_id=shop_id
            )
            
            transactions.append(transaction)
    
    # Save all transactions
    for transaction in transactions:
        await transaction.save()
    
    return transactions

