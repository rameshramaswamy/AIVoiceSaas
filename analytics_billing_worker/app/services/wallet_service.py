import uuid
import logging
from sqlalchemy import text
from app.db.postgres import AsyncSessionLocal

logger = logging.getLogger("wallet")

class WalletService:
    async def deduct_balance(self, tenant_id: str, amount: float, reference_id: str):
        """
        Atomic transaction to deduct funds.
        """
        async with AsyncSessionLocal() as session:
            async with session.begin(): # Start Transaction
                try:
                    # 1. Lock the Tenant Row (Prevents Race Conditions)
                    # We use raw SQL for simplicity in this worker without importing full Models
                    result = await session.execute(
                        text("SELECT credit_balance FROM tenants WHERE id = :id FOR UPDATE"),
                        {"id": tenant_id}
                    )
                    current_balance = result.scalar()
                    
                    if current_balance is None:
                        logger.error(f"Tenant {tenant_id} not found.")
                        return

                    # 2. Update Balance
                    new_balance = float(current_balance) - amount
                    await session.execute(
                        text("UPDATE tenants SET credit_balance = :bal WHERE id = :id"),
                        {"bal": new_balance, "id": tenant_id}
                    )

                    # 3. Log Transaction
                    await session.execute(
                        text("""
                        INSERT INTO transactions (id, tenant_id, amount, reference_id, type, created_at)
                        VALUES (:id, :tid, :amt, :ref, 'usage', NOW())
                        """),
                        {
                            "id": str(uuid.uuid4()),
                            "tid": tenant_id,
                            "amt": -amount, # Negative for deduction
                            "ref": reference_id
                        }
                    )
                    
                    logger.info(f"✅ Deducted ${amount:.4f} from Tenant {tenant_id}. New Balance: ${new_balance:.4f}")
                
                except Exception as e:
                    logger.error(f"Wallet Transaction Failed: {e}")
                    raise # Rollback happens automatically via context manager