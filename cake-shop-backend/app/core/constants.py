# Order statuses
ORDER_STATUSES = [
    "pending", "confirmed", "preparing",
    "ready", "out_for_delivery", "delivered", "cancelled"
]

# Loyalty tiers
LOYALTY_TIERS = {
    "silver":   {"min_points": 0,    "discount": 0,    "free_delivery_above": 500},
    "gold":     {"min_points": 1000, "discount": 0.05, "free_delivery_above": 300},
    "platinum": {"min_points": 5000, "discount": 0.10, "free_delivery_above": 0},
}

# Staff roles
STAFF_ROLES = ["baker", "cashier", "delivery", "manager"]

# Delivery statuses
DELIVERY_STATUSES = ["assigned", "picked_up", "on_the_way", "delivered", "failed"]

# Payment methods
PAYMENT_METHODS = ["upi", "card", "netbanking", "wallet", "cod"]

# Tax rate
GST_RATE = 0.05   # 5% GST on food items
