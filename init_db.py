from app.models.database import Base, engine
from app.models.user import User
from app.models.payment import Payment
from app.models.discount import DiscountCode
from app.models.performance import MonthlyPerformance
from app.models.alert import MarketAlert
from app.models.journal import TradeJournal
from app.models.psychology import EndOfDayCheck, PsychologyAssessment
from app.models.referral import PointTransaction, ReferralReward
from app.models.support import SupportMessage, SupportTicket
from app.models.search_usage import SearchUsage
from app.models.admin_audit import AdminAuditLog
from app.models.economic_event import EconomicEvent
from app.models.market_intelligence import AssetMarketSnapshot

def init():
    Base.metadata.create_all(bind=engine)
    print("Database tables created / updated successfully!")

if __name__ == "__main__":
    init()
