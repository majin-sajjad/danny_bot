"""
Points Calculation System
"""

import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class PointsCalculator:
    """Calculates points based on deal type and niche"""
    
    # Points configuration for different niches and deal types
    POINTS_CONFIG = {
        'solar': {
            'standard': 1,
            'self_generated': 2,
            'set': 1,
            'close': 1,
            'self': 2
        },
        'fiber': {
            'standard': 0.2,  # 5 deals = 1 point
            'self_generated': 2,
            'set': 1,
            'close': 1, 
            'self': 2
        },
        'landscaping': {
            'standard': 1,
            'self_generated': 2,
            'set': 1,
            'close': 1,
            'self': 2,
            'bonus_threshold': 50000,  # $50k threshold for bonus points
            'bonus_per_50k': 1  # 1 point per $50k above threshold
        }
    }
    
    def calculate_points(self, deal_type: str, niche: str, deal_amount: float = 0) -> int:
        """Calculate points for a deal"""
        try:
            niche = niche.lower()
            deal_type = deal_type.lower()
            
            # Get niche configuration, default to solar if not found
            niche_config = self.POINTS_CONFIG.get(niche, self.POINTS_CONFIG['solar'])
            
            # Get base points for deal type
            base_points = niche_config.get(deal_type, 1)
            
            # Handle special cases
            if niche == 'fiber' and deal_type == 'standard':
                # Fiber: 5 deals = 1 point, so 0.2 points per deal
                base_points = 0.2
            
            # Calculate bonus points for landscaping
            bonus_points = 0
            if niche == 'landscaping' and deal_amount > 0:
                threshold = niche_config.get('bonus_threshold', 50000)
                bonus_per_50k = niche_config.get('bonus_per_50k', 1)
                
                if deal_amount > threshold:
                    excess_amount = deal_amount - threshold
                    bonus_points = int(excess_amount // 50000) * bonus_per_50k
            
            total_points = base_points + bonus_points
            
            # Round to nearest integer for fiber deals
            if niche == 'fiber':
                total_points = round(total_points)
            
            return max(1, int(total_points))  # Minimum 1 point per deal
            
        except Exception as e:
            logger.error(f"Error calculating points for {deal_type} {niche} deal: {e}")
            return 1  # Default to 1 point
    
    def get_deal_type_display(self, deal_type: str, niche: str) -> str:
        """Get display name for deal type"""
        deal_type = deal_type.lower()
        
        display_names = {
            'standard': 'Standard Deal',
            'self_generated': 'Self-Generated',
            'self': 'Self-Generated',
            'set': 'Appointment Set',
            'close': 'Close',
            'single': 'Single Deal',
            'multiple': 'Multiple Deals'
        }
        
        return display_names.get(deal_type, deal_type.title())
    
    def categorize_deal_type(self, niche: str, deal_type: str) -> str:
        """Categorize deal type for statistics"""
        deal_type = deal_type.lower()
        
        setter_types = ['set', 'single', 'multiple']
        closer_types = ['close']
        self_gen_types = ['self_generated', 'self']
        
        if deal_type in setter_types:
            return 'setter'
        elif deal_type in closer_types:
            return 'closer'
        elif deal_type in self_gen_types:
            return 'self_gen'
        else:
            # Default categorization
            if deal_type == 'standard':
                return 'closer'
            else:
                return 'self_gen'
    
    def get_niche_info(self, niche: str) -> Dict:
        """Get information about a niche's point system"""
        niche = niche.lower()
        niche_config = self.POINTS_CONFIG.get(niche, self.POINTS_CONFIG['solar'])
        
        info = {
            'niche': niche.title(),
            'emoji': self._get_niche_emoji(niche),
            'point_system': self._get_point_system_description(niche, niche_config)
        }
        
        return info
    
    def _get_niche_emoji(self, niche: str) -> str:
        """Get emoji for niche"""
        emojis = {
            'solar': '☀️',
            'fiber': '🌐',
            'landscaping': '🌿'
        }
        return emojis.get(niche.lower(), '💼')
    
    def _get_point_system_description(self, niche: str, config: Dict) -> str:
        """Get description of point system for niche"""
        if niche == 'solar':
            return "1 point standard deal, 2 points self-generated"
        elif niche == 'fiber':
            return "5 deals = 1 point, 1 pt set that closes, 1 pt close, 2 pts self-gen"
        elif niche == 'landscaping':
            return "1 pt set, 1 pt close, 1 pt per $50k above $50k"
        else:
            return "1 point per standard deal, 2 points self-generated"
    
    def validate_deal_amount(self, deal_amount_str: str) -> Tuple[bool, float]:
        """Validate and parse deal amount"""
        try:
            if not deal_amount_str:
                return True, 0
            
            # Remove common currency symbols and formatting
            clean_amount = deal_amount_str.replace('$', '').replace(',', '').strip()
            
            amount = float(clean_amount)
            
            if amount < 0:
                return False, 0
            
            return True, amount
            
        except ValueError:
            return False, 0 