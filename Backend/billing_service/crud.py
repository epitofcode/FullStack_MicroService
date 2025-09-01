from sqlalchemy.orm import Session
import models
from uuid import UUID

def get_user_balance(db: Session, user_id: UUID):
    """
    Retrieves a user's balance. If the user does not have a balance record,
    it creates one with the default starting credits (100).
    """
    db_balance = db.query(models.UserBalance).filter(models.UserBalance.user_id == user_id).first()
    if not db_balance:
        db_balance = models.UserBalance(user_id=user_id)
        db.add(db_balance)
        db.commit()
        db.refresh(db_balance)
    return db_balance

def get_all_policies(db: Session):
    return db.query(models.CreditPolicy).filter(models.CreditPolicy.is_active == True).all()

def create_initial_policies(db: Session):
    """Checks for and creates the default credit policies if they don't exist."""
    policies_to_seed = [
        {
            "model_identifier": "TELUGU_SST_V1",
            "credits_per_unit": 50,
            "unit_description": "per 30 seconds"
        },
        {
            "model_identifier": "TELUGU_TTS_V1",
            "credits_per_unit": 1,
            "unit_description": "per 100 characters"
        },
    ]

    for policy_data in policies_to_seed:
        policy_exists = db.query(models.CreditPolicy).filter_by(model_identifier=policy_data["model_identifier"]).first()
        if not policy_exists:
            db_policy = models.CreditPolicy(**policy_data)
            db.add(db_policy)
            print(f"Creating credit policy for: {policy_data['model_identifier']}")
    
    db.commit()

def deduct_credits(db: Session, user_id: UUID, amount: int):
    """Deducts a specified amount from a user's balance and records the transaction."""
    db_balance = get_user_balance(db, user_id)

    if db_balance.balance < amount:
        return None # Return None to indicate failure (insufficient funds)

    db_balance.balance -= amount
    
    transaction = models.Transaction(
        user_id=user_id,
        amount=-amount, # Store deductions as negative numbers
        description=f"Deduction for 1 job"
    )
    db.add(transaction)
    
    db.commit()
    db.refresh(db_balance)
    return db_balance # Return the updated balance object on success
